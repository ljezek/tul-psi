-- Production seed data for the Student Projects Catalogue.
--
-- Only creates the initial administrator user.  All other users, courses,
-- and projects are created via the application interface by this admin.
--
-- Run via: python seed.py

INSERT INTO "user" (email, github_alias, name, role, created_at)
VALUES
    ('lukas.jezek@tul.cz', 'ljezek', 'Lukáš Ježek', 'ADMIN', NOW())
ON CONFLICT (email) DO NOTHING;
