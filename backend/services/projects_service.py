from __future__ import annotations

import json
import logging
from pathlib import Path
from opentelemetry import trace

from clients.fake_http_client import call_backend_service
from db.fake_db import simulate_query
from models.project import Project
from settings import Settings

logger = logging.getLogger(__name__)


class ProjectsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._tracer = trace.get_tracer("tul.psi.projects-service")

    async def get_projects(
        self,
        academic_year: str | None,
        subject: str | None,
        client_type: str,
    ) -> list[Project]:
        with self._tracer.start_as_current_span("projects_service.get_projects") as span:
            span.set_attribute("client.type", client_type)
            span.set_attribute("filters.academic_year", academic_year or "")
            span.set_attribute("filters.subject", subject or "")

            await simulate_query("load_projects_json", self.settings.simulated_db_delay_ms)
            await call_backend_service(
                service_name="student-profile-service",
                operation="hydrate-project-owner",
                delay_ms=self.settings.simulated_http_delay_ms,
            )

            projects = self._load_projects_from_disk()

            filtered = [
                p
                for p in projects
                if (not academic_year or p.academic_year == academic_year)
                and (not subject or p.subject.lower() == subject.lower())
            ]

            logger.info(
                "projects_query_completed",
                extra={
                    "client_type": client_type,
                    "academic_year": academic_year,
                    "subject": subject,
                    "projects_count": len(filtered),
                },
            )
            span.set_attribute("projects.count", len(filtered))
            return filtered

    def _load_projects_from_disk(self) -> list[Project]:
        file_path = Path(self.settings.projects_data_file)

        if not file_path.exists():
            raise FileNotFoundError(f"Projects data file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)

        projects: list[Project] = []
        if isinstance(payload, dict) and "projects" in payload:
            items = payload.get("projects", [])
            for row in items:
                projects.append(
                    Project(
                        id=row["id"],
                        title=row["title"],
                        academic_year=row["academicYear"],
                        subject=row["subject"],
                        technologies=row.get("technologies", []),
                    )
                )
            return projects

        raise ValueError("Unsupported projects data format")
