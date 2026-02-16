from django.urls import path, reverse_lazy
from .views import login_view, logout_view, inicio
from django.contrib.auth import views as auth_views

app_name = "sesiones"

urlpatterns = [
    path("", inicio, name="inicio"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            success_url=reverse_lazy('sesiones:password_reset_done'),
        ),
        name='password_reset'
    ),
    path(
        'password_reset_done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url=reverse_lazy('sesiones:password_reset_complete'),
        ),    
        name='password_reset_confirm'
    ),
    path(
        'reset_done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
    
]

