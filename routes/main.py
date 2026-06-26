from flask import Blueprint, render_template, request
from dao.tours_dao import get_filtered_tours, get_tour_complete_details

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Extract structural UI parameters query inputs
    lang = request.args.get('language', None)
    duration = request.args.get('duration', None)
    date_val = request.args.get('date', None)

    tours = get_filtered_tours(date_filter=date_val, duration_filter=duration, language_filter=lang)
    return render_template('index.html', tours=tours, lang=lang, duration=duration, date_val=date_val)

@main_bp.route('/tour/<int:tour_id>')
def tour_detail(tour_id):
    tour = get_tour_complete_details(tour_id)
    if not tour:
        return "Tour details asset space missing.", 404
    return render_template('tour_detail.html', tour=tour)