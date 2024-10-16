# coding: utf-8

from rest_framework.routers import SimpleRouter, Route

from src.interface.routes.authorize import user_router, auth_router
from src.infrastructure.factories.authorize import UserViewSetfactory


class UserRouter(SimpleRouter):
    routes = [
        Route(
            url=user_router.get_url("users_get"),
            mapping=user_router.map("users_get"),
            initkwargs={"viewset_factory": UserViewSetfactory},
            name="{basename}-get",
            detail=False,
        ),
        Route(
            url=user_router.get_url("users_list"),
            mapping=user_router.map("users_list"),
            initkwargs={"viewset_factory": UserViewSetfactory},
            name="{basename}-list",
            detail=False,
        ),
    ]


class AuthRouter(SimpleRouter):
    routes = [
        Route(
            url=auth_router.get_url("auth_authenticate"),
            mapping=auth_router.map("auth_authenticate"),
            initkwargs={"viewset_factory": UserViewSetfactory},
            name="{basename}-authenticate",
            detail=False,
        ),
        Route(
            url=auth_router.get_url("auth_save"),
            mapping=auth_router.map("auth_save"),
            initkwargs={"viewset_factory": UserViewSetfactory},
            name="{basename}-save",
            detail=False,
        ),
    ]
