from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from agent.models.request import Request, RequestCreate
from agent.models.enums import StatusType
from agent.db import crud

router = APIRouter(prefix="/requests", tags=["requests"])


class RequestUpdate(BaseModel):
    status: Optional[StatusType] = None
    media_id: Optional[str] = None
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None


@router.post("", response_model=Request)
async def create(body: RequestCreate):
    data = body.model_dump(exclude_none=True)
    data["req_type"] = data.pop("type")

    # Reject if there's already an active request for the same scene + type
    scene_id = data.get("scene_id")
    req_type = data.get("req_type")
    if scene_id and req_type:
        existing = await crud.list_requests(scene_id=scene_id)
        active = [r for r in existing
                  if r.get("type") == req_type
                  and r.get("status") in ("PENDING", "PROCESSING")]
        if active:
            raise HTTPException(
                409,
                f"Active {req_type} request already exists for scene {scene_id[:8]} "
                f"(status={active[0]['status']}, id={active[0]['id'][:8]})"
            )

    return await crud.create_request(**data)


@router.get("", response_model=list[Request])
async def list_all(scene_id: str = None, status: str = None):
    return await crud.list_requests(scene_id=scene_id, status=status)


@router.get("/pending", response_model=list[Request])
async def list_pending():
    return await crud.list_pending_requests()


@router.get("/{rid}", response_model=Request)
async def get(rid: str):
    r = await crud.get_request(rid)
    if not r:
        raise HTTPException(404, "Request not found")
    return r


@router.patch("/{rid}", response_model=Request)
async def update(rid: str, body: RequestUpdate):
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(400, "No fields to update")
    r = await crud.update_request(rid, **data)
    if not r:
        raise HTTPException(404, "Request not found")
    return r
