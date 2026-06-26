from dao.db import get_db_connection
from datetime import datetime

def get_filtered_tours(date_filter=None, duration_filter=None, language_filter=None):
    conn = get_db_connection()
    
    query = """
        SELECT t.*, u.first_name, u.last_name,
        (SELECT file_path FROM tour_images WHERE tour_id = t.id LIMIT 1) AS main_image
        FROM tours t
        JOIN users u ON t.guide_id = u.id
        WHERE 1=1
    """
    params = []

    if language_filter:
        query += " AND t.language = ?"
        params.append(language_filter)

    if duration_filter:
        try:
            max_duration = int(duration_filter)
            query += " AND t.duration <= ?"
            params.append(max_duration)
        except ValueError:
            pass

    rows = conn.execute(query, params).fetchall()
    results = [dict(row) for row in rows]

    # Post-filtering schedule alignments cleanly against exact calendar days
    if date_filter:
        try:
            parsed_date = datetime.strptime(date_filter, "%Y-%m-%d")
            day_name = parsed_date.strftime("%A") # e.g. "Saturday"
            
            filtered_results = []
            for tour in results:
                sched = conn.execute(
                    "SELECT 1 FROM tour_schedules WHERE tour_id = ? AND day_of_week = ?",
                    (tour['id'], day_name)
                ).fetchone()
                if sched:
                    filtered_results.append(tour)
            results = filtered_results
        except ValueError:
            pass

    conn.close()
    return results

def get_tour_complete_details(tour_id):
    conn = get_db_connection()
    tour = conn.execute("""
        SELECT t.*, u.first_name, u.last_name, u.email AS guide_email
        FROM tours t JOIN users u ON t.guide_id = u.id
        WHERE t.id = ?
    """, (tour_id,)).fetchone()
    
    if not tour:
        conn.close()
        return None

    tour_dict = dict(tour)
    tour_dict['schedules'] = [dict(r) for r in conn.execute("SELECT * FROM tour_schedules WHERE tour_id = ?", (tour_id,)).fetchall()]
    tour_dict['stops'] = [row['stop_name'] for row in conn.execute("SELECT * FROM tour_stops WHERE tour_id = ? ORDER BY stop_order ASC", (tour_id,)).fetchall()]
    tour_dict['images'] = [row['file_path'] for row in conn.execute("SELECT * FROM tour_images WHERE tour_id = ?", (tour_id,)).fetchall()]
    
    conn.close()
    return tour_dict

def has_tour_reservations(tour_id):
    conn = get_db_connection()
    res = conn.execute("SELECT COUNT(*) as cnt FROM reservations WHERE tour_id = ?", (tour_id,)).fetchone()
    conn.close()
    return res['cnt'] > 0

def create_tour(guide_id, title, meeting_point, duration, language, max_participants, description, schedule_data, stops, image_filenames):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tours (guide_id, title, meeting_point, duration, language, max_participants, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (guide_id, title, meeting_point, int(duration), language, int(max_participants), description)
        )
        tour_id = cursor.lastrowid

        # Insert schedules
        for day, time in schedule_data.items():
            if time:
                cursor.execute("INSERT INTO tour_schedules (tour_id, day_of_week, start_time) VALUES (?, ?, ?)", (tour_id, day, time))

        # Insert stops
        for idx, stop in enumerate(stops, start=1):
            if stop.strip():
                cursor.execute("INSERT INTO tour_stops (tour_id, stop_name, stop_order) VALUES (?, ?, ?)", (tour_id, stop.strip(), idx))

        # Insert promotional assets paths mapping
        for filename in image_filenames:
            cursor.execute("INSERT INTO tour_images (tour_id, file_path) VALUES (?, ?)", (tour_id, filename))

        conn.commit()
        return tour_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def update_tour_limited(tour_id, title, description, image_filenames=None):
    """
    Updates non-essential descriptive properties. Safely called even if reservations exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE tours SET title = ?, description = ? WHERE id = ?", (title, description, tour_id))
        if image_filenames:
            cursor.execute("DELETE FROM tour_images WHERE tour_id = ?", (tour_id,))
            for img in image_filenames:
                cursor.execute("INSERT INTO tour_images (tour_id, file_path) VALUES (?, ?)", (tour_id, img))
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def update_tour_full(tour_id, title, meeting_point, duration, language, max_participants, description, schedule_data, stops, image_filenames=None):
    """
    Performs full data alteration. Only executable if validation rules determine active registration tally = 0.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE tours SET title = ?, meeting_point = ?, duration = ?, language = ?, max_participants = ?, description = ? WHERE id = ?",
            (title, meeting_point, int(duration), language, int(max_participants), description, tour_id)
        )
        # Re-map schedules cleanly
        cursor.execute("DELETE FROM tour_schedules WHERE tour_id = ?", (tour_id,))
        for day, time in schedule_data.items():
            if time:
                cursor.execute("INSERT INTO tour_schedules (tour_id, day_of_week, start_time) VALUES (?, ?, ?)", (tour_id, day, time))

        # Re-map structural points
        cursor.execute("DELETE FROM tour_stops WHERE tour_id = ?", (tour_id,))
        for idx, stop in enumerate(stops, start=1):
            if stop.strip():
                cursor.execute("INSERT INTO tour_stops (tour_id, stop_name, stop_order) VALUES (?, ?, ?)", (tour_id, stop.strip(), idx))

        if image_filenames:
            cursor.execute("DELETE FROM tour_images WHERE tour_id = ?", (tour_id,))
            for img in image_filenames:
                cursor.execute("INSERT INTO tour_images (tour_id, file_path) VALUES (?, ?)", (tour_id, img))

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()

def get_tours_by_guide(guide_id):
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM tours WHERE guide_id = ?", (guide_id,)).fetchall()
    tours_list = [dict(r) for r in rows]
    conn.close()
    return tours_list