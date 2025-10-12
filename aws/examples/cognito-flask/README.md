# Cognito + Flask (Authlib) Example

This is a minimal example that shows how to authenticate users against an Amazon Cognito User Pool using the Hosted UI and OpenID Connect.

## Prerequisites
- A Cognito User Pool with a Hosted UI domain
- An App Client (public) with Authorization Code Grant and scopes: `openid email profile`
- Callback URL: `http://127.0.0.1:5000/authorize`

## Configure
Set these environment variables before running:

- COGNITO_AUTHORITY: https://cognito-idp.<region>.amazonaws.com/<user_pool_id>
- COGNITO_CLIENT_ID: <your client id>
- COGNITO_CLIENT_SECRET: <your client secret> (if your client uses a secret)
- COGNITO_SCOPE: openid email profile
- REDIRECT_URI: http://127.0.0.1:5000/authorize
- FLASK_SECRET_KEY: random string

## Install and run

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$Env:COGNITO_AUTHORITY = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXX"
$Env:COGNITO_CLIENT_ID = "<CLIENT_ID>"
$Env:COGNITO_CLIENT_SECRET = "<CLIENT_SECRET>"
$Env:REDIRECT_URI = "http://127.0.0.1:5000/authorize"
python app.py
```

Open http://127.0.0.1:5000 and click Login.
