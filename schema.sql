PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS tour_reports;
DROP TABLE IF EXISTS additional_participants;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS tour_stops;
DROP TABLE IF EXISTS tour_images;
DROP TABLE IF EXISTS tour_schedules;
DROP TABLE IF EXISTS tours;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('guide', 'participant')),
    languages TEXT -- Comma-separated strings for guides (e.g., "Italian,English")
);

CREATE TABLE tours (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guide_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    meeting_point TEXT NOT NULL,
    duration INTEGER NOT NULL, -- Stored explicitly in minutes
    language TEXT NOT NULL CHECK(language IN ('Italian', 'English', 'Spanish', 'Portuguese', 'German')),
    max_participants INTEGER NOT NULL,
    description TEXT NOT NULL,
    FOREIGN KEY (guide_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE tour_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time TEXT NOT NULL, -- Format: HH:MM
    UNIQUE(tour_id, day_of_week), -- Constraint: max one start time per day per tour
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

CREATE TABLE tour_stops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    stop_name TEXT NOT NULL,
    stop_order INTEGER NOT NULL,
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

CREATE TABLE tour_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

CREATE TABLE profile_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL,
    tour_id INTEGER NOT NULL,
    tour_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    booking_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

CREATE TABLE additional_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reservation_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    FOREIGN KEY (reservation_id) REFERENCES reservations(id) ON DELETE CASCADE
);

CREATE TABLE tour_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id INTEGER NOT NULL,
    tour_date TEXT NOT NULL,
    actual_count INTEGER NOT NULL,
    report_image TEXT NOT NULL,
    UNIQUE(tour_id, tour_date),
    FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);