export enum UserRole {
  ADMIN = "ADMIN",
  LECTURER = "LECTURER",
  STUDENT = "STUDENT"
}

export enum CourseTerm {
  SUMMER = "SUMMER",
  WINTER = "WINTER"
}

export enum ProjectType {
  TEAM = "TEAM",
  INDIVIDUAL = "INDIVIDUAL"
}

export interface UserPublic {
  id: number;
  email: string;
  github_alias: string | null;
  name: string;
  role: UserRole;
  is_active: boolean;
}

export interface LecturerPublic {
  name: string;
  github_alias: string | null;
  email: string | null;
}

export interface MemberPublic {
  id: number;
  github_alias: string | null;
  name: string;
  email: string | null;
}

export interface EvaluationCriterion {
  code: string;
  description: string;
  max_score: number;
}

export interface CourseLink {
  label: string;
  url: string;
}

export interface CoursePublic {
  code: string;
  name: string;
  syllabus: string | null;
  term: CourseTerm;
  project_type: ProjectType;
  min_score: number;
  peer_bonus_budget: number | null;
  evaluation_criteria: EvaluationCriterion[];
  links: CourseLink[];
  lecturers: LecturerPublic[];
}

export interface EvaluationScoreDetail {
  criterion_code: string;
  score: number;
  strengths: string;
  improvements: string;
}

export interface ProjectEvaluationDetail {
  lecturer_id: number;
  scores: EvaluationScoreDetail[];
  updated_at: string;
  submitted: boolean;
}

export interface CourseEvaluationDetail {
  id: number;
  student_id: number;
  rating: number;
  strengths: string | null;
  improvements: string | null;
  submitted: boolean;
  updated_at: string;
}

export interface PeerFeedbackDetail {
  course_evaluation_id: number;
  receiving_student_id: number;
  strengths: string | null;
  improvements: string | null;
  bonus_points: number;
}

export interface ProjectPublic {
  id: number;
  title: string;
  description: string | null;
  github_url: string | null;
  live_url: string | null;
  technologies: string[];
  academic_year: number;
  course: CoursePublic;
  members: MemberPublic[];
  results_unlocked: boolean | null;
  project_evaluations: ProjectEvaluationDetail[] | null;
  course_evaluations: CourseEvaluationDetail[] | null;
  received_peer_feedback: PeerFeedbackDetail[] | null;
  authored_peer_feedback: PeerFeedbackDetail[] | null;
}

export interface CourseStats {
  project_count: number;
  academic_years: number[];
}

export interface CourseListItem {
  id: number;
  code: string;
  name: string;
  syllabus: string | null;
  lecturer_names: string[];
  stats: CourseStats;
}

export interface CourseDetail extends CoursePublic {
  id: number;
  course_evaluations?: CourseEvaluationDetail[] | null;
}

export interface ProjectEvaluationCreate {
  scores: {
    criterion_code: string;
    score: number;
    strengths: string;
    improvements: string;
  }[];
  submitted: boolean;
}

export interface ProjectCreate {
  title: string;
  description?: string | null;
  github_url?: string | null;
  live_url?: string | null;
  technologies?: string[];
  academic_year: number;
  owner_email?: string | null;
}

export interface ProjectUpdate {
  title?: string | null;
  description?: string | null;
  github_url?: string | null;
  live_url?: string | null;
  technologies?: string[] | null;
}

export interface AddMemberBody {
  email: string;
  name?: string | null;
  github_alias?: string | null;
}

export interface CourseEvaluationSubmit {
  submitted: boolean;
  rating: number;
  strengths: string;
  improvements: string;
  peer_evaluations: {
    receiving_student_id: number;
    strengths: string;
    improvements: string;
    bonus_points: number;
  }[];
}
