from pydantic import BaseModel

from app.services.contracts import Role
from app.services.overview_contracts import Overview


class OverviewResponse(BaseModel):
    role: Role
    statistics: Overview
