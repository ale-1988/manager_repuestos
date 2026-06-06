import os

from .base_settings import *

ENTORNO = os.environ.get("MR_ENTORNO")

if ENTORNO is None:
    raise RuntimeError(
        "La variable de entorno MR_ENTORNO no está definida"
    )

ENTORNO = ENTORNO.upper()


if ENTORNO == "PROD":
    from .prod_settings import *
else:
    from .dev_settings import *

