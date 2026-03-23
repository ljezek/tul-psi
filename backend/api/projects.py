from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from models.project import Project
from observability.context import detect_client_type
from services.projects_service import ProjectsService
from settings import Settings, get_settings

router = APIRouter(prefix="", tags=["projects"])


def get_projects_service(settings: Settings = Depends(get_settings)) -> ProjectsService:
    return ProjectsService(settings)


@router.get("/projects", response_model=list[Project])
async def get_projects(
    request: Request,
    academic_year: str | None = None,
    subject: str | None = None,
    service: ProjectsService = Depends(get_projects_service),
):
    client_type = detect_client_type(request)
    return await service.get_projects(academic_year=academic_year, subject=subject, client_type=client_type)
