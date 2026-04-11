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

export interface UserCreate {
  email: string;
  name?: string | null;
  github_alias?: string | null;
  role: UserRole;
  is_active?: boolean;
}

export interface AdminUserUpdate {
  name?: string | null;
  github_alias?: string | null;
  role?: UserRole | null;
  is_active?: boolean | null;
}

export interface LecturerPublic {
  id: number;
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
  id: number;
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
  rating: number | null;
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
  submitted_lecturer_count: number | null;
  submitted_student_count: number | null;
  results_unlocked: boolean | null;
  project_evaluations: ProjectEvaluationDetail[] | null;
  course_evaluations: CourseEvaluationDetail[] | null;
  received_peer_feedback: PeerFeedbackDetail[] | null;
  authored_peer_feedback?: PeerFeedbackDetail[] | null;
  total_points?: number | null;
  }


export interface CriterionScoreSummary {
  criterion_code: string;
  score: number;
  strengths: string | null;
  improvements: string | null;
}

export interface ProjectEvaluationSummary {
  lecturer_id: number;
  criterion_scores: CriterionScoreSummary[];
}

export interface CourseEvaluationSummary {
  rating: number | null;
  strengths: string | null;
  improvements: string | null;
}

export interface ReceivedPeerFeedback {
  bonus_points: number;
  strengths: string | null;
  improvements: string | null;
}

export interface StudentBonusSummary {
  student_id: number;
  student_name: string;
  feedback: ReceivedPeerFeedback[];
}

export interface ProjectOverviewItem {
  project_id: number;
  project_title: string;
  academic_year: number;
  project_evaluations: ProjectEvaluationSummary[];
  course_evaluations: CourseEvaluationSummary[];
  student_bonus_points: StudentBonusSummary[];
}

export interface EvaluationOverviewResponse {
  projects: ProjectOverviewItem[];
}

export interface CourseStats {
  project_count: number;
  academic_years: number[];
  pending_evaluations_count?: number | null;
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

export interface CourseLecturerPublic {
  id: number;
  name: string;
  github_alias: string | null;
  email: string;
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

export interface CourseCreate {
  code: string;
  name: string;
  term: CourseTerm;
  project_type: ProjectType;
  min_score: number;
  owner_email: string;
  syllabus?: string | null;
  peer_bonus_budget?: number | null;
  evaluation_criteria?: EvaluationCriterion[];
  links?: CourseLink[];
}

export interface CourseUpdate {
  code?: string;
  name?: string;
  term?: CourseTerm;
  project_type?: ProjectType;
  min_score?: number;
  syllabus?: string | null;
  peer_bonus_budget?: number | null;
  evaluation_criteria?: EvaluationCriterion[];
  links?: CourseLink[];
}

export interface ProjectCreate {
  title: string;
  description?: string | null;
  github_url?: string | null;
  live_url?: string | null;
  technologies: string[];
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

export interface CourseEvaluationFormResponse {
  teammates: MemberPublic[];
  peer_bonus_budget: number | null;
  current_evaluation: CourseEvaluationDetail | null;
  authored_peer_feedback: PeerFeedbackDetail[];
  results_unlocked: boolean;
}

export interface CourseEvaluationSubmit {
  submitted: boolean;
  rating: number | null;
  strengths: string | null;
  improvements: string | null;
  peer_feedback: {
    receiving_student_id: number;
    strengths: string | null;
    improvements: string | null;
    bonus_points: number;
  }[];
}
