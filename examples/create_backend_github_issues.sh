#!/bin/bash

## This script automates the creation of GitHub Issues for the backend and DB of Student Projects
## Catalogue backend development. It is structured around the defined milestones and phases. It
## uses the GitHub CLI (gh) to create issues directly in the repository, ensuring that all tasks
## are properly categorized and linked to their respective user stories.
##
## Note: This script was created by Gemini Pro based on the README, DESIGN, and SPECIFICATION.
##
## Idempotent: re-running skips issues that already exist (matched by exact title)
## and skips sub-issue links that are already present.

set -euo pipefail

# Ensure gh cli is installed
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI (gh) could not be found. Please install it first."
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo "jq could not be found. Please install it first."
    exit 1
fi

REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)

# Returns the issue number if an open or closed issue with this exact title already exists,
# otherwise returns an empty string.
find_issue() {
    local title="$1"
    gh issue list --repo "$REPO" --state all --search "$title" --json number,title \
        | jq -r --arg t "$title" '.[] | select(.title == $t) | .number' \
        | head -1
}

# Creates an issue only if one with the same title does not already exist.
# Optional 4th argument: parent issue number — links the new issue as a sub-issue and sleeps 1s.
# Prints the issue number to stdout; status messages go to stderr.
get_or_create_issue() {
    local title="$1"
    local body="$2"
    local label="$3"
    local parent="${4:-}"

    local number
    number=$(find_issue "$title")

    if [[ -z "$number" ]]; then
        number=$(gh issue create --title "$title" --body "$body" --label "$label" --milestone "$MILESTONE" \
            | awk -F/ '{print $NF}')
    else
        echo "  ⏭  Already exists #$number: $title" >&2
    fi

    if [[ -n "$parent" ]]; then
        add_sub_issue "$parent" "$number"
        sleep 1
    fi

    echo "$number"
}

# Register CHILD_NUMBER as a sub-issue of PARENT_NUMBER using the GitHub Sub-Issues API.
# Skips silently if the link already exists.
add_sub_issue() {
    local parent_number=$1
    local child_number=$2

    local already_linked
    already_linked=$(gh api "repos/$REPO/issues/$parent_number/sub_issues" 2>/dev/null \
        | jq --argjson n "$child_number" '[.[] | .number] | map(select(. == $n)) | length' \
        || echo "0")

    if [[ "$already_linked" -gt 0 ]]; then
        echo "  ⏭  Sub-issue link already exists: #$parent_number → #$child_number" >&2
        return
    fi

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
P1_ID=$(get_or_create_issue \
    "Backend Foundation & Setup" \
    "As a developer, I need the backend skeleton set up with FastAPI, a database connection, and basic testing so that I can begin implementing feature logic." \
    "user-story")

get_or_create_issue \
    "Create AI Copilot Instructions" \
    "Draft the \`.github/copilot-instructions.md\` file containing the project's tech stack, coding standards, and testing strategy to align all future AI work." \
    "task" "$P1_ID"

get_or_create_issue \
    "Project Setup & Linter" \
    "Initialize the Python environment, install FastAPI, SQLModel, Uvicorn, and Pytest. Set up standard Ruff linting configuration." \
    "task" "$P1_ID"

get_or_create_issue \
    "Dockerized Database" \
    "Create a \`docker-compose.yml\` that spins up a local PostgreSQL instance based on the architecture doc." \
    "task" "$P1_ID"

get_or_create_issue \
    "Health Check Endpoint" \
    "Implement \`GET /health\` returning \`{\"status\": \"ok\", \"version\": \"1.0.0\"}\`." \
    "task" "$P1_ID"

# --- PHASE 2: Data Persistence Layer ---
echo "Creating Phase 2 (Data Persistence)..."
P2_ID=$(get_or_create_issue \
    "Data Persistence Layer" \
    "As a developer, I need the database schema and ORM models configured so that the application can store and retrieve core entities." \
    "user-story")

get_or_create_issue \
    "Base Models & Alembic Init" \
    "Initialize Alembic and configure it to read from the \`DATABASE_URL\`." \
    "task" "$P2_ID"

get_or_create_issue \
    "Core Entities (Users, Courses, Projects)" \
    "Implement SQLModel classes for \`USER\`, \`COURSE\`, \`PROJECT\`, and \`PROJECT_MEMBER\`." \
    "task" "$P2_ID"

get_or_create_issue \
    "Evaluation Entities" \
    "Implement \`COURSE_EVALUATION\`, \`PROJECT_EVALUATION\`, and \`PEER_FEEDBACK\` using JSONB columns where specified." \
    "task" "$P2_ID"

get_or_create_issue \
    "Database Dev Seed Script" \
    "Create a \`seed.py\` script that populates the local PostgreSQL database with mock users, courses, and projects to unblock frontend and discovery API development." \
    "task" "$P2_ID"

# --- PHASE 3A: Public API (Parallel to Auth) ---
echo "Creating Phase 3A (Project Discovery)..."
P3A_ID=$(get_or_create_issue \
    "Public API & Project Discovery" \
    "As a visitor, I need API endpoints to search and filter through existing student projects without needing to log in." \
    "user-story")

get_or_create_issue \
    "Project Discovery Endpoint" \
    "Implement \`GET /api/v1/projects\` with query parameters to filter by \`q\` (search), \`course\`, \`year\`, \`term\`, and \`technology\`." \
    "task" "$P3A_ID"

# --- PHASE 3B: Authentication Flow ---
echo "Creating Phase 3B (Authentication)..."
P3B_ID=$(get_or_create_issue \
    "Authentication Flow (Faked SMTP)" \
    "As a user, I need to log in using a One-Time Password sent to my \`@tul.cz\` email so that I can securely access role-based features." \
    "user-story")

get_or_create_issue \
    "OTP Request Endpoint" \
    "Implement \`POST /api/v1/auth/otp/request\`. Reject non-\`@tul.cz\` emails with 422. Fake the SMTP step by logging the 6-digit OTP to the terminal." \
    "task" "$P3B_ID"

get_or_create_issue \
    "OTP Verify & JWT generation" \
    "Implement \`POST /api/v1/auth/otp/verify\`. Validate the token, mark it as used, and return a mocked JWT in an HttpOnly cookie." \
    "task" "$P3B_ID"

get_or_create_issue \
    "Auth Dependency" \
    "Create a FastAPI dependency (e.g., \`get_current_user\`) that reads the JWT cookie, mocks the CSRF check, and injects the user context into protected routes." \
    "task" "$P3B_ID"

# --- PHASE 4: Core API CRUD (Protected) ---
echo "Creating Phase 4 (Core API)..."
P4_ID=$(get_or_create_issue \
    "Core API & Project Management" \
    "As a lecturer or student, I need protected API endpoints to manage courses and seed new projects." \
    "user-story")

get_or_create_issue \
    "Course Management Endpoints" \
    "Implement \`GET /api/v1/courses\` (public list), \`POST /api/v1/courses\` (Admin only), and \`GET /api/v1/courses/{id}\`." \
    "task" "$P4_ID"

get_or_create_issue \
    "Project Seeding Endpoint" \
    "Implement \`POST /api/v1/courses/{id}/projects\`. Create the project and fake sending an invite email to the assigned owner." \
    "task" "$P4_ID"

# --- PHASE 5: Feedback & Evaluation (User Stories Only) ---
echo "Creating Phase 5 (Evaluations)..."
get_or_create_issue \
    "Lecturer Project Evaluation" \
    "As a lecturer, I need to submit numeric scores and textual feedback across multiple criteria configured for the course." \
    "user-story"
sleep 1
get_or_create_issue \
    "Student Course & Peer Evaluation" \
    "As a student, I need a combined form to evaluate the course quality and provide qualitative peer feedback. The system must unlock results only after all teammates publish and lecturers submit their evaluation." \
    "user-story"
sleep 1

# --- PHASE 6: Observability (User Stories Only) ---
echo "Creating Phase 6 (Observability)..."
get_or_create_issue \
    "System Observability & Telemetry" \
    "As a system operator, I need the application to emit OTLP traces and Prometheus metrics via OpenTelemetry SDK, and output structured JSON logs." \
    "user-story"
sleep 1

echo "✅ All issues successfully generated and assigned to Milestone 2!"
