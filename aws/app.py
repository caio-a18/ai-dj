#!/usr/bin/env python3
import os
import aws_cdk as cdk
from infra.stack import AiDjStack

app = cdk.App()

account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")

# Optional context params, pass via `-c key=value` or cdk.json context
spotify_secret_arn = app.node.try_get_context("spotifySecretArn")
allowed_origins = app.node.try_get_context("allowedOrigins") or None

AiDjStack(
	app,
	"AiDjStack",
	env=cdk.Environment(account=account, region=region),
	spotify_secret_arn=spotify_secret_arn,
	allowed_origins=allowed_origins,
)

app.synth()
