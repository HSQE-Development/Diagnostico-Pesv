from functools import wraps


def authenticated_user_exempt(view_func):
    """
    Decorator used to skip the AuthenticatedUser middleware.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        setattr(request, "_skip_authenticated_user", True)
        return view_func(request, *args, **kwargs)

    return _wrapped_view
