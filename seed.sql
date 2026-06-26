-- Passwords hash evaluated using generate_password_hash('password123', method='pbkdf2:sha256')
-- All default users share the password: password123
-- Sample Guides
INSERT INTO users (email, password_hash, first_name, last_name, role, languages) VALUES 
('marco.rossi@zenawalks.it', 'pbkdf2:sha256:1000000$2yS1HvWaMo22QuS1$28642d48f8feb86b729c3e8a994480edadf59f2cd767a5d8df69acd4a81a3152', 'Marco', 'Rossi', 'guide', 'Italian,English,Spanish'),
('elena.bianchi@zenawalks.it', 'pbkdf2:sha256:1000000$2yS1HvWaMo22QuS1$28642d48f8feb86b729c3e8a994480edadf59f2cd767a5d8df69acd4a81a3152', 'Elena', 'Bianchi', 'guide', 'English,German,Portuguese');

-- Sample Participants
INSERT INTO users (email, password_hash, first_name, last_name, role, languages) VALUES 
('john.doe@gmail.com', 'pbkdf2:sha256:1000000$2yS1HvWaMo22QuS1$28642d48f8feb86b729c3e8a994480edadf59f2cd767a5d8df69acd4a81a3152', 'John', 'Doe', 'participant', NULL),
('clara.schmidt@web.de', 'pbkdf2:sha256:1000000$2yS1HvWaMo22QuS1$28642d48f8feb86b729c3e8a994480edadf59f2cd767a5d8df69acd4a81a3152', 'Clara', 'Schmidt', 'participant', NULL),
('lucas.silva@uol.com.br', 'pbkdf2:sha256:1000000$2yS1HvWaMo22QuS1$28642d48f8feb86b729c3e8a994480edadf59f2cd767a5d8df69acd4a81a3152', 'Lucas', 'Silva', 'participant', NULL);

-- Sample Tours
INSERT INTO tours (guide_id, title, meeting_point, duration, language, max_participants, description) VALUES 
(1, 'Caruggi Secrets: Historical Center Exploration', 'Piazza De Ferrari (Near the central fountain)', 120, 'Italian', 15, 'Uncover the mysterious medieval alleyways of Genova, learning about the ancient maritime republic superpower status.'),
(1, 'Genoese Street Food Odyssey', 'Mercato Orientale (Main Entry Gate)', 90, 'English', 10, 'Taste authentic warm focaccia, fresh farinata, and authentic local historical snacks directly inside the bustling local markets.'),
(2, 'Rolli Palaces: Golden Age Architecture Walk', 'Piazza Caricamento', 150, 'English', 20, 'Walk past UNESCO heritage residential assets built by the elite rulers of the Renaissance era.');

-- Tour Schedules mapping
INSERT INTO tour_schedules (tour_id, day_of_week, start_time) VALUES 
(1, 'Saturday', '10:00'),
(1, 'Sunday', '15:30'),
(2, 'Friday', '12:00'),
(2, 'Saturday', '16:00'),
(3, 'Saturday', '14:00');

-- Tour Stops mapping (Minimum 4 tracking constraints verified)
INSERT INTO tour_stops (tour_id, stop_name, stop_order) VALUES 
(1, 'Piazza De Ferrari', 1), (1, 'Cattedrale di San Lorenzo', 2), (1, 'Palazzo Ducale', 3), (1, 'Porto Antico', 4),
(2, 'Mercato Orientale', 1), (2, 'Via San Vincenzo bakeries', 2), (2, 'Sottoripa historical fry shops', 3), (2, 'Piazza Erbe', 4),
(3, 'Piazza Caricamento', 1), (3, 'Via Garibaldi Lookouts', 2), (3, 'Palazzo Rosso Atrium', 3), (3, 'Palazzo Tursi Gardens', 4);

-- Standard placeholders mapped into db file system array
INSERT INTO tour_images (tour_id, file_path) VALUES 
(1, 'sample1.jpg'), (1, 'sample2.jpg'), (1, 'sample3.jpg'), (1, 'sample4.jpg'), (1, 'sample5.jpg'),
(2, 'sample1.jpg'), (2, 'sample2.jpg'), (2, 'sample3.jpg'), (2, 'sample4.jpg'), (2, 'sample5.jpg'),
(3, 'sample1.jpg'), (3, 'sample2.jpg'), (3, 'sample3.jpg'), (3, 'sample4.jpg'), (3, 'sample5.jpg');

-- Inject a reservation safely to showcase live evaluation functions
-- Saturday, June 27th, 2026 matches the Saturday routine for Tour #1
INSERT INTO reservations (participant_id, tour_id, tour_date) VALUES (1, 1, '2026-06-27');
INSERT INTO additional_participants (reservation_id, first_name, last_name) VALUES (1, 'Jane', 'Doe');