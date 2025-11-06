#!/usr/bin/env python3
import os
import aws_cdk as cdk
from infra.stack import AiDjStack

app = cdk.App()

# Environment settings
account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-2")

# Context variables
spotify_secret_arn = app.node.try_get_context("spotifySecretArn")
allowed_origins = app.node.try_get_context("allowedOrigins") or None
playlists_table_name = app.node.try_get_context("playlistsTableName") or None
datasets_table_name = app.node.try_get_context("datasetsTableName") or None

# Create the stack
AiDjStack(
	app,
	"AiDjStack",
	env=cdk.Environment(account=account, region=region),
	spotify_secret_arn=spotify_secret_arn,
	allowed_origins=allowed_origins,
    playlists_table_name=playlists_table_name,
    datasets_table_name=datasets_table_name,
)

app.synth()
