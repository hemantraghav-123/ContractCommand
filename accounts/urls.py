from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("register/", views.register, name="register"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-code/", views.verify_code, name="verify_code"),
    path("", views.dashboard, name="dashboard"),
]
