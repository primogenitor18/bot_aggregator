from sqladmin import ModelView

from models.models import User


class UserAdmin(ModelView, model=User):
    column_list = [User.username, User.blocked, User.role]
