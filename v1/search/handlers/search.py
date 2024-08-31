import os
import uuid
import aiofiles
import traceback

from typing import Optional, Any, Union, List

from fastapi import (
    APIRouter,
    status,
    Response,
    Header,
    Request,
    Depends,
    BackgroundTasks,
    UploadFile,
    Query,
)

from v1.search.models.request import SearchRequest, TaskRestartRequest
from v1.search.models.response import (
    SearchResponse,
    ParsingTaskResultResponse,
    ParsingTaskResponse,
    ParsingTasksListResponse,
    ParsingTaskStartResponse,
)

from response_models import Error40xResponse

from managers.search.manager import SearchManager
from managers.search.task_manager import ParsingTasksManager
from managers.permissions.permissions import check_auth

from models.session import get_session
from models.models import User, ParsingTasks
from models.base import TaskStatus

from tasks.mass_search import mass_search

from config import STATIC_DIR


router = APIRouter(
    prefix="/v1/search",
    tags=["search"]
)


@router.post(
    "/fts",
    responses={
        200: {
            "model": List[SearchResponse],
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def search_method(
    request: Request,
    search: SearchRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    user: User = Depends(check_auth),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[SearchResponse, Error40xResponse]:
    async with get_session() as s:
        manager = SearchManager(s, user)
        res, st = await manager.search(
            search.fts,
            search.provider,
            search.country,
            search.search_type,
            request.headers.get("SocketId", 0),
            request.user.id,
            background_tasks,
            redis_connection=request.app.redis_pubsub_con,
        )
        return SearchResponse(
            provider_name=search.provider,
            data=[i for i in res.get("items", []) if isinstance(i, dict)],
        )


@router.post(
    "/search_task/create",
    responses={
        200: {
            "model": ParsingTaskStartResponse,
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def create_task_search_method(
    request: Request,
    file: UploadFile,
    response: Response,
    background_tasks: BackgroundTasks,
    user: User = Depends(check_auth),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[Error40xResponse, ParsingTaskStartResponse]:
    task_id = uuid.uuid4().hex
    os.makedirs(os.path.join(STATIC_DIR, "tasks", task_id), exist_ok=True)
    async with aiofiles.open(
        os.path.join(STATIC_DIR, "tasks", task_id, f"{task_id}.csv"),
        mode="wb",
    ) as afp:
        await afp.write(file.file.read())

    manager = ParsingTasksManager(background_tasks, request.user.id, task_id)
    await manager.start_task("create")

    return ParsingTaskStartResponse(task_id=task_id)


@router.post(
    "/search_task/restart",
    responses={
        200: {
            "model": Error40xResponse,
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def restart_task_search_method(
    request: Request,
    data: TaskRestartRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    user: User = Depends(check_auth),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Error40xResponse:
    manager = ParsingTasksManager(background_tasks, request.user.id)
    task = await manager.get(data.task_id)
    manager.task_id = task.task_id
    await manager.start_task("restart")

    return Error40xResponse(reason="pending")


@router.get(
    "/search_task/report",
    responses={
        200: {
            "model": ParsingTaskResultResponse,
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def report_task_search_method(
    request: Request,
    task_id: int,
    response: Response,
    background_tasks: BackgroundTasks,
    user: User = Depends(check_auth),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[Error40xResponse, ParsingTaskResultResponse]:
    manager = ParsingTasksManager(background_tasks, request.user.id)
    task = await manager.get(task_id)
    try:
        files = os.listdir(os.path.join(STATIC_DIR, "tasks", task.task_id, "report"))
    except Exception:
        print(traceback.format_exc())
        return ParsingTaskResultResponse(files=[], count=0)
    else:
        return ParsingTaskResultResponse(
            files=[os.path.join(STATIC_DIR, "tasks", task.task_id, "report", f) for f in files],
            count=len(files),
        )


@router.get(
    "/search_tasks/list",
    responses={
        200: {
            "model": ParsingTasksListResponse,
        },
        401: {
            "model": Error40xResponse,
            "description": "wrong auth token",
        },
    },
    summary="authentication",
)
async def list_task_search_method(
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    limit: int = Query(10),
    offset: int = Query(0),
    user: User = Depends(check_auth),
    status_code: Optional[Any] = Header(status.HTTP_200_OK, description="internal usage, not used by client"),
) -> Union[Error40xResponse, ParsingTasksListResponse]:
    manager = ParsingTasksManager(background_tasks, request.user.id)
    tasks, count = await manager.list_tasks(limit, offset)
    return ParsingTasksListResponse(
        result=[
            ParsingTaskResponse(
                id=t.id,
                task_id=t.task_id,
                filename=os.path.join(STATIC_DIR, "tasks", t.task_id, t.filename),
                status=t.status_str,
                created_at=t.created_at,
                full_report=os.path.join(STATIC_DIR, "tasks", t.task_id, "full_report.json") if os.path.exists(os.path.join(STATIC_DIR, "tasks", t.task_id, "full_report.json")) else "",
            )
            for t in tasks
        ],
        count=count,
    )
