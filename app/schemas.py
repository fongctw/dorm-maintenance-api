from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import Priority, Role, TicketStatus


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: list[dict] = Field(default_factory=list)


class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class CategoryOut(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentBase(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class CommentCreate(CommentBase):
    pass


class CommentOut(CommentBase):
    id: int
    author_role: Role
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketBase(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=2000)
    room: str = Field(pattern=r"^[A-Z]-\d{4}$")
    priority: Priority
    category_id: int


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    room: str | None = Field(default=None, pattern=r"^[A-Z]-\d{4}$")
    priority: Priority | None = None
    category_id: int | None = None


class StatusUpdateRequest(BaseModel):
    status: TicketStatus


class TicketOut(TicketBase):
    id: int
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    comments: list[CommentOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
