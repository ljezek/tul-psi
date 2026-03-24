// Shared TypeScript types used across the frontend

export type Language = 'cs' | 'en';

export type Role = 'host' | 'student' | 'lektor';

export interface Project {
  id: string;
  title: string;
  shortDescription: string;
  description: string;
  tags: string[];
  subjectCode: string;
  academicYear: string;
  studentIds: string[];
  repoUrl?: string;
  demoUrl?: string;
}

export interface Subject {
  code: string;
  name: string;
}

export interface Student {
  id: string;
  name: string;
  email: string;
}
