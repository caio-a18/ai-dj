from __future__ import annotations

import os
from flask import Flask, redirect, url_for, session
from authlib.integrations.flask_client import OAuth

# Config via env vars to avoid hard-coding secrets
COGNITO_AUTHORITY = os.environ.get("COGNITO_AUTHORITY")  # e.g., https://cognito-idp.us-east-1.amazonaws.com/us-east-1_abc123
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")
COGNITO_CLIENT_SECRET = os.environ.get("COGNITO_CLIENT_SECRET")
COGNITO_SCOPE = os.environ.get("COGNITO_SCOPE", "openid email profile")
REDIRECT_URI = os.environ.get("REDIRECT_URI")  # e.g., http://127.0.0.1:5000/authorize

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24))
oauth = OAuth(app)

oauth.register(
    name="oidc",
    client_id=COGNITO_CLIENT_ID,
    client_secret=COGNITO_CLIENT_SECRET,
    server_metadata_url=f"{COGNITO_AUTHORITY}/.well-known/openid-configuration",
    client_kwargs={"scope": COGNITO_SCOPE},
)


@app.route("/")
def index():
    user = session.get("user")
    if user:
        return f'Hello, {user.get("email","user")} <a href="/logout">Logout</a>'
    return 'Welcome! Please <a href="/login">Login</a>.'


@app.route("/login")
def login():
    redirect_uri = REDIRECT_URI or url_for("authorize", _external=True)
    return oauth.oidc.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    token = oauth.oidc.authorize_access_token()
    user = token.get("userinfo") or {}
    session["user"] = user
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
