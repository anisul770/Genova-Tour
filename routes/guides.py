import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from PIL import Image
from dao.users_dao import update_user_profile
from dao.tours_dao import get_tours_by_guide, has_tour_reservations, create_tour, get_tour_complete_details, update_tour_full, update_tour_limited
from dao.reservations_dao import get_guide_tour_metrics, submit_tour_attendance_report

guides_bp = Blueprint('guides', __name__)

def process_and_save_image(file_storage, folder_path, target_height=400, idx=None):
    """
    Leverages your professor's exact Pillow center-cropping layout logic
    with LANCZOS downsampling to generate crisp, square assets without distortions.
    """
    # Open data context stream safely
    img = Image.open(file_storage)
    width, height = img.size
    
    # Professor's dynamic aspect-ratio scaling equations
    new_width = target_height * width / height
    size = (new_width, target_height)
    img.thumbnail(size, Image.Resampling.LANCZOS)
    
    # Professor's clean center-cropping bounding coordinates box
    left = new_width / 2 - target_height / 2
    top = 0
    right = new_width / 2 + target_height / 2
    bottom = target_height
    img = img.crop((left, top, right, bottom))
    
    # Generate timestamp signature matching professor's database string conventions
    secs = int(datetime.now().timestamp())
    ext = file_storage.filename.split(".")[-1].lower()
    
    # Fix: If processing a batch loop, append index sequence to prevent file overwrite collisions
    if idx is not None:
        img_name = f"{secs}_{idx}.{ext}"
    else:
        img_name = f"{secs}.{ext}"
        
    # Ensure local directory folders are structurally present before committing write stream
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        
    full_dest_path = os.path.join(folder_path, img_name)
    img.save(full_dest_path)
    
    return img_name

@guides_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_guide:
        return "Access Forbidden", 403
    tours = get_tours_by_guide(current_user.id)
    
    # Bundle metrics structures for all historical listings dynamically
    for t in tours:
        t['metrics'] = get_guide_tour_metrics(t['id'])
    return render_template('guides/dashboard.html', tours=tours)

@guides_bp.route('/tour/new', methods=['GET', 'POST'])
@login_required
def create_new_tour():
    if not current_user.is_guide:
        return "Access Forbidden", 403
        
    if request.method == 'POST':
        title = request.form.get('title')
        meeting_point = request.form.get('meeting_point')
        duration = request.form.get('duration')
        language = request.form.get('language')
        max_p = request.form.get('max_participants')
        description = request.form.get('description')
        
        # Formulate stops array allocation mapping
        stops = request.form.getlist('stops[]')
        valid_stops = [s.strip() for s in stops if s.strip()]
        
        if len(valid_stops) < 4:
            flash("Structural error: Tour maps require at least 4 active stops verified.", "danger")
            return redirect(url_for('guides.create_new_tour'))

        if language not in current_user.languages:
            flash("Validation error: You cannot offer a tour in a language you do not speak.", "danger")
            return redirect(url_for('guides.create_new_tour'))

        # Map weekday schedule values
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        schedule_data = {}
        for d in days:
            time_val = request.form.get(f'sched_{d}')
            if time_val:
                schedule_data[d] = time_val

        if not schedule_data:
            flash("Tour routines must maintain at least 1 weekly operational day deployment mapping.", "danger")
            return redirect(url_for('guides.create_new_tour'))

        # Upload arrays scanning validation check routines
        uploaded_files = request.files.getlist('promo_photos')
        if len(uploaded_files) != 5:
            flash("Constraint mismatch: You must upload exactly 5 promotional verification photos.", "danger")
            return redirect(url_for('guides.create_new_tour'))

        filenames = []
        try:
            # Fix: Pass dynamic enumerate indexes down to the processing layer
            for idx, f in enumerate(uploaded_files):
                img = Image.open(f)
                width, height = img.size
                fn = process_and_save_image(f, current_app.config['UPLOAD_FOLDER_PROMO'],target_height=height, idx=idx)
                filenames.append(fn)
        except Exception:
            flash("Pillow layer processing failed. Check your file extension types.", "danger")
            return redirect(url_for('guides.create_new_tour'))

        create_tour(current_user.id, title, meeting_point, duration, language, max_p, description, schedule_data, valid_stops, filenames)
        flash("New Genoese Walking Tour added to public catalog systems successfully!", "success")
        return redirect(url_for('guides.dashboard'))

    return render_template('guides/tour_form.html', action="Create", languages=current_user.languages)

@guides_bp.route('/tour/edit/<int:tour_id>', methods=['GET', 'POST'])
@login_required
def edit_tour(tour_id):
    if not current_user.is_guide:
        return "Access Forbidden", 403
        
    tour = get_tour_complete_details(tour_id)
    if not tour or str(tour['guide_id']) != str(current_user.id):
        return "Asset manipulation ownership context invalid.", 401

    locked = has_tour_reservations(tour_id)

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Optional image modification array verification
        uploaded_files = request.files.getlist('promo_photos')
        has_new_images = len(uploaded_files) == 5 if uploaded_files and uploaded_files[0].filename else False
        
        filenames = []
        if has_new_images:
            for idx, f in enumerate(uploaded_files):
                img = Image.open(f)
                width, height = img.size
                fn = process_and_save_image(f, current_app.config['UPLOAD_FOLDER_PROMO'],target_height=height, idx=idx)
                filenames.append(fn)

        if locked:
            # Safe descriptive mutator fallback routines applied here
            update_tour_limited(tour_id, title, description, filenames if has_new_images else tour['images'])
            flash("Tour has reservations. Updated only non-essential description assets safely.", "info")
        else:
            # Perform complete destructive table modifications setup safely
            meeting_point = request.form.get('meeting_point')
            duration = request.form.get('duration')
            language = request.form.get('language')
            max_p = request.form.get('max_participants')
            stops = request.form.getlist('stops[]')
            valid_stops = [s.strip() for s in stops if s.strip()]

            if len(valid_stops) < 4:
                flash("Structural maps error: At least 4 chronological stops mandatory.", "danger")
                return redirect(url_for('guides.edit_tour', tour_id=tour_id))

            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            schedule_data = {}
            for d in days:
                time_val = request.form.get(f'sched_{d}')
                if time_val:
                    schedule_data[d] = time_val

            update_tour_full(tour_id, title, meeting_point, duration, language, max_p, description, schedule_data, valid_stops, filenames if has_new_images else None)
            flash("Tour layout fields fully customized and updated successfully.", "success")
            
        return redirect(url_for('guides.dashboard'))

    # Restructure active schedules object lookup helper formatting maps
    sched_map = {s['day_of_week']: s['start_time'] for s in tour['schedules']}
    return render_template('guides/tour_form.html', action="Edit", tour=tour, sched_map=sched_map, locked=locked, languages=current_user.languages)

@guides_bp.route('/tour/report/<int:tour_id>/<string:date_str>', methods=['GET', 'POST'])
@login_required
def report_tour(tour_id, date_str):
    if not current_user.is_guide:
        return "Access Forbidden", 403
    tour = get_tour_complete_details(tour_id)
    if not tour or str(tour['guide_id']) != str(current_user.id):
        return "Unauthorized operations.", 401

    if request.method == 'POST':
        count = request.form.get('actual_count')
        file_img = request.files.get('report_photo')

        if not count or not file_img:
            flash("Report payload processing requires explicit headcounts and image confirmation streams.", "danger")
            return redirect(request.url)

        try:
            # No sequence index needed here as report images are uploaded singular per record request
            img = Image.open(file_img)
            width, height = img.size
            fn = process_and_save_image(file_img, current_app.config['UPLOAD_FOLDER_REPORTS'],target_height=height)
            success = submit_tour_attendance_report(tour_id, date_str, count, fn)
            if success:
                flash("Attendance verification index data declared and stored safely. Commission logged.", "success")
            else:
                flash("System handling conflict: Report entity row execution duplicate blocked.", "danger")
        except Exception:
            flash("Pillow module engine translation crash validating input image stream.", "danger")
            
        return redirect(url_for('guides.dashboard'))

    return render_template('guides/report.html', tour=tour, date_str=date_str)

@guides_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'guide':
        flash('Unauthorized access layer.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        selected_languages = request.form.getlist('languages')
        print(f"Selected languages for update: {selected_languages}")
        
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        password_to_update = None
        if new_password:
            if new_password == confirm_password:
                password_to_update = new_password
            else:
                flash('Password confirmation mismatch.', 'danger')
                return redirect(url_for('guides.profile'))
        
        update_user_profile(current_user.id, first_name, last_name, password_to_update, selected_languages)
        
        flash('Guide profile updated successfully.', 'success')
        return redirect(url_for('guides.dashboard'))

    guide_languages = [lang for lang in current_user.languages] if hasattr(current_user, 'languages') else []
    return render_template('guides/profile.html', guide_languages=guide_languages)