export type Role = 'host' | 'student' | 'lektor';

export interface Subject {
  id: string;
  code: string;
  name: string;
}

export interface Student {
  id: string;
  name: string;
  email: string;
}

export interface Project {
  id: string;
  title: string;
  description: string;
  fullDescription: string;
  academicYear: string; // e.g., "2023/2024"
  subjectId: string;
  tags: string[];
  authorIds: string[]; // IDs of students
  githubUrl?: string;
  liveUrl?: string;
  imageUrl?: string;
}

export interface Feedback {
  id: string;
  projectId: string;
  fromStudentId: string;
  toStudentId: string;
  strengths: string;
  improvements: string;
  createdAt: string;
}

export interface AppState {
  currentRole: Role;
  currentUser: Student | null; // Null for host/lektor for simplicity in this demo, or mock object
}