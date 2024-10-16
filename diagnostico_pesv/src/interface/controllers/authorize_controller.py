import logging
from http import HTTPStatus
from typing import Tuple

from src.usecases.authorize import UserInteractor
from src.interface.repositories.exceptions import EntityDoesNotExist
from src.interface.serializers.authorize_serializer import UserSerializer

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, user_interactor: UserInteractor):
        self.user_interactor = user_interactor

    def get(self, id: int) -> Tuple[dict, int]:
        try:
            user = self.user_interactor.get(id)
        except EntityDoesNotExist as err:
            logger.error("Failure retrieving %s user: %s", id, err.message)
            return {"error": err.message}, HTTPStatus.NOT_FOUND.value

        return UserSerializer().dump(user), HTTPStatus.OK.value

    def list(self) -> Tuple[list, int]:
        users = self.user_interactor.list_all()
        if not users:
            users = []
        return (UserSerializer(many=True).dump(users), HTTPStatus.OK.value)

    def authenticate(self, email: str, password: str) -> Tuple[dict, int]:
        try:
            user = self.user_interactor.authenticate(email, password)
        except EntityDoesNotExist as err:
            logger.error("Failure retrieving %s user: %s", email, err.message)
            return {"error": err.message}, HTTPStatus.NOT_FOUND.value
        return UserSerializer().dump(user), HTTPStatus.OK.value

    def save(self, user_data: dict, groups: list) -> Tuple[dict, int]:
        user = self.user_interactor.save(user_data, groups)
        return UserSerializer().dump(user), HTTPStatus.OK.value
