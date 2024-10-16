from dataclasses import dataclass
from datetime import date
from typing import Union


@dataclass
class UserEntity:
    id: int
    password: str
    last_login: date | None
    is_superuser: bool
    username: str
    first_name: str
    last_name: str
    email: str
    is_staff: bool
    is_active: bool
    date_joined: date
    licensia_sst: str | None
    cedula: str
    avatar: str | None

    def get_full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_avatar(self) -> str | None:
        return self.avatar
