from flask import url_for
from flask_mail import Message
from datetime import datetime, timedelta, UTC
from models import db

def send_verification_email(user, mail):
    token = user.generate_verification_token()
    db.session.commit()  # Commit the token to database
    
    verification_url = url_for('auth.verify_email', token=token, _external=True)
    msg = Message('Verify Your Email',
                  recipients=[user.email])
    msg.body = f'''To verify your email, visit the following link:
{verification_url}

If you did not make this request then simply ignore this email.
'''
    msg.html = f'''
    <h1>Welcome to LegalQA Chatbot!</h1>
    <p>To verify your email, please click the button below:</p>
    <a href="{verification_url}" style="display: inline-block; padding: 10px 20px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px;">Verify Email</a>
    <p>If you did not make this request, please ignore this email.</p>
    '''
    mail.send(msg) 