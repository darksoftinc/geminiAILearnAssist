# Use this Flask blueprint for Google authentication. Do not use flask-dance.
import json
import os
import requests
from app import db
from flask import Blueprint, redirect, request, url_for, flash, current_app
from flask_login import login_required, login_user, logout_user
from models import User
from oauthlib.oauth2 import WebApplicationClient

GOOGLE_CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]
GOOGLE_CLIENT_SECRET = os.environ["GOOGLE_OAUTH_CLIENT_SECRET"]
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)

@google_auth.route("/google_login")
def login():
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        # Get the current domain from environment
        domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
        redirect_uri = f"https://{domain}/google_login/callback"
        
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
        )
        
        current_app.logger.info(f"Redirecting to Google OAuth: {request_uri}")
        return redirect(request_uri)
    except Exception as e:
        current_app.logger.error(f"Google OAuth login error: {str(e)}")
        flash("Failed to initialize Google login", "error")
        return redirect(url_for('auth.login'))

@google_auth.route("/google_login/callback")
def callback():
    try:
        code = request.args.get("code")
        if not code:
            flash("Google authentication failed - no authorization code received", "error")
            return redirect(url_for('auth.login'))

        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
        redirect_url = f"https://{domain}/google_login/callback"
        
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=redirect_url,
            code=code
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        if not token_response.ok:
            flash("Failed to get token from Google", "error")
            return redirect(url_for('auth.login'))

        client.parse_request_body_response(json.dumps(token_response.json()))
        
        try:
            userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
            uri, headers, body = client.add_token(userinfo_endpoint)
            userinfo_response = requests.get(uri, headers=headers, data=body)
            
            if not userinfo_response.ok:
                flash("Failed to get user info from Google", "error")
                return redirect(url_for('auth.login'))

            userinfo = userinfo_response.json()
            if userinfo.get("email_verified"):
                users_email = userinfo["email"]
                users_name = userinfo["given_name"]
            else:
                flash("Email not verified by Google", "error")
                return redirect(url_for('auth.login'))
                
            user = User.query.filter_by(email=users_email).first()
            if not user:
                user = User(username=users_name, email=users_email)
                db.session.add(user)
                db.session.commit()

            login_user(user)
            current_app.logger.info(f"Successfully logged in user: {users_email}")
            return redirect(url_for('dashboard.index'))
            
        except Exception as e:
            current_app.logger.error(f"Error processing user info: {str(e)}")
            flash("Failed to process user information", "error")
            return redirect(url_for('auth.login'))
            
    except Exception as e:
        current_app.logger.error(f"Google authentication failed: {str(e)}")
        flash(f"Google authentication failed: {str(e)}", "error")
        return redirect(url_for('auth.login'))
