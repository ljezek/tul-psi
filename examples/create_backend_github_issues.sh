#!/bin/bash

## This script automates the creation of GitHub Issues for the backend and DB of Student Projects
## Catalogue backend development. It is structured around the defined milestones and phases. It
## uses the GitHub CLI (gh) to create issues directly in the repository, ensuring that all tasks
## are properly categorized and linked to their respective user stories.
##
## Note: This script was created by Gemini Pro based on the README, DESIGN, and SPECIFICATION.

set -euo pipefail

# Ensure gh cli is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) could not be found. Please install it first."
    exit 1
fi

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

# Register CHILD_NUMBER as a sub-issue of PARENT_NUMBER using the GitHub Sub-Issues API.
add_sub_issue() {
    local parent_number=$1
    local child_number=$2
    local child_db_id
    child_db_id=$(gh api "repos/$REPO/issues/$child_number" --jq '.id')
    gh api --method POST \
        -H "Accept: application/vnd.github+json" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        "repos/$REPO/issues/$parent_number/sub_issues" \
        -F "sub_issue_id=$child_db_id" --silent
}

echo "🚀 Generating GitHub Issues for Student Projects Catalogue..."

MILESTONE="Milestone 2: core functionality"

# --- PHASE 1: Foundation ---
echo "Creating Phase 1 (Foundation)..."
P1_ID=$(gh issue create --title "Backend Foundation & Setup" --body "As a developer, I need the backend skeleton set up with FastAPI, a database connection, and basic testing so that I can begin implementing feature logic." --label "user-story" --milestone "$MILESTONE" | awk -F/ '{print $NF}')

TASK_ID=$(gh issue create --title "Create AI Copilot Instructions" --body "Draft the \`.github/copilot-instructions.md\` file containing the project's tech stack, coding standards, and testing strategy to align all future AI work." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P1_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "Project Setup & Linter" --body "Initialize the Python environment, install FastAPI, SQLModel, Uvicorn, and Pytest. Set up standard Ruff linting configuration." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P1_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "Dockerized Database" --body "Create a \`docker-compose.yml\` that spins up a local PostgreSQL instance based on the architecture doc." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P1_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "Health Check Endpoint" --body "Implement \`GET /health\` returning \`{\"status\": \"ok\", \"version\": \"1.0.0\"}\`." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P1_ID" "$TASK_ID"; sleep 1

# --- PHASE 2: Data Persistence Layer ---
echo "Creating Phase 2 (Data Persistence)..."
P2_ID=$(gh issue create --title "Data Persistence Layer" --body "As a developer, I need the database schema and ORM models configured so that the application can store and retrieve core entities." --label "user-story" --milestone "$MILESTONE" | awk -F/ '{print $NF}')

TASK_ID=$(gh issue create --title "Base Models & Alembic Init" --body "Initialize Alembic and configure it to read from the \`DATABASE_URL\`." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P2_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "Core Entities (Users, Courses, Projects)" --body "Implement SQLModel classes for \`USER\`, \`COURSE\`, \`PROJECT\`, and \`PROJECT_MEMBER\`." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P2_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "Evaluation Entities" --body "Implement \`COURSE_EVALUATION\`, \`PROJECT_EVALUATION\`, and \`PEER_FEEDBACK\` using JSONB columns where specified." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P2_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "Database Dev Seed Script" --body "Create a \`seed.py\` script that populates the local PostgreSQL database with mock users, courses, and projects to unblock frontend and discovery API development." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P2_ID" "$TASK_ID"; sleep 1

# --- PHASE 3A: Public API (Parallel to Auth) ---
echo "Creating Phase 3A (Project Discovery)..."
P3A_ID=$(gh issue create --title "Public API & Project Discovery" --body "As a visitor, I need API endpoints to search and filter through existing student projects without needing to log in." --label "user-story" --milestone "$MILESTONE" | awk -F/ '{print $NF}')

TASK_ID=$(gh issue create --title "Project Discovery Endpoint" --body "Implement \`GET /api/v1/projects\` with query parameters to filter by \`q\` (search), \`course\`, \`year\`, \`term\`, and \`technology\`." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P3A_ID" "$TASK_ID"; sleep 1

# --- PHASE 3B: Authentication Flow ---
echo "Creating Phase 3B (Authentication)..."
P3B_ID=$(gh issue create --title "Authentication Flow (Faked SMTP)" --body "As a user, I need to log in using a One-Time Password sent to my \`@tul.cz\` email so that I can securely access role-based features." --label "user-story" --milestone "$MILESTONE" | awk -F/ '{print $NF}')

TASK_ID=$(gh issue create --title "OTP Request Endpoint" --body "Implement \`POST /api/v1/auth/otp/request\`. Reject non-\`@tul.cz\` emails with 422. Fake the SMTP step by logging the 6-digit OTP to the terminal." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P3B_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "OTP Verify & JWT generation" --body "Implement \`POST /api/v1/auth/otp/verify\`. Validate the token, mark it as used, and return a mocked JWT in an HttpOnly cookie." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P3B_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "Auth Dependency" --body "Create a FastAPI dependency (e.g., \`get_current_user\`) that reads the JWT cookie, mocks the CSRF check, and injects the user context into protected routes." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P3B_ID" "$TASK_ID"; sleep 1

# --- PHASE 4: Core API CRUD (Protected) ---
echo "Creating Phase 4 (Core API)..."
P4_ID=$(gh issue create --title "Core API & Project Management" --body "As a lecturer or student, I need protected API endpoints to manage courses and seed new projects." --label "user-story" --milestone "$MILESTONE" | awk -F/ '{print $NF}')

TASK_ID=$(gh issue create --title "Course Management Endpoints" --body "Implement \`GET /api/v1/courses\` (public list), \`POST /api/v1/courses\` (Admin only), and \`GET /api/v1/courses/{id}\`." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P4_ID" "$TASK_ID"; sleep 1

TASK_ID=$(gh issue create --title "Project Seeding Endpoint" --body "Implement \`POST /api/v1/courses/{id}/projects\`. Create the project and fake sending an invite email to the assigned owner." --label "task" --milestone "$MILESTONE" | awk -F/ '{print $NF}')
add_sub_issue "$P4_ID" "$TASK_ID"; sleep 1

# --- PHASE 5: Feedback & Evaluation (User Stories Only) ---
echo "Creating Phase 5 (Evaluations)..."
gh issue create --title "Lecturer Project Evaluation" --body "As a lecturer, I need to submit numeric scores and textual feedback across multiple criteria configured for the course." --label "user-story" --milestone "$MILESTONE"
sleep 1
gh issue create --title "Student Course & Peer Evaluation" --body "As a student, I need a combined form to evaluate the course quality and provide qualitative peer feedback. The system must unlock results only after all teammates publish and lecturers submit their evaluation." --label "user-story" --milestone "$MILESTONE"
sleep 1

# --- PHASE 6: Observability (User Stories Only) ---
echo "Creating Phase 6 (Observability)..."
gh issue create --title "System Observability & Telemetry" --body "As a system operator, I need the application to emit OTLP traces and Prometheus metrics via OpenTelemetry SDK, and output structured JSON logs." --label "user-story" --milestone "$MILESTONE"
sleep 1

echo "✅ All issues successfully generated and assigned to Milestone 2!"