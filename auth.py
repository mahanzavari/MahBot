from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Chat, Message
from werkzeug.security import generate_password_hash
from utils import send_verification_email
import re
from datetime import datetime, timedelta, UTC
import os
from werkzeug.utils import secure_filename

auth = Blueprint('auth', __name__)

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is strong"

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password')
            
    return render_template('auth/login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('auth/signup.html')
            
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            flash(message)
            return render_template('auth/signup.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('auth/signup.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already taken')
            return render_template('auth/signup.html')
            
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        try:
            send_verification_email(user, current_app.extensions['mail'])
            flash('Please check your email to verify your account.')
        except Exception as e:
            flash('Error sending verification email. Please try again later.')
            current_app.logger.error(f'Error sending verification email: {str(e)}')
        
        login_user(user)
        return redirect(url_for('index'))
        
    return render_template('auth/signup.html')

@auth.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user is None:
        flash('Invalid verification token')
        return redirect(url_for('index'))
    
    # Check if token is expired (24 hours)
    if user.verification_sent_at and datetime.now(UTC) - user.verification_sent_at > timedelta(hours=24):
        flash('Verification token has expired. Please request a new one.')
        return redirect(url_for('auth.dashboard'))
    
    user.email_verified = True
    user.verification_token = None
    user.verification_sent_at = None
    db.session.commit()
    
    flash('Your email has been verified!')
    return redirect(url_for('auth.dashboard'))

@auth.route('/resend-verification', methods=['POST'])
@login_required
def resend_verification():
    if current_user.email_verified:
        return jsonify({'success': False, 'message': 'Email already verified'})
    
    try:
        send_verification_email(current_user, current_app.extensions['mail'])
        return jsonify({'success': True, 'message': 'Verification email sent'})
    except Exception as e:
        current_app.logger.error(f'Error sending verification email: {str(e)}')
        return jsonify({'success': False, 'message': 'Error sending verification email'})

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'redirect': url_for('auth.login')})
    return redirect(url_for('auth.login'))

@auth.route('/dashboard')
@login_required
def dashboard():
    # Get user statistics
    total_chats = Chat.query.filter_by(user_id=current_user.id).count()
    total_messages = Message.query.join(Chat).filter(Chat.user_id == current_user.id).count()
    
    # Get recent chats
    recent_chats = Chat.query.filter_by(user_id=current_user.id)\
        .order_by(Chat.created_at.desc())\
        .limit(5)\
        .all()
    
    # Get chat activity by day (last 7 days)
    today = datetime.now(UTC).date()
    chat_activity = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = Chat.query.filter(
            Chat.user_id == current_user.id,
            db.func.date(Chat.created_at) == date
        ).count()
        chat_activity.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    return render_template('auth/dashboard.html',
                         user=current_user,
                         total_chats=total_chats,
                         total_messages=total_messages,
                         recent_chats=recent_chats,
                         chat_activity=chat_activity)

@auth.route('/profile', methods=['POST'])
@login_required
def update_profile():
    display_name = request.form.get('display_name', '').strip()
    avatar = request.files.get('avatar')
    user = current_user
    updated = False
    # Update display name
    if display_name and display_name != user.display_name:
        user.display_name = display_name
        updated = True
    # Handle avatar upload
    if avatar and avatar.filename:
        filename = secure_filename(f'user_{user.id}_avatar_{avatar.filename}')
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, filename)
        avatar.save(file_path)
        # Save relative URL for use in templates
        user.avatar_url = url_for('static', filename=f'uploads/{filename}')
        updated = True
    if updated:
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'No changes made.'}) 