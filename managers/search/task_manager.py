import uuid

from typing import List, Literal, Optional, Tuple

from fastapi import BackgroundTasks

from sqlalchemy import func
from sqlalchemy.future import select

from models.base import TaskStatus
from models.models import ParsingTasks
from models.session import get_session

from tasks.mass_search import mass_search


class ParsingTasksManager:
    def __init__(self, background_tasks: BackgroundTasks, user_id: int, task_id: str = ""):
        self.task_id = task_id
        if not self.task_id:
            self.task_id = uuid.uuid4().hex
        self.user_id = user_id
        self.background_tasks = background_tasks

    async def create(self) -> ParsingTasks:
        async with get_session() as s:
            parsing_task = ParsingTasks(task_id=self.task_id, filename=f"{self.task_id}.csv", status=TaskStatus.pending.value)
            s.add(parsing_task)
            await s.commit()
            return parsing_task

    async def get(self, pk: int) -> Optional[ParsingTasks]:
        async with get_session() as s:
            return (
                await s.execute(select(ParsingTasks).filter(ParsingTasks.id == pk))
            ).scalars().first()

    async def restart(self) -> Optional[ParsingTasks]:
        async with get_session() as s:
            parsing_task = (
                await s.execute(select(ParsingTasks).filter(ParsingTasks.task_id == self.task_id))
            ).scalars().first()
            if not parsing_task:
                return
            parsing_task.status = TaskStatus.pending.value
            await s.commit()
            return parsing_task

    async def start_task(self, action: Literal["create", "restart"] = "create") -> None:
        method = getattr(self, action, None)
        if not method:
            return
        parsing_task = await method()
        if not parsing_task:
            return
        self.background_tasks.add_task(
            mass_search,
            f"{self.task_id}.csv",
            "quickosint",
            self.user_id,
            self.task_id,
        )

    async def list_tasks(self, limit: int = 10, offset: int = 0) -> Tuple[List[ParsingTasks], int]:
        async with get_session() as s:
            tasks = (
                await s.execute(
                    select(ParsingTasks)
                    .limit(limit)
                    .offset(offset)
                    .order_by(ParsingTasks.created_at.desc())
                )
            ).scalars().all()
            tasks_count = (
                await s.execute(
                    select(func.count(ParsingTasks.id))
                )
            ).scalar()
            return tasks, tasks_count
