from __future__ import annotations

import logging
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from clients.fake_http_client import enrich_project_info
from db.fake_db import load_projects_from_db
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
        with self._tracer.start_as_current_span(
            "projects_service.get_projects"
        ) as span:
            span.set_attribute("client.type", client_type)
            span.set_attribute("filters.academic_year", academic_year or "")
            span.set_attribute("filters.subject", subject or "")

            try:
                projects = await load_projects_from_db(
                    self.settings.projects_data_file,
                    self.settings.simulated_db_delay_ms,
                    academic_year=academic_year,
                    subject=subject,
                    error_rate=self.settings.db_error_rate,
                )

                for project in projects:
                    enrichment = await enrich_project_info(
                        project_name=project.title,
                        delay_ms=self.settings.simulated_http_delay_ms,
                        error_rate=self.settings.enrich_error_rate,
                    )
                    project.students = enrichment["students"]
            except RuntimeError as exc:
                span.set_status(StatusCode.ERROR, str(exc))
                span.record_exception(exc)
                logger.error(
                    "get_projects_failed",
                    extra={
                        "client_type": client_type,
                        "academic_year": academic_year,
                        "subject": subject,
                        "root_cause": str(exc),
                    },
                )
                raise

            span.set_attribute("projects.count", len(projects))
            return projects
