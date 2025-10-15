# ai-dj

## Local Demo (Option A: Purely Local with LocalStack)

This walkthrough lets you demo the system end-to-end without using real AWS. You'll enqueue a playlist request, run a local worker to process it, and read the stored result from a local DynamoDB table.

Prereqs:
- Docker Desktop running
- LocalStack (community) container
- AWS CLI configured (any dummy credentials will do for LocalStack)
- Python 3.11+ venv with dev deps installed

### 1) Start LocalStack

PowerShell:

```powershell
docker run --rm -it -p 4566:4566 -p 4510-4559:4510-4559 localstack/localstack:latest
```

Leave this running in a window.

### 2) Create local AWS resources

Open a new terminal and set a couple env vars for convenience:

```powershell
$env:AWS_ENDPOINT_URL = "http://localhost:4566"
$env:AWS_REGION = "us-east-1"
$env:AWS_ACCESS_KEY_ID = "test"
$env:AWS_SECRET_ACCESS_KEY = "test"
```

Create DynamoDB table, SQS queue, and a Secrets Manager secret:

```powershell
aws --endpoint-url $env:AWS_ENDPOINT_URL dynamodb create-table `
	--table-name playlists `
	--attribute-definitions AttributeName=playlist_id,AttributeType=S `
	--key-schema AttributeName=playlist_id,KeyType=HASH `
	--billing-mode PAY_PER_REQUEST `
	--region $env:AWS_REGION

aws --endpoint-url $env:AWS_ENDPOINT_URL sqs create-queue `
	--queue-name playlist-requests `
	--region $env:AWS_REGION

aws --endpoint-url $env:AWS_ENDPOINT_URL secretsmanager create-secret `
	--name ai-dj/spotify/credentials `
	--secret-string '{"spotify_client_id":"dummy","spotify_client_secret":"dummy","spotify_redirect_uri":"http://127.0.0.1:3000/callback"}' `
	--region $env:AWS_REGION
```

Get the queue URL and save it to an env var:

```powershell
$queue = aws --endpoint-url $env:AWS_ENDPOINT_URL sqs get-queue-url --queue-name playlist-requests --region $env:AWS_REGION | ConvertFrom-Json
$env:QUEUE_URL = $queue.QueueUrl
```

### 3) Install dev dependencies

From the repo root (venv active):

```powershell
pip install -r ai-dj/aws/requirements-dev.txt
pip install -r ai-dj/aws/lambdas/api/requirements.txt
pip install -r ai-dj/aws/lambdas/worker/requirements.txt
```

### 4) Run the API locally

In a terminal (venv active):

```powershell
$env:AWS_ENDPOINT_URL = "http://localhost:4566"; `
$env:AWS_REGION = "us-east-1"; `
$env:TABLE_NAME = "playlists"; `
$env:QUEUE_URL = $env:QUEUE_URL; `
$env:SPOTIFY_SECRET_ARN = "ai-dj/spotify/credentials"; `
python ai-dj\aws\lambdas\api\dev_api.py
```

This starts FastAPI at http://127.0.0.1:8000.

Enqueue a request (PowerShell):

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/playlists/request" -Method Post -ContentType "application/json" -Body '{"prompt":"songs like Blinding Lights","user_id":"demo","count":5}'
```

Alternative: enqueue directly to SQS (bypass API):

```powershell
aws --endpoint-url $env:AWS_ENDPOINT_URL sqs send-message `
	--queue-url $env:QUEUE_URL `
	--message-body '{"type":"playlist_request","prompt":"songs like Blinding Lights","user_id":"demo","count":5}' `
	--region $env:AWS_REGION
```

### 5) Run the local dev worker

In another terminal (venv active):

```powershell
$env:AWS_ENDPOINT_URL = "http://localhost:4566"; `
$env:AWS_REGION = "us-east-1"; `
$env:TABLE_NAME = "playlists"; `
$env:QUEUE_URL = $env:QUEUE_URL; `
$env:SPOTIFY_SECRET_ARN = "ai-dj/spotify/credentials"; `
python ai-dj\aws\lambdas\worker\dev_worker.py
```

You should see the worker pick up the message and write a playlist item.

### 6) Verify in DynamoDB

List items (LocalStack supports PartiQL select for simplicity):

```powershell
aws --endpoint-url $env:AWS_ENDPOINT_URL dynamodb scan --table-name playlists --region $env:AWS_REGION
```

You should see an item with status "ready" and a list of mocked songs. If you set real Spotify credentials in the secret, the worker will try to seed the list with real search results for the base query it extracts.

### Troubleshooting

- If `uvicorn` isn't found, ensure you've installed dev deps: `pip install -r ai-dj/aws/requirements-dev.txt` in your active venv.
- If AWS CLI commands fail, double-check `$env:AWS_ENDPOINT_URL` is set and LocalStack is running on port 4566.
- On first run, the queue URL is dynamic. Re-run the `get-queue-url` command if you restarted the container.
- If the worker prints "TABLE_NAME not configured", verify `$env:TABLE_NAME` is set in the same terminal where you run the worker.

## No-Docker Fallback (Moto single-process demo)

If Docker isn't available on your machine, you can still show the flow using moto (mock AWS) in a single Python process.

Run (venv active):

```powershell
pip install -r ai-dj/aws/requirements-dev.txt
pip install -r ai-dj/aws/lambdas/api/requirements.txt
pip install -r ai-dj/aws/lambdas/worker/requirements.txt
python ai-dj\aws\scripts\local_demo_moto.py
```

What you'll see:
- API health output
- Enqueue response
- Worker processes a message
- DynamoDB mock item printed with a playlist
