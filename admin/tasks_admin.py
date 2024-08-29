from sqladmin import ModelView

from models.models import ParsingTasks


class ParsingTasksAdmin(ModelView, model=ParsingTasks):
    column_list = [ParsingTasks.task_id, ParsingTasks.status]
