// Typed constants mirroring seed_dev.sql exactly.
// Tests import from here — never hardcode IDs or emails in spec files.

export const OTP = '000000';

export const USERS = {
  admin:    { id: 1,  email: 'psi.admin@tul.cz',           name: 'PSI Admin',         role: 'ADMIN'    },
  jezek:    { id: 2,  email: 'lukas.jezek@tul.cz',          name: 'Lukáš Ježek',       role: 'LECTURER' },
  spanek:   { id: 3,  email: 'roman.spanek@tul.cz',         name: 'Roman Špánek',      role: 'LECTURER' },
  kral:     { id: 4,  email: 'tomas.kral@tul.cz',           name: 'Tomáš Král',        role: 'LECTURER' },
  alice:    { id: 5,  email: 'alice.novakova@tul.cz',       name: 'Alice Nováková',    role: 'STUDENT'  },
  bob:      { id: 6,  email: 'bob.krcek@tul.cz',            name: 'Bob Krček',         role: 'STUDENT'  },
  jan:      { id: 11, email: 'jan.novak@tul.cz',            name: 'Jan Novák',         role: 'STUDENT'  },
  jana:     { id: 12, email: 'jana.svobodova@tul.cz',       name: 'Jana Svobodová',    role: 'STUDENT'  },
  dan_k:    { id: 25, email: 'dan.kerslager@tul.cz',        name: 'Dan Keršláger',     role: 'STUDENT'  },
} as const;

export const COURSES = {
  psi: { id: 1, code: 'PSI', name: 'Pokročilé Softwarové Inženýrství' },
  ald: { id: 2, code: 'ALD', name: 'Algoritmizace a datové struktury' },
} as const;

export const PROJECTS = {
  // PSI-2025 completed (results_unlocked = true)
  eventPlanner:  { id: 1,  title: 'TUL Event Planner',                  unlocked: true,  courseId: 1 },
  studijniAss:   { id: 2,  title: 'Studijní Asistent',                  unlocked: true,  courseId: 1 },
  budgetTracker: { id: 3,  title: 'Budget Tracker',                     unlocked: true,  courseId: 1 },
  // PSI-2026 in-progress
  lectorsSpc:    { id: 4,  title: 'Lectors - Student Projects Catalogue', unlocked: false, courseId: 1 },
  bookstore:     { id: 5,  title: 'Bookstore',                           unlocked: false, courseId: 1 },
  lolTracker:    { id: 6,  title: 'LOL tracker',                         unlocked: false, courseId: 1 },
  kanban:        { id: 7,  title: 'PSI - Kanban Board',                  unlocked: false, courseId: 1 },
  quizApp:       { id: 8,  title: 'QuizApp',                             unlocked: false, courseId: 1 },
} as const;

// course_evaluation id=10: jan.novak on project 4, submitted=false
export const COURSE_EVALS = {
  janDraft: { id: 10, projectId: PROJECTS.lectorsSpc.id, studentId: USERS.jan.id, submitted: false },
} as const;
