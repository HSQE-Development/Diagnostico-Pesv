from src.domain.user import UserEntity
from typing import List


class UserRepository:
    def __init__(self, db_repo: object):
        self.db_repo = db_repo

    def list_all(self) -> List[UserEntity]:
        return self.db_repo.list_all()

    def get(self, id: int) -> UserEntity:
        user = self.db_repo.get(id)
        return user

    def get_user_by_email(self, email: str) -> UserEntity | None:
        return self.db_repo.get_user_by_email(email)

    def check_password(self, user: UserEntity, password: str) -> bool:
        return self.db_repo.check_password(user, password)

    def save(self, user: UserEntity) -> UserEntity:
        return self.db_repo.save(user)

    def set_password(self, user: UserEntity, password: str) -> None:
        return self.db_repo.set_password(user, password)

    def assign_groups(self, user: UserEntity, groups: list) -> None:
        return self.db_repo.assign_groups(user, groups)
