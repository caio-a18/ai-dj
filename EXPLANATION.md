# AI‑DJ: Data and Auth Integration Guide

This document explains two things:
- How the ML team should inject data into Amazon S3 in a way the backend understands.
- How the frontend team should connect user login with Cognito and call the API.

Bucket and region (current project)
- Bucket: aidj-data
- Region: us-east-2
- Prefixes used:
  - datasets/ — any ML-owned inputs/artifacts
  - playlists/ — full playlist JSON payloads (one file per playlist)

---

## 1) ML team: how to inject data into S3

### 1.1 Access
Use an IAM role with least-privilege S3 permissions. Minimum policy (same account) to read/write only the two prefixes:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "arn:aws:s3:::aidj-data",
      "Condition": {
        "StringLike": { "s3:prefix": ["datasets/*", "playlists/*"] }
      }
    },
    {
      "Sid": "RWOnDatasetsAndPlaylists",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject","s3:PutObject","s3:DeleteObject",
        "s3:AbortMultipartUpload","s3:ListMultipartUploadParts","s3:ListBucketMultipartUploads"
      ],
      "Resource": [
        "arn:aws:s3:::aidj-data/datasets/*",
        "arn:aws:s3:::aidj-data/playlists/*"
      ]
    }
  ]
}
```

If you’re in a different AWS account, add a trust policy on our role to allow your account to assume it, and optionally add a bucket policy granting that role.

### 1.2 What to upload where
- Training corpora, features, model artifacts → s3://aidj-data/datasets/... (your structure)
- Produced playlists → s3://aidj-data/playlists/{playlist_id}.json

The backend already understands playlist JSON stored under playlists/ and provides an API to retrieve it.

### 1.3 Playlist JSON contract (system of record)
One JSON file per playlist with this structure:

```json
{
  "playlist_id": "9e6c7b62-9dfb-4b30-9a73-0f5d1b06a9f0",
  "metadata": {
    "user_id": "u1",
    "prompt": "50 energetic pop songs",
    "created_at": 1730850000,
    "model_version": "v1"
  },
  "songs": [
    {
      "id": "3GZoWLVbmxcBys6g0DLFLf",
      "title": "Blinding Lights",
      "artist": "The Weeknd",
      "album": "After Hours",
      "url": "https://open.spotify.com/track/3GZoWLVbmxcBys6g0DLFLf",
      "duration_ms": 200040,
      "score": 0.92
    }
  ]
}
```

Minimum required per song: title and artist OR a stable id/url. Additional fields are optional.

### 1.4 Upload examples (PowerShell)
Use AWS CLI v2 (installed at `C:\Program Files\Amazon\AWSCLIV2\aws.exe`). Replace `<PROFILE>` if needed.

```powershell
$AWS = "C:\Program Files\Amazon\AWSCLIV2\aws.exe"
$env:AWS_PROFILE = "aijdj"
$env:AWS_DEFAULT_REGION = "us-east-2"

# Upload a dataset artifact
& $AWS s3 cp .\examples\datasets\tracks_sample.csv s3://aidj-data/datasets/examples/tracks_sample.csv

# Upload a playlist JSON
& $AWS s3 cp .\examples\playlists\sample_playlist.json s3://aidj-data/playlists/sample_playlist.json --content-type application/json
```

### 1.5 DynamoDB integration (metadata index)
The backend writes/updates DynamoDB metadata when it creates playlists. If the ML team will upload playlist JSONs directly and wants them to appear automatically in the API listings, there are two options:
- Event-driven: we add an S3 event → Lambda that upserts DynamoDB when new playlists/*.json arrive (recommended; no DynamoDB permissions needed for ML).
- Direct write: grant ML role DynamoDB PutItem/UpdateItem on the playlists table; you write both S3 and DynamoDB.


---

## 2) Frontend team: Cognito login and calling the API

### 2.1 Cognito setup you’ll be given
- Hosted UI Domain: https://<your-domain>.auth.<region>.amazoncognito.com
- User Pool ID: <pool_id>
- App Client ID: <client_id> (no secret)
- Region: us-east-2 (for this project)
- Allowed callback URLs: http://localhost:3000/callback (add prod later)
- Allowed sign-out URLs: http://localhost:3000/
- OAuth flow: Authorization Code with PKCE
- Scopes: openid, email, profile

### 2.2 Quick start options
- Option A: Use AWS Amplify Auth (simplest for SPA)
- Option B: Do raw OAuth PKCE yourself (more control)

#### Option A: Amplify (React/Vue/Vanilla)
Install and configure:
```ts
import { Amplify } from 'aws-amplify';
import { fetchAuthSession, signInWithRedirect, signOut } from 'aws-amplify/auth';

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: '<pool_id>',
      userPoolClientId: '<client_id>',
      loginWith: { oauth: { domain: '<your-domain>.auth.us-east-2.amazoncognito.com', scopes: ['openid','email','profile'], redirectSignIn: ['http://localhost:3000/callback'], redirectSignOut: ['http://localhost:3000/'], responseType: 'code' } },
      region: 'us-east-2',
    }
  }
});

// Trigger login
await signInWithRedirect();

// After redirect back to /callback, Amplify completes the code exchange automatically.
const session = await fetchAuthSession();
const idToken = session.tokens?.idToken?.toString();
```

Call the API with the ID token (API Gateway JWT authorizer expects a valid Cognito token):
```ts
const res = await fetch('<HttpApiUrl>/playlists/request', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${idToken}` },
  body: JSON.stringify({ prompt: "50 energetic pop songs", user_id: "u1", count: 50 })
});
```

Fetch a playlist later:
```ts
const meta = await fetch('<HttpApiUrl>/playlists/<playlist_id>', { headers: { Authorization: `Bearer ${idToken}` }}).then(r=>r.json());
const data = await fetch('<HttpApiUrl>/playlists/<playlist_id>/data', { headers: { Authorization: `Bearer ${idToken}` }}).then(r=>r.json());
```

#### Option B: Raw OAuth PKCE (outline)
1) Generate `code_verifier` and `code_challenge` (S256).
2) Redirect user to Hosted UI authorize URL:
```
https://<domain>.auth.us-east-2.amazoncognito.com/oauth2/authorize?client_id=<client_id>&response_type=code&redirect_uri=http://localhost:3000/callback&scope=openid+email+profile&code_challenge_method=S256&code_challenge=<challenge>
```
3) On /callback, exchange code + `code_verifier` for tokens using the Cognito /oauth2/token endpoint.
4) Send the ID token in `Authorization: Bearer <id_token>` when calling the API.

> Tip: For SPAs, always prefer PKCE (no client secret in the browser).

### 2.3 CORS
The API enables CORS for allowed origins passed at deploy time. For local dev, http://localhost:3000 is included. If you see CORS errors, share your exact frontend origin so we can add it.

---

## 3) Mock data to try right now

This repo includes examples:
- `examples/datasets/tracks_sample.csv` — tiny CSV with a few songs.
- `examples/playlists/sample_playlist.json` — playlist JSON matching the contract above.

Upload them (PowerShell):
```powershell
$AWS = "C:\\Program Files\\Amazon\\AWSCLIV2\\aws.exe"
$env:AWS_PROFILE = "aijdj"; $env:AWS_DEFAULT_REGION = "us-east-2"
& $AWS s3 cp .\examples\datasets\tracks_sample.csv s3://aidj-data/datasets/examples/tracks_sample.csv
& $AWS s3 cp .\examples\playlists\sample_playlist.json s3://aidj-data/playlists/sample_playlist.json --content-type application/json
```

---

## 4) Values teams will need
- Bucket: aidj-data (us-east-2)
- HttpApiUrl: provided after deploy (CDK output)
- Cognito: domain, userPoolId, userPoolClientId (CDK output if we keep Cognito)

If you need auto-ingest from S3 → DynamoDB when a new playlist file appears, ping the backend—we can add a tiny S3 event Lambda to keep the index in sync without giving ML DynamoDB permissions.