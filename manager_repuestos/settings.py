import os

from .base_settings import *

ENTORNO = os.environ.get("MR_ENTORNO", "DEV")

if ENTORNO.upper() == "PROD":
    from .prod_settings import *
else:
    from .dev_settings import *