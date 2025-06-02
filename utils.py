from flask import url_for
from flask_mail import Message
from datetime import datetime, timedelta, UTC
from models import db
import os
import logging
import torch

logger = logging.getLogger(__name__)

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

def check_gpu_availability():
    """Check if GPU is available and return appropriate configuration."""
    try:
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU detected: {gpu_name} (Count: {gpu_count})")
            return {
                'has_gpu': True,
                'gpu_count': gpu_count,
                'gpu_name': gpu_name,
                'n_gpu_layers': -1  # Use all layers on GPU
            }
        else:
            logger.info("No GPU detected, using CPU")
            return {
                'has_gpu': False,
                'n_gpu_layers': 0  # Use CPU only
            }
    except Exception as e:
        logger.error(f"Error checking GPU availability: {str(e)}")
        return {
            'has_gpu': False,
            'n_gpu_layers': 0  # Fallback to CPU
        } 