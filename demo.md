# AWS Infrastructure:

## API Layer

- FastAPI on Lambda (Mangum)
- HTTP API Gateway (HTTP API)
- Routes: /health, /playlists/request, /playlists/{id}
- CORS allowlist
- JWT-ready via Cognito

## Queueing

- SQS main queue
- DLQ for failures
- Async decoupling
- 60s visibility
- Batch size 5

## Worker

- Lambda SQS trigger
- Parse prompt heuristics
- Optional Spotify seeds
- Writes to DynamoDB
- Offline mode supported

## Data

- DynamoDB playlists table
- PK: playlist_id (S)
- GSI: by_user (user_id, created_at)
- S3 bucket for artifacts
- Pay-per-request billing

## Auth

- Cognito User Pool
- App client (OIDC)
- JWT authorizer on API
- Hosted UI compatible
- Limited CORS origins

## Secrets

- AWS Secrets Manager
- Spotify client creds JSON
- Read-only Lambda access
- No secrets in code

## Security

- Least-privilege IAM
- DLQ resilience
- HTTPS enforced where relevant
- CORS allowlist only
- CloudWatch logs/metrics