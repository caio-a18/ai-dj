from __future__ import annotations

import aws_cdk as cdk
from aws_cdk.assertions import Template

from infra.stack import AiDjStack


def test_cdk_template_has_core_resources():
    app = cdk.App()
    stack = AiDjStack(app, "TestStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::DynamoDB::Table", 1)
    template.resource_count_is("AWS::S3::Bucket", 1)
    template.resource_count_is("AWS::SQS::Queue", 2)  # main + DLQ
    template.resource_count_is("AWS::Lambda::Function", 2)  # API + Worker
    template.resource_count_is("AWS::Cognito::UserPool", 1)
    template.resource_count_is("AWS::Cognito::UserPoolClient", 1)
    # HTTP API components exist
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)
