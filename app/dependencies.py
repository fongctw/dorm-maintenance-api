from fastapi import Header

from app.errors import AppException
from app.models import Role


def get_role(x_role: str = Header(..., alias="X-Role")) -> Role:
    value = x_role.strip().lower()
    if value not in {Role.student.value, Role.technician.value}:
        raise AppException(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Invalid role",
            details=[{"field": "X-Role", "message": "Must be student or technician"}],
        )
    return Role(value)
