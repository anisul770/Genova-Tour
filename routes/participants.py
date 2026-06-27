from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from dao.tours_dao import get_tour_complete_details
from dao.users_dao import update_user_profile
from dao.reservations_dao import get_booked_seats_count, check_participant_overlap, create_reservation, cancel_reservation, get_participant_agenda

participants_bp = Blueprint('participants', __name__)

@participants_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_participant:
        return "Access Forbidden", 403
    agenda = get_participant_agenda(current_user.id)
    return render_template('participants/dashboard.html', agenda=agenda)

@participants_bp.route('/book/<int:tour_id>', methods=['POST'])
@login_required
def book_tour(tour_id):
    if not current_user.is_participant:
        return "Access Forbidden", 403

    tour = get_tour_complete_details(tour_id)
    target_date = request.form.get('tour_date') # Format: YYYY-MM-DD
    
    if not target_date:
        flash("Please select a valid date for reservation workflows.", "warning")
        return redirect(url_for('main.tour_detail', tour_id=tour_id))

    # Evaluate day validation constraint rules matching actual weekly setups
    parsed_date = datetime.strptime(target_date, "%Y-%m-%d")
    day_of_week = parsed_date.strftime("%A")
    
    valid_days = [s['day_of_week'] for s in tour['schedules']]
    if day_of_week not in valid_days:
        flash(f"Operational mismatch: This tour does not operate on a {day_of_week}.", "danger")
        return redirect(url_for('main.tour_detail', tour_id=tour_id))

    # Assemble extra passengers logic arrays safely
    guest_firsts = request.form.getlist('guest_first_name[]')
    guest_lasts = request.form.getlist('guest_last_name[]')
    
    guests = []
    for f, l in zip(guest_firsts, guest_lasts):
        if f.strip() and l.strip():
            guests.append({'first_name': f.strip(), 'last_name': l.strip()})
            
    party_size = 1 + len(guests)
    if party_size > 4:
        flash("Constraint violation: Individual ticketing profiles handle up to 4 passengers maximum.", "danger")
        return redirect(url_for('main.tour_detail', tour_id=tour_id))

    # Check capacity constraints
    already_booked = get_booked_seats_count(tour_id, target_date)
    if already_booked + party_size > tour['max_participants']:
        available = tour['max_participants'] - already_booked
        flash(f"Capacity Overflow error. Only {available} slots remain open for booking on this date.", "danger")
        return redirect(url_for('main.tour_detail', tour_id=tour_id))

    # Check schedule overlap conflicts
    if check_participant_overlap(current_user.id, target_date, tour_id):
        flash("Schedule intersection crash: You have an active tour reservation overlapping this timeframe.", "danger")
        return redirect(url_for('main.tour_detail', tour_id=tour_id))

    # Execute transactional commit paths
    success = create_reservation(current_user.id, tour_id, target_date, guests)
    if success:
        flash("Seats successfully reserved for your party. Check your agenda below.", "success")
    else:
        flash("System booking allocation processing fault.", "danger")
        
    return redirect(url_for('participants.dashboard'))

@participants_bp.route('/cancel/<int:res_id>', methods=['POST'])
@login_required
def cancel(res_id):
    if not current_user.is_participant:
        return "Access Forbidden", 403
        
    success, msg = cancel_reservation(res_id, current_user.id)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for('participants.dashboard'))

@participants_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'participant':
        flash('Unauthorized access layer.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        password_to_update = None
        if new_password:
            if new_password == confirm_password:
                password_to_update = new_password
            else:
                flash('Password confirmation mismatch.', 'danger')
                return redirect(url_for('participants.profile'))

        print(f"Updating profile for user_id={current_user.id} with first_name={first_name}, last_name={last_name}, password_to_update={'[REDACTED]' if password_to_update else None}")   
        success = update_user_profile(current_user.id, first_name, last_name, password_to_update)
        print(f"Update user profile result: {success}")
        if success:
            flash('Tourist credentials modified successfully.', 'success')
        else:
            flash('An error occurred updating your profile.', 'danger')
            
        return redirect(url_for('participants.dashboard'))

    return render_template('participants/profile.html')

@participants_bp.route('/participant_to_guide', methods=['GET', 'POST'])
@login_required
def participant_to_guide():
    """
    Transition a participant account to a guide account.
    """
    return render_template('participants/register_guide.html')

@participants_bp.route('/register_guide', methods=['GET', 'POST'])
@login_required
def register_guide():
    if request.method == 'POST':
        selected_languages = request.form.getlist('languages')
        update_user_profile(current_user.id, current_user.first_name, current_user.last_name,languages_list=selected_languages,role='guide')
    return render_template('guides/dashboard.html')