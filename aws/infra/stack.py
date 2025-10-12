from __future__ import annotations

import os
from typing import Optional

from constructs import Construct
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    Environment,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events,
    aws_sqs as sqs,
    aws_secretsmanager as secretsmanager,
)

# Alpha modules
from aws_cdk import (
    aws_apigatewayv2_alpha as apigwv2,
    aws_apigatewayv2_integrations_alpha as apigwv2_integrations,
)
from aws_cdk import aws_cognito as cognito

try:
    # Preferred for Python Lambda bundling (requires Docker)
    from aws_cdk import aws_lambda_python_alpha as lambda_python
except Exception:
    lambda_python = None  # type: ignore


class AiDjStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env: Optional[Environment] = None,
        spotify_secret_arn: Optional[str] = None,
        allowed_origins: Optional[list[str]] = None,
        bedrock_region: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, env=env, **kwargs)

        # Config
        allowed_origins = allowed_origins or [
            "http://localhost:3000",
            "https://localhost:3000",
            "https://*.vercel.app",
        ]
        bedrock_region = bedrock_region or (env.region if env else "us-east-1")

        # DynamoDB: Playlists table
        table = dynamodb.Table(
            self,
            "PlaylistsTable",
            table_name=f"aijdj-playlists-{self.account}-{self.region}",
            partition_key=dynamodb.Attribute(name="playlist_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        table.add_global_secondary_index(
            index_name="by_user",
            partition_key=dynamodb.Attribute(name="user_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="created_at", type=dynamodb.AttributeType.STRING),
        )

        # S3: Data bucket
        bucket = s3.Bucket(
            self,
            "DataBucket",
            bucket_name=f"aijdj-data-{self.account}-{self.region}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # SQS: DLQ and main queue
        dlq = sqs.Queue(
            self,
            "PlaylistRequestsDLQ",
            queue_name=f"aijdj-playlist-requests-dlq-{self.account}-{self.region}",
            retention_period=Duration.days(14),
        )
        queue = sqs.Queue(
            self,
            "PlaylistRequestsQueue",
            queue_name=f"aijdj-playlist-requests-{self.account}-{self.region}",
            visibility_timeout=Duration.seconds(60),
            dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=3, queue=dlq),
        )

        # Optional: Secrets Manager secret for Spotify credentials (user-provided)
        secret: Optional[secretsmanager.ISecret] = None
        if spotify_secret_arn:
            secret = secretsmanager.Secret.from_secret_complete_arn(
                self, "SpotifySecret", spotify_secret_arn
            )

        # Lambda: API (FastAPI via Mangum)
        api_env = {
            "TABLE_NAME": table.table_name,
            "BUCKET_NAME": bucket.bucket_name,
            "QUEUE_URL": queue.queue_url,
            "ALLOWED_ORIGINS": ",".join(allowed_origins),
            "BEDROCK_REGION": bedrock_region,
        }
        if spotify_secret_arn:
            api_env["SPOTIFY_SECRET_ARN"] = spotify_secret_arn

        if lambda_python is not None:
            api_fn = lambda_python.PythonFunction(
                self,
                "ApiFunction",
                entry=os.path.join(os.path.dirname(__file__), "..", "lambdas", "api"),
                index="main.py",
                handler="handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                timeout=Duration.seconds(30),
                memory_size=512,
                environment=api_env,
            )
        else:
            api_fn = _lambda.Function(
                self,
                "ApiFunction",
                code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "..", "lambdas", "api")),
                handler="main.handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                timeout=Duration.seconds(30),
                memory_size=512,
                environment=api_env,
            )

        table.grant_read_data(api_fn)
        queue.grant_send_messages(api_fn)
        if secret is not None:
            secret.grant_read(api_fn)

        # Lambda: Worker (SQS consumer)
        worker_env = {
            "TABLE_NAME": table.table_name,
            "BUCKET_NAME": bucket.bucket_name,
            "BEDROCK_REGION": bedrock_region,
        }
        if spotify_secret_arn:
            worker_env["SPOTIFY_SECRET_ARN"] = spotify_secret_arn

        if lambda_python is not None:
            worker_fn = lambda_python.PythonFunction(
                self,
                "WorkerFunction",
                entry=os.path.join(os.path.dirname(__file__), "..", "lambdas", "worker"),
                index="handler.py",
                handler="lambda_handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                timeout=Duration.seconds(120),
                memory_size=1024,
                environment=worker_env,
            )
        else:
            worker_fn = _lambda.Function(
                self,
                "WorkerFunction",
                code=_lambda.Code.from_asset(os.path.join(os.path.dirname(__file__), "..", "lambdas", "worker")),
                handler="handler.lambda_handler",
                runtime=_lambda.Runtime.PYTHON_3_11,
                timeout=Duration.seconds(120),
                memory_size=1024,
                environment=worker_env,
            )

        table.grant_read_write_data(worker_fn)
        bucket.grant_read_write(worker_fn)
        if secret is not None:
            secret.grant_read(worker_fn)

        # Allow worker to call Bedrock (placeholder permissions)
        worker_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=["*"],  # Narrow to required models as you adopt Bedrock
            )
        )

        # Event source mapping for SQS
        worker_fn.add_event_source(lambda_events.SqsEventSource(queue, batch_size=5))

        # API Gateway HTTP API + Lambda proxy integration
        http_api = apigwv2.HttpApi(
            self,
            "HttpApi",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_headers=["*"],
                allow_methods=[apigwv2.CorsHttpMethod.ANY],
                allow_origins=allowed_origins,
                max_age=Duration.days(10),
            ),
        )

        http_api.add_routes(
            path="/{proxy+}",
            methods=[apigwv2.HttpMethod.ANY],
            integration=apigwv2_integrations.HttpLambdaIntegration("ApiIntegration", api_fn),
        )
        # Cognito User Pool and App Client
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"aijdj-users-{self.account}-{self.region}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(required=True, mutable=False)
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=user_pool,
            user_pool_client_name="aijdj-web",
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True, implicit_code_grant=False),
                callback_urls=["http://localhost:3000/callback"],
                logout_urls=["http://localhost:3000"],
            ),
            generate_secret=False,
        )

        # Note: Configure API auth at the route level later if needed
        # Outputs
        CfnOutput(self, "HttpApiUrl", value=http_api.api_endpoint)
        CfnOutput(self, "TableName", value=table.table_name)
        CfnOutput(self, "BucketName", value=bucket.bucket_name)
        CfnOutput(self, "QueueUrl", value=queue.queue_url)
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)
