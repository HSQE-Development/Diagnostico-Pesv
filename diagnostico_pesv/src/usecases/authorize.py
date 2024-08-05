from typing import List
from src.domain.user import UserEntity
from src.interface.repositories.authorize import UserRepository


class UserInteractor:

    def __init__(self, user_repo: object):
        self.user_repo = user_repo

    def list_all(self) -> List[UserEntity]:
        return self.user_repo.list_all()

    def get(self, id: int) -> UserEntity:
        return self.user_repo.get(id)

    def save(self, user: UserEntity) -> UserEntity:
        return self.user_repo.save(user)

    def update(self, user: UserEntity) -> UserEntity:
        return self.user_repo.save(user)

    def delete(self, user: UserEntity):
        self.user_repo.delete(user)

    def get_user_by_email(self, email: str):
        return self.user_repo.get_user_by_email(email)

    def authenticate(self, email: str, password: str) -> UserEntity | None:
        user = self.user_repo.get_user_by_email(email)
        if not user.is_active:
            return None
        if not self.user_repo.check_password(user, password):
            return None
        return user

    def save(self, user_data: dict, groups: list) -> UserEntity:
        user_entity = UserEntity(
            id=0,
            username=user_data["username"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            is_active=user_data.get("is_active", True),
            licensia_sst=user_data.get("licensia_sst", None),
            cedula=user_data.get("cedula", ""),
            avatar=user_data.get("avatar", None),
            date_joined=None,
            is_staff=user_data.get("is_staff", False),
            is_superuser=user_data.get("is_superuser", False),
            last_login=user_data.get("last_login", None),
            password=None,
        )
        new_user = self.user_repo.save(user_entity)
        # if user_data["id"] != 0:
        self.user_repo.set_password(new_user, user_data["password"])
        self.user_repo.assign_groups(new_user, groups)

        return new_user
