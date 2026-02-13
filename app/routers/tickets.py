from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_role
from app.errors import AppException
from app.models import Category, Comment, Priority, Role, Ticket, TicketStatus
from app.schemas import CommentCreate, CommentOut, StatusUpdateRequest, TicketCreate, TicketOut, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["tickets"])

VALID_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.open: {TicketStatus.in_progress, TicketStatus.rejected},
    TicketStatus.in_progress: {TicketStatus.done, TicketStatus.rejected},
    TicketStatus.done: set(),
    TicketStatus.rejected: set(),
}


SORT_COLUMNS = {
    "id": Ticket.id,
    "created_at": Ticket.created_at,
    "updated_at": Ticket.updated_at,
    "priority": Ticket.priority,
    "status": Ticket.status,
}


def _get_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.comments), joinedload(Ticket.category))
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise AppException(status_code=404, code="NOT_FOUND", message="Ticket not found")
    return ticket


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)) -> Ticket:
    category = db.query(Category).filter(Category.id == payload.category_id, Category.is_active.is_(True)).first()
    if not category:
        raise AppException(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Invalid category",
            details=[{"field": "category_id", "message": "Category not found or inactive"}],
        )

    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    return _get_ticket_or_404(ticket.id, db)


@router.get("", response_model=list[TicketOut])
def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: Priority | None = None,
    category_id: int | None = None,
    room: str | None = None,
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[Ticket]:
    query = db.query(Ticket).options(joinedload(Ticket.comments))

    if status_filter is not None:
        query = query.filter(Ticket.status == status_filter)
    if priority is not None:
        query = query.filter(Ticket.priority == priority)
    if category_id is not None:
        query = query.filter(Ticket.category_id == category_id)
    if room is not None:
        query = query.filter(Ticket.room == room)

    sort_column = SORT_COLUMNS.get(sort_by)
    if sort_column is None:
        raise AppException(
            status_code=400,
            code="VALIDATION_ERROR",
            message="Invalid sort field",
            details=[{"field": "sort_by", "message": f"Must be one of: {', '.join(SORT_COLUMNS.keys())}"}],
        )

    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    return query.offset(skip).limit(limit).all()


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Ticket:
    return _get_ticket_or_404(ticket_id, db)


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    role: Role = Depends(get_role),
    db: Session = Depends(get_db),
) -> Ticket:
    ticket = _get_ticket_or_404(ticket_id, db)

    if role == Role.student and ticket.status != TicketStatus.open:
        raise AppException(
            status_code=403,
            code="FORBIDDEN",
            message="Student can edit ticket only when status is open",
        )

    updates = payload.model_dump(exclude_unset=True)

    if "category_id" in updates:
        category = db.query(Category).filter(Category.id == updates["category_id"], Category.is_active.is_(True)).first()
        if not category:
            raise AppException(
                status_code=400,
                code="VALIDATION_ERROR",
                message="Invalid category",
                details=[{"field": "category_id", "message": "Category not found or inactive"}],
            )

    for key, value in updates.items():
        setattr(ticket, key, value)

    db.commit()
    return _get_ticket_or_404(ticket_id, db)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)) -> Response:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise AppException(status_code=404, code="NOT_FOUND", message="Ticket not found")

    db.delete(ticket)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    ticket_id: int,
    payload: CommentCreate,
    role: Role = Depends(get_role),
    db: Session = Depends(get_db),
) -> Comment:
    _get_ticket_or_404(ticket_id, db)

    comment = Comment(ticket_id=ticket_id, message=payload.message, author_role=role)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.put("/{ticket_id}/status", response_model=TicketOut)
def update_ticket_status(
    ticket_id: int,
    payload: StatusUpdateRequest,
    role: Role = Depends(get_role),
    db: Session = Depends(get_db),
) -> Ticket:
    if role != Role.technician:
        raise AppException(status_code=403, code="FORBIDDEN", message="Only technician can update status")

    ticket = _get_ticket_or_404(ticket_id, db)
    if payload.status not in VALID_TRANSITIONS[ticket.status]:
        raise AppException(
            status_code=409,
            code="INVALID_STATUS_TRANSITION",
            message=f"Cannot transition from {ticket.status.value} to {payload.status.value}",
        )

    ticket.status = payload.status
    db.commit()
    return _get_ticket_or_404(ticket_id, db)
