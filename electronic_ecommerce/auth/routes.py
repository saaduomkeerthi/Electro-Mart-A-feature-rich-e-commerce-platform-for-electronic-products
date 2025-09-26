# electronic_ecommerce/auth/routes.py

import random
import string
import io
from PIL import Image, ImageDraw, ImageFont
from flask import (
    Blueprint, render_template, request, jsonify, session, redirect, url_for, send_file
)
from flask_mail import Message
from .. import mail

# --- MODEL IMPORTS ---
from ..models.user_model import (
    register_user,
    login_user,
    get_user_by_email,
    get_password_reset_token,
    verify_password_reset_token,
    update_password_for_user
)

# Define the blueprint for all authentication-related routes
auth_bp = Blueprint('auth_bp', __name__, template_folder='templates')

# -----------------------------------------------------------------------------
# AUTHENTICATION ROUTES
# -----------------------------------------------------------------------------

@auth_bp.route("/register", methods=['GET', 'POST'])
def register():
    """Handles user registration."""
    if request.method == 'POST':
        data = request.get_json()
        response, status_code = register_user(data)
        return jsonify(response), status_code
    return render_template("register.html")


@auth_bp.route("/login", methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    Validates credentials and CAPTCHA, then redirects all successful logins
    to a central dispatcher route.
    """
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        captcha_input = data.get('captcha')

        if 'captcha_text' not in session or not captcha_input or captcha_input.upper() != session['captcha_text'].upper():
            return jsonify({"error": "Invalid CAPTCHA. Please try again."}), 400

        user = login_user(email, password)

        if user:
            session.pop('captcha_text', None)
            session['user_id'] = user['user_id']
            session['full_name'] = user['full_name']
            session['user_role'] = user['role']

            redirect_url = url_for('home_bp.dashboard_redirect')

            return jsonify({"message": "Login successful! Redirecting...", "redirect_url": redirect_url}), 200
        else:
            return jsonify({"error": "Invalid email, password, or CAPTCHA."}), 401

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    """Logs the user out by clearing all session data."""
    session.clear()
    return redirect(url_for('landing'))


@auth_bp.route("/captcha")
def captcha():
    """Generates a new CAPTCHA image and stores its text in the session."""
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    session['captcha_text'] = captcha_text

    img = Image.new('RGB', (150, 60), color=(240, 240, 240))
    d = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 35)
    except IOError:
        font = ImageFont.load_default()

    d.text((10, 10), captcha_text, fill=(70, 130, 180), font=font)

    for _ in range(5):
        d.line([(random.randint(0, 150), random.randint(0, 60)),
                (random.randint(0, 150), random.randint(0, 60))], fill=(160, 160, 160))

    buf = io.BytesIO()
    img.save(buf, 'PNG')
    buf.seek(0)

    return send_file(buf, mimetype='image/png')

# -----------------------------------------------------------------------------
# PASSWORD RESET ROUTES
# -----------------------------------------------------------------------------

def send_password_reset_email(user):
    """Generates a token and sends the password reset email to the user."""
    token = get_password_reset_token(user['user_id'])
    reset_url = url_for('auth_bp.reset_password_with_token', token=token, _external=True)
    
    msg = Message('Password Reset Request for ElectroMart',
                  recipients=[user['email']])
    
    msg.body = f'''Hello {user['full_name']},

To reset your password, please visit the following link:
{reset_url}

If you did not make this request, simply ignore this email and no changes will be made.
This link will expire in 30 minutes.

Sincerely,
The ElectroMart Team
'''
    mail.send(msg)


@auth_bp.route("/forgot_password", methods=['GET', 'POST'])
def forgot_password():
    """
    Handles the first step of password reset.
    GET: Renders the page to enter an email.
    POST: Processes the email and sends a reset link.
    """
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({"error": "Email address is required."}), 400

        user = get_user_by_email(email)

        if user:
            try:
                send_password_reset_email(user)
            except Exception as e:
                print(f"MAIL SENDING ERROR: {e}")
                return jsonify({"error": "Could not send reset email. Please try again later."}), 500

        return jsonify({
            "message": "If an account with that email exists, a password reset link has been sent."
        }), 200
        
    return render_template("forgot_password.html")


@auth_bp.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_password_with_token(token):
    """
    Handles the second step of password reset.
    GET: Verifies the token and shows the password reset form.
    POST: Processes the new password submission.
    """
    user_id = verify_password_reset_token(token)
    
    if user_id is None:
        return render_template("message_display.html", 
                               title="Invalid Token",
                               message="The password reset link is invalid or has expired.",
                               link_url=url_for('auth_bp.forgot_password'),
                               link_text="Request a new reset link")

    if request.method == 'POST':
        data = request.get_json()
        new_password = data.get('password')

        if not new_password or len(new_password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long."}), 400

        success, message = update_password_for_user(user_id, new_password)

        if success:
            return jsonify({
                "message": "Password reset successfully! Redirecting to login...",
                "redirect_url": url_for('auth_bp.login')
            }), 200
        else:
            return jsonify({"error": message}), 500

    return render_template("reset_password.html", token=token)