from src.domain.core.constants import HTTP_VERB_GET, HTTP_VERB_POST
from src.domain.core.routing import Route, Router
from src.interface.routes.constants import USERS_PREFIX
from src.interface.controllers.authorize_controller import UserController

user_router = Router()
user_router.register(
    [
        Route(
            http_verb=HTTP_VERB_GET,
            path=rf"^{USERS_PREFIX}/<id:int>",
            controller=UserController,
            method="get",
            name="users_get",
        ),
        Route(
            http_verb=HTTP_VERB_GET,
            path=rf"^{USERS_PREFIX}/",
            controller=UserController,
            method="list",
            name="users_list",
        ),
    ]
)

auth_router = Router()
auth_router.register(
    [
        Route(
            http_verb=HTTP_VERB_POST,
            path=rf"^{USERS_PREFIX}/authenticate/",
            controller=UserController,
            method="authenticate",
            name="auth_authenticate",
        ),
        Route(
            http_verb=HTTP_VERB_POST,
            path=rf"^{USERS_PREFIX}/save",
            controller=UserController,
            method="save",
            name="auth_save",
        ),
    ]
)
