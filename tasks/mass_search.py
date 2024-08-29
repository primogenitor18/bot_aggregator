import os
import json
import aiofiles
from aiocsv import AsyncReader

from sqlalchemy import update
from sqlalchemy.future import select

from models.base import TaskStatus
from models.models import ParsingTasks, User
from models.session import get_session

from managers.search.manager import SearchManager

from config import STATIC_DIR


async def mass_search(
    filename: str,
    provider: str,
    user_id: int,
    task_id: str,
):
    async with get_session() as s:
        try:
            user = (
                await s.execute(select(User).filter(User.id == user_id))
            ).scalars().first()
            if not user:
                return
            manager = SearchManager(s, user)
            os.makedirs(os.path.join(STATIC_DIR, "tasks", task_id, "report"), exist_ok=True)
            async with aiofiles.open(
                os.path.join(STATIC_DIR, "tasks", task_id, filename),
                mode="r",
                encoding="utf-8",
                newline="",
            ) as afp:
                reader = AsyncReader(afp)
                async for row in reader:
                    if reader.line_num < 2:
                        continue
                    res, st = await manager.search(row[0], provider, row[1], row[2])
                    async with aiofiles.open(
                        os.path.join(STATIC_DIR, "tasks", task_id, "report", f"{row[0]}.json"),
                        mode="w",
                        encoding="utf-8",
                        newline="",
                    ) as afp:
                        await afp.write(json.dumps(res))
        except Exception:
            await s.execute(update(ParsingTasks).where(ParsingTasks.task_id == task_id).values(status=TaskStatus.failed.value))
        else:
            await s.execute(update(ParsingTasks).where(ParsingTasks.task_id == task_id).values(status=TaskStatus.success.value))
        finally:
            await s.commit()
