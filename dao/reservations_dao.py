from dao.db import get_db_connection
from datetime import datetime, timedelta

def get_booked_seats_count(tour_id, date_string):
    conn = get_db_connection()
    query = """
        SELECT COUNT(r.id) AS explicit_bookings,
               (SELECT COUNT(*) FROM additional_participants WHERE reservation_id = r.id) AS extra_bookings
        FROM reservations r
        WHERE r.tour_id = ? AND r.tour_date = ?
    """
    rows = conn.execute(query, (tour_id, date_string)).fetchall()
    total = 0
    for row in rows:
        total += row['explicit_bookings'] + row['extra_bookings']
    conn.close()
    return total

def check_participant_overlap(participant_id, target_date_str, tour_id):
    """
    Verifies schedule integrity. Returns True if an operational timing conflict is detected.
    """
    conn = get_db_connection()
    
    # Target tour timing variables
    target_sched = conn.execute(
        "SELECT ts.day_of_week, ts.start_time, t.duration FROM tour_schedules ts JOIN tours t ON ts.tour_id = t.id WHERE t.id = ?",
        (tour_id,)
    ).fetchall()
    
    parsed_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_day = parsed_date.strftime("%A")
    
    target_time_str = None
    target_duration = 0
    for s in target_sched:
        if s['day_of_week'] == target_day:
            target_time_str = s['start_time']
            target_duration = s['duration']
            break
            
    if not target_time_str:
        conn.close()
        return False # Not operational on this date anyway

    t_start = datetime.strptime(f"{target_date_str} {target_time_str}", "%Y-%m-%d %H:%M")
    t_end = t_start + timedelta(minutes=target_duration)

    # Fetch existing commitments for this specific day
    commitments = conn.execute("""
        SELECT r.tour_id, ts.start_time, t.duration 
        FROM reservations r
        JOIN tours t ON r.tour_id = t.id
        JOIN tour_schedules ts ON ts.tour_id = t.id
        WHERE r.participant_id = ? AND r.tour_date = ?
    """, (participant_id, target_date_str)).fetchall()

    for c in commitments:
        c_day = parsed_date.strftime("%A")
        # Ensure scheduling checks extract correct matching days
        c_sched_time = conn.execute("SELECT start_time FROM tour_schedules WHERE tour_id = ? AND day_of_week = ?", (c['tour_id'], c_day)).fetchone()
        if not c_sched_time:
            continue
            
        c_start = datetime.strptime(f"{target_date_str} {c_sched_time['start_time']}", "%Y-%m-%d %H:%M")
        c_end = c_start + timedelta(minutes=c['duration'])
        
        # Intersect checks configuration
        if max(t_start, c_start) < min(t_end, c_end):
            conn.close()
            return True # Overlap conflict found

    conn.close()
    return False

def create_reservation(participant_id, tour_id, date_string, additional_guests=None):
    """
    Atoms atomic operations preserving capacity thresholds perfectly.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO reservations (participant_id, tour_id, tour_date) VALUES (?, ?, ?)", (participant_id, tour_id, date_string))
        res_id = cursor.lastrowid
        
        if additional_guests:
            for guest in additional_guests:
                if guest.get('first_name') and guest.get('last_name'):
                    cursor.execute(
                        "INSERT INTO additional_participants (reservation_id, first_name, last_name) VALUES (?, ?, ?)",
                        (res_id, guest['first_name'].strip(), guest['last_name'].strip())
                    )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def cancel_reservation(reservation_id, participant_id):
    """
    Enforces the mandatory 24-hour cancellation rule.
    """
    conn = get_db_connection()
    res = conn.execute("""
        SELECT r.*, ts.start_time 
        FROM reservations r
        JOIN tours t ON r.tour_id = t.id
        JOIN tour_schedules ts ON ts.tour_id = t.id
        WHERE r.id = ? AND r.participant_id = ?
    """, (reservation_id, participant_id)).fetchone()
    
    if not res:
        conn.close()
        return False, "Reservation entry could not be verified."

    # Parse execution barriers
    tour_date_parsed = datetime.strptime(res['tour_date'], "%Y-%m-%d")
    # Resolve the day name to map the schedule correctly
    day_name = tour_date_parsed.strftime("%A")
    
    sched_time_row = conn.execute("SELECT start_time FROM tour_schedules WHERE tour_id = ? AND day_of_week = ?", (res['tour_id'], day_name)).fetchone()
    time_str = sched_time_row['start_time'] if sched_time_row else "00:00"
    
    tour_datetime = datetime.strptime(f"{res['tour_date']} {time_str}", "%Y-%m-%d %H:%M")
    
    if tour_datetime - datetime.now() < timedelta(hours=24):
        conn.close()
        return False, "Cancellations are locked down within 24 hours of operational deployment."

    conn.execute("DELETE FROM reservations WHERE id = ?", (reservation_id,))
    conn.commit()
    conn.close()
    return True, "Reservation cancelled successfully."

def get_participant_agenda(participant_id):
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT r.id AS res_id, r.tour_date, t.title, t.meeting_point, t.id AS tour_id
        FROM reservations r
        JOIN tours t ON r.tour_id = t.id
        WHERE r.participant_id = ?
        ORDER BY r.tour_date DESC
    """, (participant_id,)).fetchall()
    
    agenda = []
    for r in rows:
        d = dict(r)
        parsed_date = datetime.strptime(d['tour_date'], "%Y-%m-%d")
        day_name = parsed_date.strftime("%A")
        
        st = conn.execute("SELECT start_time FROM tour_schedules WHERE tour_id = ? AND day_of_week = ?", (d['tour_id'], day_name)).fetchone()
        d['start_time'] = st['start_time'] if st else "N/A"
        
        guests = conn.execute("SELECT first_name, last_name FROM additional_participants WHERE reservation_id = ?", (d['res_id'],)).fetchall()
        d['guests'] = [f"{g['first_name']} {g['last_name']}" for g in guests]
        d['total_count'] = 1 + len(guests)
        
        # Check active cancellation clearance boundaries
        tour_dt = datetime.strptime(f"{d['tour_date']} {d['start_time']}", "%Y-%m-%d %H:%M") if st else datetime.now()
        d['can_cancel'] = (tour_dt - datetime.now()) > timedelta(hours=24)
        
        agenda.append(d)
        
    conn.close()
    return agenda

def get_guide_tour_metrics(tour_id):
    conn = get_db_connection()
    # Fetch distinct operational dates booked so far
    dates_rows = conn.execute("SELECT DISTINCT tour_date FROM reservations WHERE tour_id = ? ORDER BY tour_date DESC", (tour_id,)).fetchall()
    
    metrics = []
    for d_row in dates_rows:
        date_str = d_row['tour_date']
        
        res_list = conn.execute("SELECT id, participant_id FROM reservations WHERE tour_id = ? AND tour_date = ?", (tour_id, date_str)).fetchall()
        
        total_p = 0
        bookings_manifest = []
        for r in res_list:
            p_user = conn.execute("SELECT first_name, last_name, email FROM users WHERE id = ?", (r['participant_id'],)).fetchone()
            guests = conn.execute("SELECT first_name, last_name FROM additional_participants WHERE reservation_id = ?", (r['id'],)).fetchall()
            
            guest_names = [f"{g['first_name']} {g['last_name']}" for g in guests]
            total_p += 1 + len(guests)
            
            bookings_manifest.append({
                'lead_name': f"{p_user['first_name']} {p_user['last_name']}",
                'lead_email': p_user['email'],
                'guests': guest_names,
                'count': 1 + len(guests)
            })
            
        # Is report filed already?
        rep = conn.execute("SELECT * FROM tour_reports WHERE tour_id = ? AND tour_date = ?", (tour_id, date_str)).fetchone()
        
        # Determine execution chronological completion
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        # For validation simplicity, historical dates are treated as report eligible
        is_past = parsed_date.date() <= datetime.now().date()

        metrics.append({
            'date': date_str,
            'total_expected': total_p,
            'manifest': bookings_manifest,
            'is_reported': rep is not None,
            'report_data': dict(rep) if rep else None,
            'eligible_for_report': is_past and (rep is None) and (total_p > 0)
        })
        
    conn.close()
    return metrics

def submit_tour_attendance_report(tour_id, date_string, head_count, image_filename):
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO tour_reports (tour_id, tour_date, actual_count, report_image) VALUES (?, ?, ?, ?)",
            (tour_id, date_string, int(head_count), image_filename)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()