from sqladmin import ModelView

from models.models import Provider


class ProviderAdmin(ModelView, model=Provider):
    column_list = [Provider.name, Provider.accessed_role, Provider.auth_token]
