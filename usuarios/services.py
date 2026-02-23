#from usuarios.models import Usuario
from django.contrib.auth import get_user_model

def get_usuario_sistema():
    User = get_user_model()
    return User.objects.get(username="sistema")