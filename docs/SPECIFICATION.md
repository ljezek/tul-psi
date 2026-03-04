# Product Specification: Student Projects Catalogue

## Product Vision & Target Audience
The **Student Projects Catalogue** is a centralized platform designed for the Faculty of Mechatronics, Informatics and Interdisciplinary Studies at the Technical University of Liberec (_TUL_). Its vision is to provide a centralized repository of various student projects created at TUL and foster a culture of constructive feedback by allowing students to evaluate the courses and peers.

**Target Audience:**
*   **Students:** To present their work, reflect on their learning experience, and provide/receive peer feedback.
*   **Lecturers:** To manage course projects, monitor student collaboration, and gather insights for course improvement.
*   **General Public / Partners:** To explore the innovative outputs of the faculty's students and identify potential talent or collaboration opportunities.

**Success metrics:**
*   >90% of students provide course and peer feedback.

## User Scenarios

### 1. Public Project Discovery
A visitor arrives at the site to see the faculty's ongoing and finished projects. They use the **Dashboard** to filter by course, academic year or search for specific technologies (e.g., "AI", "SQL"). They click on a project card to see a full description, the student team, and links to source code or live demos.

### 2. Student Reflection & Peer Evaluation
After a student completes a project, they switch to the **Student Zone**, where they fill out course evaluation to help the lecturer(s) improve the course for future students.

Additionally, for team projects students evaluate their peers: fill out qualitative peer feedback and distribute bonus points. After all project feedback is collected, the app displays anonymized feedback to each student.

The evaluation forms are designed to promote constructive feedback (i.e., 1 strength and 1 area for improvement).

### 3. Lecturer Administration & Quality Control
A lecturer uses the **Admin Panel** to set up the courses and manage projects. They create projects and assign students to their respective teams.

At the end of the term, they review the **Feedback** tab. They see anonymized courses feedback to identify course pain points and check the **Average Peer Bonus Points** to identify high-performers or potential team conflicts.

## UX Flow
```mermaid
graph TD
    Start[App Entry] --> RoleSelect{Role Selection}
    RoleSelect -->|Public| Dashboard[Project Dashboard]
    RoleSelect -->|Student| StudentZone[Student Zone]
    RoleSelect -->|Lecturer| AdminPanel[Admin Panel]
    
    Dashboard --> ProjectDetail[Project Detail (Modal)]
    
    StudentZone --> CourseEval[Course Evaluation Form]
    StudentZone --> PeerEval[Peer Feedback Form]
    StudentZone --> RecFeedback[View Received Feedback]
    
    AdminPanel --> ProjMgmt[Project Management]
    AdminPanel --> CourseMgmt[Course Management]
    AdminPanel --> FeedbackReview[Feedback Review & Stats]
```

## Functional Requirements

### Must have
*   **Project Catalogue:** Searchable and filterable list of student projects with detailed modals.
*   **Role-Based Access:** Distinct views for Public, Student, and Lecturer roles.
*   **Project Management:** Lecturer interface to create new courses, projects and assign students to teams.
*   **Peer Feedback System:** 
    *   Qualitative feedback (Strengths/Improvements) for each teammate.
    *   Quantitative bonus point distribution to peers.

### Should have
*   **Course Evaluation:** Student form for collecting constructive feedback for course quality and future improvements.
*   **Anonymized Reporting:**
    *    Course feedback is presented to lecturers without student names to ensure honesty.
    *    Students can view anonymized feedback received from their peers to help them grow.
*   **Collaboration Analytics:** Lecturers can view for each student average peer bonus points and anonymized peer feedback.

### Could have
*   **Bilingual Interface:** Full support for Czech and English languages.
*   **Feedback Moderation:** Filtering/flagging of inappropriate comments in the feedback.
*   **Student-driven Project Management:** Student interface for managing their projects: adding description, project links and peers. This would help offload lecturers (who would only send project invite to lead student in each project).

## Prototype
The working prototype of this application is available at:
[https://ais-dev-wraur5d2xxu7fjsci5byoi-507011329275.europe-west2.run.app](https://ais-dev-wraur5d2xxu7fjsci5byoi-507011329275.europe-west2.run.app)

## Non-Goals: Out of Scope
*   **Integration with TUL SSO:** For simplicity we plan to use One-Time-Password for authentication rather than integration with TUL SSO (Shibo).
*   **Direct Messaging:** No real-time chat functionality between users.
*   **Grade Automation:** The system provides data to lecturers but does not automatically calculate final grades.
*   **Asset Hosting:** The platform links to external repositories (GitHub) rather than hosting project binaries or datasets.

## Non-Functional Requirements (NFR)

*   **Availability & Reliability:** The system must be hosted on Azure with a target availability of 99.5% (SLA), particularly during the final submission and exam periods.
    * **Health checks** must be implemented to facilitate automated instance recovery within the cloud environment
*   **Scalability:** To handle traffic spikes near project deadlines, the application shall utilize Azure Auto-scaling and capacity planning.
*   **Security:** The platform must implement protection against CORS and XSRF vulnerabilities. User authentication will use OTP and secure credential management.
*   **Observability (Monitoring & Logging):** Real-time monitoring, alerting, and logging must be configured using *Azure Application Insights* to track system health and errors.
*   **CI/CD Pipeline:** A fully automated CI/CD pipeline must be established to execute unit and integration tests on every commit to the `main` branch. Successful builds must be automatically deployed to the Azure environment (guarded by quality checks, unit and integration tests).
*   **Code Quality & Maintainability:** The project must adhere to "Clean Code" principles.
    *   All architectural decisions and changes must be **documented** in the repository via Markdown files (README, Spec, and Design Doc).
    *   All code must have consistent **code style**.
    *   No direct commits to the `main` (all changes are made via **Pull Requests with Code Review**).
    *   **Unit tests** with > 80% coverage.