DEBUG = True

ALLOWED_HOSTS = ['localhost','192.168.100.20','127.0.0.1']

# ==================================================
# Limites de sesion
# ==================================================
# 1 horas
SESSION_COOKIE_AGE = 3600 
# Reinicia el contador con actividad del usuario
SESSION_SAVE_EVERY_REQUEST = False
# No cerrar al cerrar el navegador
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# ==================================================
# Protección contra fuerza bruta (django-axes)
# ==================================================
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_LOCKOUT_TEMPLATE = "sesiones/bloqueado.html"