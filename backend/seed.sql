-- Development seed data for the Student Projects Catalogue.
--
-- Organized in foreign-key dependency order so that every referenced table
-- already has its rows when the referencing INSERT runs.
--
-- All INSERTs are idempotent: ON CONFLICT … DO NOTHING means re-running the
-- script never duplicates rows.  Surrogate-PK tables use OVERRIDING SYSTEM
-- VALUE to fix IDs, which is safe because the sequences are reset at the end.
--
-- Edge cases covered:
--   * Invited student who has not yet accepted (joined_at IS NULL).
--   * Stub project: no description, no technologies, no GitHub URL.
--   * results_unlocked = TRUE (completed) vs FALSE (in-progress).
--   * Published vs draft CourseEvaluation (published = FALSE).
--   * Team projects with peer feedback and bonus points.
--   * Individual projects without peer feedback.
--   * Course with peer_bonus_budget vs NULL.
--   * Multiple lecturers assigned to a single course.
--
-- Run via: python seed.py [--reset]

-- ============================================================================
-- user
-- ============================================================================
-- 1 admin, 3 lecturers, 6 synthetic past-year students, 15 current students.

INSERT INTO "user" (id, email, github_alias, name, role, created_at)
OVERRIDING SYSTEM VALUE
VALUES
    -- Admin
    (1,  'psi.admin@tul.cz',          'psi-admin',          'PSI Admin',           'ADMIN',    '2025-09-01 10:00:00+00'),
    -- Lecturers
    (2,  'lukas.jezek@tul.cz',         'ljezek',             'Lukáš Ježek',         'LECTURER', '2025-09-01 10:00:00+00'),
    (3,  'roman.spanek@tul.cz',        'roman-spanek',       'Roman Špánek',        'LECTURER', '2025-09-01 10:00:00+00'),
    (4,  'tomas.kral@tul.cz',          'tomaskral',          'Tomáš Král',          'LECTURER', '2025-09-01 10:00:00+00'),
    -- Past students (PSI-2025 and KDP-2025)
    (5,  'alice.novakova@tul.cz',      'alicenov',           'Alice Nováková',      'STUDENT',  '2025-09-15 09:00:00+00'),
    (6,  'bob.krcek@tul.cz',           'bobkrcek',           'Bob Krček',           'STUDENT',  '2025-09-15 09:00:00+00'),
    (7,  'carol.blazkova@tul.cz',      'carolblaz',          'Carol Blažková',      'STUDENT',  '2025-09-15 09:00:00+00'),
    (8,  'dan.horak@tul.cz',           'danhorak',           'Dan Horák',           'STUDENT',  '2025-09-15 09:00:00+00'),
    (9,  'eva.markova@tul.cz',         'evamark',            'Eva Marková',         'STUDENT',  '2025-09-15 09:00:00+00'),
    (10, 'filip.zak@tul.cz',           'filipzak',           'Filip Žák',           'STUDENT',  '2025-09-15 09:00:00+00'),
    -- Current students (PSI-2026, sourced from data/projects.json)
    (11, 'jan.novak@tul.cz',           'jannovak',           'Jan Novák',           'STUDENT',  '2026-02-01 09:00:00+00'),
    (12, 'jana.svobodova@tul.cz',      'janasvo',            'Jana Svobodová',      'STUDENT',  '2026-02-01 09:00:00+00'),
    (13, 'jiri.seps@tul.cz',           'JiriSeps',           'Jiří Šeps',           'STUDENT',  '2026-02-01 09:00:00+00'),
    (14, 'matej.hauschwitz@tul.cz',    'matejhauschwitz',    'Matěj Hauschwitz',    'STUDENT',  '2026-02-01 09:00:00+00'),
    (15, 'vojtech.gero@tul.cz',        'VojtechGero',        'Vojtěch Gerö',        'STUDENT',  '2026-02-01 09:00:00+00'),
    (16, 'martin.cizek@tul.cz',        'cizek-maritn',       'Martin Čížek',        'STUDENT',  '2026-02-01 09:00:00+00'),
    (17, 'jiri.ruta@tul.cz',           'rutaji',             'Jiří Růta',           'STUDENT',  '2026-02-01 09:00:00+00'),
    (18, 'ondrej.braunsveig@tul.cz',   'OndrejBraunsveig',   'Ondřej Braunšveig',   'STUDENT',  '2026-02-01 09:00:00+00'),
    (19, 'david.salek@tul.cz',         'ddeejjvviidd',       'David Šálek',         'STUDENT',  '2026-02-01 09:00:00+00'),
    (20, 'lilian.luca@tul.cz',         'lilianlucatul',      'Lilian Luca',         'STUDENT',  '2026-02-01 09:00:00+00'),
    (21, 'martin.renner@tul.cz',       'martinrenner',       'Martin Renner',       'STUDENT',  '2026-02-01 09:00:00+00'),
    (22, 'zakhar.fedorov@tul.cz',      'zakharfedorov',      'Zakhar Fedorov',      'STUDENT',  '2026-02-01 09:00:00+00'),
    (23, 'vlastimil.palfi@tul.cz',     'PalfiVlastimil',     'Vlastimil Pálfi',     'STUDENT',  '2026-02-01 09:00:00+00'),
    (24, 'jan.reisiegel@tul.cz',       'JanReisiegel',       'Jan Reisiegel',       'STUDENT',  '2026-02-01 09:00:00+00'),
    (25, 'dan.kerslager@tul.cz',       'DanKerslager',       'Dan Keršláger',       'STUDENT',  '2026-02-01 09:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- course
-- ============================================================================
-- PSI-2025: completed team course with peer bonus.
-- PSI-2026: in-progress team course with peer bonus (current year).
-- KDP-2025: completed individual course, no peer bonus.

INSERT INTO course (id, code, name, syllabus, term, project_type, min_score,
                    peer_bonus_budget, evaluation_criteria, links,
                    created_by, created_at)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'PSI', 'Pokročilé Softwarové Inženýrství',
        'Studenti v týmech navrhnou a implementují netriviální softwarový projekt. Důraz je kladen na architekturu, testování a dokumentaci.',
        'WINTER', 'TEAM', 50, 10,
        '[{"code":"architecture","description":"Architektura a návrh systému","max_score":20},{"code":"code_quality","description":"Kvalita kódu a dodržení konvencí","max_score":20},{"code":"testing","description":"Testování a pokrytí kódu","max_score":20},{"code":"documentation","description":"Dokumentace a README","max_score":20},{"code":"presentation","description":"Prezentace a demo","max_score":20}]'::jsonb,
        '[{"label":"Moodle","url":"https://moodle.tul.cz/course/view.php?id=12344"},{"label":"GitHub Organisation","url":"https://github.com/PSI-RDB-2025"}]'::jsonb,
        1, '2025-09-01 12:00:00+00'),
    (2, 'KDP', 'Klauzurní projekt',
        'Individuální softwarový nebo výzkumný projekt obhajovaný u státní závěrečné zkoušky.',
        'SUMMER', 'INDIVIDUAL', 60, NULL,
        '[{"code":"analysis","description":"Analýza a specifikace požadavků","max_score":30},{"code":"implementation","description":"Implementace a funkčnost","max_score":40},{"code":"report","description":"Technická zpráva","max_score":30}]'::jsonb,
        '[]'::jsonb,
        1, '2025-02-01 12:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- course_lecturer
-- ============================================================================
-- PSI-2025: Jan Novák (2) + Petra Svobodová (3).
-- PSI-2026: Jan Novák (2) + Tomáš Král (4).
-- KDP-2025: Petra Svobodová (3).

INSERT INTO course_lecturer (course_id, user_id, assigned_at)
VALUES
    (1, 3, '2025-09-01 12:30:00+00'),
    (1, 2, '2025-09-01 12:30:00+00'),
    (2, 4, '2025-02-01 12:30:00+00')
ON CONFLICT (course_id, user_id) DO NOTHING;

-- ============================================================================
-- project
-- ============================================================================
-- PSI-2025 (ids 1–3): fully completed, results_unlocked = TRUE.
-- PSI-2026 (ids 4–8): in-progress, results_unlocked = FALSE.
--   id 4 — fully populated (description, GitHub, live_url, technologies set).
--   id 5 — partial: GitHub set but no description or technologies yet.
--   id 6 — stub:    only title seeded; owner has not linked a repo yet.
--   id 7, 8 — normal in-progress: description and GitHub set, no live_url.
-- KDP-2025 (ids 9–10): fully completed, results_unlocked = TRUE.

INSERT INTO project (id, title, description, github_url, live_url, technologies,
                     results_unlocked, course_id, academic_year, created_at)
OVERRIDING SYSTEM VALUE
VALUES
    -- PSI-2025 completed projects
    (1,  'TUL Event Planner',
         'Webová aplikace pro správu a přihlašování na fakultní akce a workshopy.',
         'https://github.com/PSI-2025/event-planner',
         'https://event-planner.tul.cz',
         '["Python","FastAPI","React","PostgreSQL"]'::jsonb,
         true, 1, 2025, '2025-09-20 10:00:00+00'),
    (2,  'Studijní Asistent',
         'Chatbot integrovaný s Moodle pro zodpovídání dotazů ke studijním materiálům.',
         'https://github.com/PSI-2025/studijni-asistent',
         NULL,
         '["Python","LangChain","Vue.js"]'::jsonb,
         true, 1, 2025, '2025-09-20 10:00:00+00'),
    (3,  'Budget Tracker',
         'Mobilní aplikace pro sledování osobních výdajů s exportem do CSV.',
         'https://github.com/PSI-2025/budget-tracker',
         'https://budget.tul.cz',
         '["Flutter","Dart","Firebase"]'::jsonb,
         true, 1, 2025, '2025-09-20 10:00:00+00'),
    -- PSI-2026 in-progress projects (sourced from data/projects.json)
    (4,  'Lectors - Student Projects Catalogue',
         'Plná implementace Student Projects Catalogue — React SPA + FastAPI backend + PostgreSQL.',
         'https://github.com/ljezek/tul-psi',
         'https://psi.tul.cz',
         '["React","TypeScript","FastAPI","Python","PostgreSQL","Docker"]'::jsonb,
         false, 1, 2026, '2026-02-15 10:00:00+00'),
    (5,  'Bookstore',
         NULL,
         'https://github.com/matejhauschwitz/PSI',
         NULL,
         '[]'::jsonb,
         false, 1, 2026, '2026-02-15 10:00:00+00'),
    (6,  'LOL tracker',
         NULL,
         NULL,
         NULL,
         '[]'::jsonb,
         false, 1, 2026, '2026-02-15 10:00:00+00'),
    (7,  'PSI - Kanban Board',
         'Webová aplikace: PSI - Kanban Board.',
         'https://github.com/martinrenner/PSI',
         NULL,
         '["Python","React"]'::jsonb,
         false, 1, 2026, '2026-02-15 10:00:00+00'),
    (8,  'QuizApp',
         'Webová aplikace: QuizApp.',
         'https://github.com/PSI-RDB-2026/QuizApp',
         NULL,
         '["Python","React"]'::jsonb,
         false, 1, 2026, '2026-02-15 10:00:00+00'),
    -- KDP-2025 completed individual projects
    (9,  'Analýza výkonnosti distribuovaných systémů',
         'Srovnání latence a propustnosti různých message-broker architektur.',
         'https://github.com/alicenov/kdp-2025',
         NULL,
         '["Python","RabbitMQ","Kafka"]'::jsonb,
         true, 2, 2025, '2025-02-15 10:00:00+00'),
    (10, 'Detekce anomálií v IoT datech pomocí ML',
         'Klasifikace chybových stavů senzorů pomocí izolačního lesa.',
         'https://github.com/danhorak/kdp-2025',
         NULL,
         '["Python","scikit-learn","MQTT"]'::jsonb,
         true, 2, 2025, '2025-02-15 10:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- project_member
-- ============================================================================
-- invited_by = NULL means the student was seeded directly as the project owner.
-- joined_at  = NULL means the invitation has not been accepted yet (edge case).

INSERT INTO project_member (id, project_id, user_id, invited_by, invited_at, joined_at)
OVERRIDING SYSTEM VALUE
VALUES
    -- PSI-2025 project 1 (TUL Event Planner): Alice (owner) + Bob
    (1,  1,  5,  NULL, '2025-09-20 10:00:00+00', '2025-09-20 10:00:00+00'),
    (2,  1,  6,  5,    '2025-09-20 10:05:00+00', '2025-09-20 10:10:00+00'),
    -- PSI-2025 project 2 (Studijní Asistent): Carol (owner) + Dan + Eva
    (3,  2,  7,  NULL, '2025-09-20 10:00:00+00', '2025-09-20 10:00:00+00'),
    (4,  2,  8,  7,    '2025-09-20 10:05:00+00', '2025-09-20 10:10:00+00'),
    (5,  2,  9,  7,    '2025-09-20 10:05:00+00', '2025-09-20 10:10:00+00'),
    -- PSI-2025 project 3 (Budget Tracker): Filip (owner) + Bob
    (6,  3,  10, NULL, '2025-09-20 10:00:00+00', '2025-09-20 10:00:00+00'),
    (7,  3,  6,  10,   '2025-09-20 10:05:00+00', '2025-09-20 10:10:00+00'),
    -- PSI-2026 project 4 (Lectors SPC): Lukáš (owner) + Roman
    (8,  4,  11, NULL, '2026-02-15 10:00:00+00', '2026-02-15 10:00:00+00'),
    (9,  4,  12, 11,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    -- PSI-2026 project 5 (Bookstore): Jiří Šeps (owner) + Matěj + Vojtěch
    (10, 5,  13, NULL, '2026-02-15 10:00:00+00', '2026-02-15 10:00:00+00'),
    (11, 5,  14, 13,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    (12, 5,  15, 13,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    -- PSI-2026 project 6 (LOL tracker — stub): Martin Čížek (owner) + Jiří Růta (invited, NOT joined) + Ondřej
    (13, 6,  16, NULL, '2026-02-15 10:00:00+00', '2026-02-15 10:00:00+00'),
    (14, 6,  17, 16,   '2026-02-15 10:05:00+00', NULL),
    (15, 6,  18, 16,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    -- PSI-2026 project 7 (PSI Kanban Board): David (owner) + Lilian + Martin Renner + Zakhar
    (16, 7,  19, NULL, '2026-02-15 10:00:00+00', '2026-02-15 10:00:00+00'),
    (17, 7,  20, 19,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    (18, 7,  21, 19,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    (19, 7,  22, 19,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    -- PSI-2026 project 8 (QuizApp): Vlastimil (owner) + Jan Reisiegel + Dan Keršláger
    (20, 8,  23, NULL, '2026-02-15 10:00:00+00', '2026-02-15 10:00:00+00'),
    (21, 8,  24, 23,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    (22, 8,  25, 23,   '2026-02-15 10:05:00+00', '2026-02-15 10:10:00+00'),
    -- KDP-2025 project 9 (Analýza výkonnosti): Alice
    (23, 9,  5,  NULL, '2025-02-15 10:00:00+00', '2025-02-15 10:00:00+00'),
    -- KDP-2025 project 10 (Detekce anomálií): Dan
    (24, 10, 8,  NULL, '2025-02-15 10:00:00+00', '2025-02-15 10:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- project_evaluation
-- ============================================================================
-- PSI-2025: both lecturers (Jan Novák id=2, Petra Svobodová id=3) evaluate
--           all three projects.  Novák awards 16/20 per criterion; Svobodová
--           awards 18/20 per criterion.
-- KDP-2025: Petra Svobodová evaluates both projects, awarding 25 per criterion.

INSERT INTO project_evaluation (project_id, lecturer_id, scores, submitted_at)
VALUES
    -- Project 1 — Jan Novák (score 16/20 per criterion)
    (1, 2, '[{"criterion_code":"architecture","score":16,"strengths":"Výborná práce v oblasti Architektura a návrh systému.","improvements":"Doporučuji věnovat více pozornosti detailům v Architektura a návrh systému."},{"criterion_code":"code_quality","score":16,"strengths":"Výborná práce v oblasti Kvalita kódu a dodržení konvencí.","improvements":"Doporučuji věnovat více pozornosti detailům v Kvalita kódu a dodržení konvencí."},{"criterion_code":"testing","score":16,"strengths":"Výborná práce v oblasti Testování a pokrytí kódu.","improvements":"Doporučuji věnovat více pozornosti detailům v Testování a pokrytí kódu."},{"criterion_code":"documentation","score":16,"strengths":"Výborná práce v oblasti Dokumentace a README.","improvements":"Doporučuji věnovat více pozornosti detailům v Dokumentace a README."},{"criterion_code":"presentation","score":16,"strengths":"Výborná práce v oblasti Prezentace a demo.","improvements":"Doporučuji věnovat více pozornosti detailům v Prezentace a demo."}]'::jsonb,
     '2026-01-15 10:00:00+00'),
    -- Project 1 — Petra Svobodová (score 18/20 per criterion)
    (1, 3, '[{"criterion_code":"architecture","score":18,"strengths":"Výborná práce v oblasti Architektura a návrh systému.","improvements":"Doporučuji věnovat více pozornosti detailům v Architektura a návrh systému."},{"criterion_code":"code_quality","score":18,"strengths":"Výborná práce v oblasti Kvalita kódu a dodržení konvencí.","improvements":"Doporučuji věnovat více pozornosti detailům v Kvalita kódu a dodržení konvencí."},{"criterion_code":"testing","score":18,"strengths":"Výborná práce v oblasti Testování a pokrytí kódu.","improvements":"Doporučuji věnovat více pozornosti detailům v Testování a pokrytí kódu."},{"criterion_code":"documentation","score":18,"strengths":"Výborná práce v oblasti Dokumentace a README.","improvements":"Doporučuji věnovat více pozornosti detailům v Dokumentace a README."},{"criterion_code":"presentation","score":18,"strengths":"Výborná práce v oblasti Prezentace a demo.","improvements":"Doporučuji věnovat více pozornosti detailům v Prezentace a demo."}]'::jsonb,
     '2026-01-15 10:00:00+00'),
    -- Project 2 — Jan Novák
    (2, 2, '[{"criterion_code":"architecture","score":16,"strengths":"Výborná práce v oblasti Architektura a návrh systému.","improvements":"Doporučuji věnovat více pozornosti detailům v Architektura a návrh systému."},{"criterion_code":"code_quality","score":16,"strengths":"Výborná práce v oblasti Kvalita kódu a dodržení konvencí.","improvements":"Doporučuji věnovat více pozornosti detailům v Kvalita kódu a dodržení konvencí."},{"criterion_code":"testing","score":16,"strengths":"Výborná práce v oblasti Testování a pokrytí kódu.","improvements":"Doporučuji věnovat více pozornosti detailům v Testování a pokrytí kódu."},{"criterion_code":"documentation","score":16,"strengths":"Výborná práce v oblasti Dokumentace a README.","improvements":"Doporučuji věnovat více pozornosti detailům v Dokumentace a README."},{"criterion_code":"presentation","score":16,"strengths":"Výborná práce v oblasti Prezentace a demo.","improvements":"Doporučuji věnovat více pozornosti detailům v Prezentace a demo."}]'::jsonb,
     '2026-01-15 10:00:00+00'),
    -- Project 2 — Petra Svobodová
    (2, 3, '[{"criterion_code":"architecture","score":18,"strengths":"Výborná práce v oblasti Architektura a návrh systému.","improvements":"Doporučuji věnovat více pozornosti detailům v Architektura a návrh systému."},{"criterion_code":"code_quality","score":18,"strengths":"Výborná práce v oblasti Kvalita kódu a dodržení konvencí.","improvements":"Doporučuji věnovat více pozornosti detailům v Kvalita kódu a dodržení konvencí."},{"criterion_code":"testing","score":18,"strengths":"Výborná práce v oblasti Testování a pokrytí kódu.","improvements":"Doporučuji věnovat více pozornosti detailům v Testování a pokrytí kódu."},{"criterion_code":"documentation","score":18,"strengths":"Výborná práce v oblasti Dokumentace a README.","improvements":"Doporučuji věnovat více pozornosti detailům v Dokumentace a README."},{"criterion_code":"presentation","score":18,"strengths":"Výborná práce v oblasti Prezentace a demo.","improvements":"Doporučuji věnovat více pozornosti detailům v Prezentace a demo."}]'::jsonb,
     '2026-01-15 10:00:00+00'),
    -- Project 3 — Jan Novák
    (3, 2, '[{"criterion_code":"architecture","score":16,"strengths":"Výborná práce v oblasti Architektura a návrh systému.","improvements":"Doporučuji věnovat více pozornosti detailům v Architektura a návrh systému."},{"criterion_code":"code_quality","score":16,"strengths":"Výborná práce v oblasti Kvalita kódu a dodržení konvencí.","improvements":"Doporučuji věnovat více pozornosti detailům v Kvalita kódu a dodržení konvencí."},{"criterion_code":"testing","score":16,"strengths":"Výborná práce v oblasti Testování a pokrytí kódu.","improvements":"Doporučuji věnovat více pozornosti detailům v Testování a pokrytí kódu."},{"criterion_code":"documentation","score":16,"strengths":"Výborná práce v oblasti Dokumentace a README.","improvements":"Doporučuji věnovat více pozornosti detailům v Dokumentace a README."},{"criterion_code":"presentation","score":16,"strengths":"Výborná práce v oblasti Prezentace a demo.","improvements":"Doporučuji věnovat více pozornosti detailům v Prezentace a demo."}]'::jsonb,
     '2026-01-15 10:00:00+00'),
    -- Project 3 — Petra Svobodová
    (3, 3, '[{"criterion_code":"architecture","score":18,"strengths":"Výborná práce v oblasti Architektura a návrh systému.","improvements":"Doporučuji věnovat více pozornosti detailům v Architektura a návrh systému."},{"criterion_code":"code_quality","score":18,"strengths":"Výborná práce v oblasti Kvalita kódu a dodržení konvencí.","improvements":"Doporučuji věnovat více pozornosti detailům v Kvalita kódu a dodržení konvencí."},{"criterion_code":"testing","score":18,"strengths":"Výborná práce v oblasti Testování a pokrytí kódu.","improvements":"Doporučuji věnovat více pozornosti detailům v Testování a pokrytí kódu."},{"criterion_code":"documentation","score":18,"strengths":"Výborná práce v oblasti Dokumentace a README.","improvements":"Doporučuji věnovat více pozornosti detailům v Dokumentace a README."},{"criterion_code":"presentation","score":18,"strengths":"Výborná práce v oblasti Prezentace a demo.","improvements":"Doporučuji věnovat více pozornosti detailům v Prezentace a demo."}]'::jsonb,
     '2026-01-15 10:00:00+00'),
    -- KDP project 9 — Petra Svobodová (score 25 per criterion)
    (9,  3, '[{"criterion_code":"analysis","score":25,"strengths":"Výborná práce v oblasti Analýza a specifikace požadavků.","improvements":"Doporučuji věnovat více pozornosti detailům v Analýza a specifikace požadavků."},{"criterion_code":"implementation","score":25,"strengths":"Výborná práce v oblasti Implementace a funkčnost.","improvements":"Doporučuji věnovat více pozornosti detailům v Implementace a funkčnost."},{"criterion_code":"report","score":25,"strengths":"Výborná práce v oblasti Technická zpráva.","improvements":"Doporučuji věnovat více pozornosti detailům v Technická zpráva."}]'::jsonb,
     '2026-01-10 10:00:00+00'),
    -- KDP project 10 — Petra Svobodová
    (10, 3, '[{"criterion_code":"analysis","score":25,"strengths":"Výborná práce v oblasti Analýza a specifikace požadavků.","improvements":"Doporučuji věnovat více pozornosti detailům v Analýza a specifikace požadavků."},{"criterion_code":"implementation","score":25,"strengths":"Výborná práce v oblasti Implementace a funkčnost.","improvements":"Doporučuji věnovat více pozornosti detailům v Implementace a funkčnost."},{"criterion_code":"report","score":25,"strengths":"Výborná práce v oblasti Technická zpráva.","improvements":"Doporučuji věnovat více pozornosti detailům v Technická zpráva."}]'::jsonb,
     '2026-01-10 10:00:00+00')
ON CONFLICT (project_id, lecturer_id) DO NOTHING;

-- ============================================================================
-- course_evaluation
-- ============================================================================
-- PSI-2025 (ids 1–7): all published, rating = 4.
-- KDP-2025 (ids 8–9): all published, rating = 5.
-- PSI-2026 (id 10):   draft (published = FALSE, strengths/improvements NULL).

INSERT INTO course_evaluation (id, project_id, student_id, rating,
                                strengths, improvements, published, submitted_at)
OVERRIDING SYSTEM VALUE
VALUES
    -- PSI-2025 project 1 (TUL Event Planner): Alice + Bob
    (1,  1,  5,  4, 'Kurz byl výborně organizován a přednášky byly srozumitelné.', 'Uvítal bych více praktických cvičení v první polovině semestru.', true,  '2026-01-20 10:00:00+00'),
    (2,  1,  6,  4, 'Kurz byl výborně organizován a přednášky byly srozumitelné.', 'Uvítal bych více praktických cvičení v první polovině semestru.', true,  '2026-01-20 10:00:00+00'),
    -- PSI-2025 project 2 (Studijní Asistent): Carol + Dan + Eva
    (3,  2,  7,  4, 'Kurz byl výborně organizován a přednášky byly srozumitelné.', 'Uvítal bych více praktických cvičení v první polovině semestru.', true,  '2026-01-20 10:00:00+00'),
    (4,  2,  8,  4, 'Kurz byl výborně organizován a přednášky byly srozumitelné.', 'Uvítal bych více praktických cvičení v první polovině semestru.', true,  '2026-01-20 10:00:00+00'),
    (5,  2,  9,  4, 'Kurz byl výborně organizován a přednášky byly srozumitelné.', 'Uvítal bych více praktických cvičení v první polovině semestru.', true,  '2026-01-20 10:00:00+00'),
    -- PSI-2025 project 3 (Budget Tracker): Filip + Bob
    (6,  3,  10, 4, 'Kurz byl výborně organizován a přednášky byly srozumitelné.', 'Uvítal bych více praktických cvičení v první polovině semestru.', true,  '2026-01-20 10:00:00+00'),
    (7,  3,  6,  4, 'Kurz byl výborně organizován a přednášky byly srozumitelné.', 'Uvítal bych více praktických cvičení v první polovině semestru.', true,  '2026-01-20 10:00:00+00'),
    -- KDP-2025 project 9 (Analýza výkonnosti): Alice
    (8,  9,  5,  5, 'Práce na projektu mi dala skvělou přípravu na obhajobu.',       'Více konzultačních termínů by pomohlo v průběhu zpracování.',       true,  '2026-01-20 10:00:00+00'),
    -- KDP-2025 project 10 (Detekce anomálií): Dan
    (9,  10, 8,  5, 'Práce na projektu mi dala skvělou přípravu na obhajobu.',       'Více konzultačních termínů by pomohlo v průběhu zpracování.',       true,  '2026-01-20 10:00:00+00'),
    -- PSI-2026 project 4 (Lectors SPC): Lukáš — draft, free-text not yet filled in
    (10, 4,  11, 4, NULL, NULL, false, '2026-03-01 09:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- peer_feedback
-- ============================================================================
-- Only PSI-2025 projects have peer feedback (peer_bonus_budget = 10).
-- Each team member distributes 10 points evenly across their teammates.
--   2-person team: each teammate receives 10 bonus points.
--   3-person team: each teammate receives 5 bonus points.

INSERT INTO peer_feedback (course_evaluation_id, receiving_student_id,
                            strengths, improvements, bonus_points)
VALUES
    -- CE 1 (Alice evaluates project 1): feedback for Bob (id 6)
    (1,  6,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.', 10),
    -- CE 2 (Bob evaluates project 1): feedback for Alice (id 5)
    (2,  5,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.', 10),
    -- CE 3 (Carol evaluates project 2): feedback for Dan (id 8) + Eva (id 9)
    (3,  8,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.',  5),
    (3,  9,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.',  5),
    -- CE 4 (Dan evaluates project 2): feedback for Carol (id 7) + Eva (id 9)
    (4,  7,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.',  5),
    (4,  9,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.',  5),
    -- CE 5 (Eva evaluates project 2): feedback for Carol (id 7) + Dan (id 8)
    (5,  7,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.',  5),
    (5,  8,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.',  5),
    -- CE 6 (Filip evaluates project 3): feedback for Bob (id 6)
    (6,  6,  'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.', 10),
    -- CE 7 (Bob evaluates project 3): feedback for Filip (id 10)
    (7,  10, 'Spolehlivý člen týmu, vždy včas plnil zadané úkoly.', 'Doporučuji aktivnější komunikaci při blokujících problémech.', 10)
ON CONFLICT (course_evaluation_id, receiving_student_id) DO NOTHING;