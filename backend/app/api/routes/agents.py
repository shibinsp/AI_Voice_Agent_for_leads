from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.entities import Agent
from app.schemas.agent import AgentCreate, AgentListResponse, AgentRead, AgentUpdate

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
def list_agents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> AgentListResponse:
    items = db.scalars(
        select(Agent)
        .order_by(Agent.is_active.desc(), Agent.updated_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    total = db.scalar(select(func.count()).select_from(Agent)) or 0
    return AgentListResponse(
        items=[AgentRead.model_validate(item) for item in items],
        total=total,
    )


@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: int, db: Session = Depends(get_db)) -> AgentRead:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentRead.model_validate(agent)


@router.post("", response_model=AgentRead, status_code=status.HTTP_201_CREATED)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)) -> AgentRead:
    _raise_if_duplicate(db, name=payload.name, script_key=payload.script_key)

    agent = Agent(**payload.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return AgentRead.model_validate(agent)


@router.patch("/{agent_id}", response_model=AgentRead)
def update_agent(
    agent_id: int,
    payload: AgentUpdate,
    db: Session = Depends(get_db),
) -> AgentRead:
    agent = db.get(Agent, agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data or "script_key" in update_data:
        _raise_if_duplicate(
            db,
            name=update_data.get("name"),
            script_key=update_data.get("script_key"),
            exclude_id=agent_id,
        )

    for key, value in update_data.items():
        setattr(agent, key, value)

    db.add(agent)
    db.commit()
    db.refresh(agent)
    return AgentRead.model_validate(agent)


def _raise_if_duplicate(
    db: Session,
    *,
    name: str | None,
    script_key: str | None,
    exclude_id: int | None = None,
) -> None:
    clauses = []
    if name is not None:
        clauses.append(Agent.name == name)
    if script_key is not None:
        clauses.append(Agent.script_key == script_key)
    if not clauses:
        return

    query = select(Agent).where(or_(*clauses))
    if exclude_id is not None:
        query = query.where(Agent.id != exclude_id)

    existing = db.scalar(query)
    if existing is None:
        return

    if name is not None and existing.name == name:
        detail = "Agent name already exists"
    else:
        detail = "Agent script_key already exists"
    raise HTTPException(status_code=409, detail=detail)

