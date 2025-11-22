from django.urls import path
from .views import login_view, logout_view, inicio

app_name = "sesiones"

urlpatterns = [
    path("", inicio, name="inicio"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]

