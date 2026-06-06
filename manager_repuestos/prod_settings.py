DEBUG = False

ALLOWED_HOSTS = ["movete.ar","www.movete.ar",]

# ==================================================
# Limites de sesion
# ==================================================
SESSION_COOKIE_AGE = 7200
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ==================================================
# Protección contra fuerza bruta (django-axes)
# ==================================================
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_RESET_ON_SUCCESS = True
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True
AXES_LOCKOUT_TEMPLATE = "sesiones/bloqueado.html"

# ==================================================
# movete.ar ya responed por https
# ==================================================
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# ==================================================
# 
# ==================================================
CSRF_TRUSTED_ORIGINS = [
    "https://movete.ar",
    "https://www.movete.ar",
]

# ==================================================
# Cabeceras de seguridad
# ==================================================
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ==================================================
# Si todo funciona por https
# ==================================================
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# ==================================================
# 
# ==================================================
SECURE_REFERRER_POLICY = "same-origin"

# ==================================================
# Logging
# ==================================================
# LOGGING = 