from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from dao.users_dao import verify_user_credentials, register_new_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = verify_user_credentials(email, password)
        if user:
            login_user(user)
            flash(f"Welcome back, {user.first_name}!", "success")
            if user.is_guide:
                return redirect(url_for('guides.dashboard'))
            return redirect(url_for('participants.dashboard'))
            
        flash("Invalid email or password credentials.", "danger")
    return render_template('auth/login.html')

@auth_bp.route('/register/guide', methods=['GET', 'POST'])
def register_guide():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        selected_langs = request.form.getlist('languages') # HTML checkbox array
        
        if not email or not password or not first_name or not last_name or not selected_langs:
            flash("All structural framework context properties are strictly mandatory.", "danger")
            return redirect(url_for('auth.register_guide'))

        # Backend validations matching assignment constraints
        allowed = {'Italian', 'English', 'Spanish', 'Portuguese', 'German'}
        if not all(l in allowed for l in selected_langs):
            flash("Unauthorized language input mutation detected.", "danger")
            return redirect(url_for('auth.register_guide'))

        success = register_new_user(email, password, first_name, last_name, 'guide', selected_langs)
        if success:
            flash("Guide identity provisioned successfully. You can now log in.", "success")
            return redirect(url_for('auth.login'))
        
        flash("Email register collision detected. Choose another address.", "danger")
    return render_template('auth/register_guide.html')

@auth_bp.route('/register/participant', methods=['GET', 'POST'])
def register_participant():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')

        if not email or not password or not first_name or not last_name:
            flash("All profile fields are mandatory.", "danger")
            return redirect(url_for('auth.register_participant'))

        success = register_new_user(email, password, first_name, last_name, 'participant')
        if success:
            flash("Participant profile created. Welcome aboard!", "success")
            return redirect(url_for('auth.login'))
            
        flash("Registration failed. Email is already taken.", "danger")
    return render_template('auth/register_participant.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Session logged out cleanly.", "info")
    return redirect(url_for('main.index'))