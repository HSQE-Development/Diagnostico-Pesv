from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from src.interface.controllers.authorize_controller import UserController
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from src.infrastructure.utils.authorize.utils import get_tokens_for_user
from src.infrastructure.utils.authorize.decorators import authenticated_user_exempt
from rest_framework import status as status_rest
from rest_framework_simplejwt.tokens import RefreshToken
from src.infrastructure.orm.db.authorize.models import User


class UserViewSet(ViewSet):
    viewset_factory = None
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @property
    def controller(self) -> UserController:
        return self.viewset_factory.create()

    def get(self, request: Request, id: int, *args, **kwargs) -> Response:
        payload, status = self.controller.get(id)
        return Response(data=payload, status=status)

    def list(self, request: Request, *args, **kwargs) -> Response:
        print("shasdhasdasd")
        payload, status = self.controller.list_all()
        return Response(data=payload, status=status)


class AuthorizeViewSet(ViewSet):
    viewset_factory = None
    authentication_classes = []
    permission_classes = []

    @property
    def controller(self) -> UserController:
        return self.viewset_factory.create()

    def authenticate(self, request: Request) -> Response:
        email = request.data["email"]
        password = request.data["password"]
        try:
            user_authenticated, status = self.controller.authenticate(email, password)
            refresh = get_tokens_for_user(user_authenticated)
            return Response(
                {"tokens": refresh, "user": user_authenticated}, status=status
            )
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status_rest.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def save(self, request: Request) -> Response:
        try:
            user_data = request.data
            groups = request.data.get("groups", [])
            user_created, status = self.controller.save(user_data, groups)
            print(user_created)
            # refresh = RefreshToken.for_user(user_created)
            # tokens = {
            #     "refresh": str(refresh),
            #     "access": str(refresh.access_token),
            # }
            tokens = {
                "refresh": "str(refresh)",
                "access": "str(refresh.access_token)",
            }
            return Response(
                {"tokens": tokens, "user": user_created},
                status=status,
            )
        except Exception as ex:
            return Response(
                {"error": str(ex)}, status=status_rest.HTTP_500_INTERNAL_SERVER_ERROR
            )
