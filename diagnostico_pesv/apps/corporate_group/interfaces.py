from abc import ABC, abstractmethod
from .models import Corporate


class ICorporateGroupRepository(ABC):
    @abstractmethod
    def get_by_id(self, id: int) -> Corporate | None:
        pass
