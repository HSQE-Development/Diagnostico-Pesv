from typing import List, Union
from django.core.cache import cache
from src.domain.user import UserEntity
from src.infrastructure.orm.cache.user.constants import CACHE_AVAILABLE_USERS_KEY


class UserCacheRepository:

    def get(self, key: str) -> UserEntity:
        return cache.get(key)

    def get_availables(self) -> List[UserEntity]:
        return self.get(CACHE_AVAILABLE_USERS_KEY)

    def save(self, key: str, value: Union[UserEntity, list]):
        cache.set(key, value)

    def save_availables(self, users: List[UserEntity]):
        self.save(CACHE_AVAILABLE_USERS_KEY, users)
