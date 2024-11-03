import json
import os
import secrets
import requests
from app import db
from flask import Blueprint, redirect, request, url_for, flash, current_app, session
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
        # Get the current domain from environment or request
        if request.headers.get('X-Forwarded-Proto') == 'https':
            domain = request.headers.get('X-Forwarded-Host', '')
        else:
            domain = os.environ.get("REPLIT_DEV_DOMAIN", "")
            
        redirect_uri = f"https://{domain}/google_login/callback"
        
        # Add state parameter for security
        state = secrets.token_hex(16)
        session['oauth_state'] = state
        
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
            state=state
        )
        
        # Log the redirect URI for debugging
        current_app.logger.info(f"OAuth redirect URI: {redirect_uri}")
        return redirect(request_uri)
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {str(e)}")
        flash("Google login initialization failed", "error")
        return redirect(url_for('auth.login'))

@google_auth.route("/google_login/callback")
def callback():
    try:
        # Verify state parameter
        state = request.args.get('state')
        stored_state = session.pop('oauth_state', None)
        
        if not state or state != stored_state:
            flash("Invalid OAuth state", "error")
            return redirect(url_for('auth.login'))

        code = request.args.get("code")
        if not code:
            flash("Google authentication failed - no authorization code received", "error")
            return redirect(url_for('auth.login'))

        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        if request.headers.get('X-Forwarded-Proto') == 'https':
            domain = request.headers.get('X-Forwarded-Host', '')
        else:
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
