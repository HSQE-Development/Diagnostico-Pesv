from src.infrastructure.orm.db.authorize.repositories import UserDatabaseRepository
from src.interface.repositories.authorize import UserRepository
from src.interface.controllers.authorize_controller import UserController
from src.usecases.authorize import UserInteractor


class UserDatabaseRepositoryFactory:
    @staticmethod
    def get() -> UserDatabaseRepository:
        return UserDatabaseRepository()


class UserRepositoryFactory:
    @staticmethod
    def get() -> UserRepository:
        db_repo = UserDatabaseRepositoryFactory.get()
        return UserRepository(db_repo)


class UserInteractorFactory:
    @staticmethod
    def get() -> UserInteractor:
        user_repo = UserRepositoryFactory.get()
        return UserInteractor(user_repo)


class UserViewSetfactory:
    @staticmethod
    def create() -> UserController:
        user_interactor = UserInteractorFactory.get()
        return UserController(user_interactor)
