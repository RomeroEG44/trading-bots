from .dca import DCA
from .rejilla import Rejilla
from .reversion import Reversion
from .ruptura import Ruptura
from .tendencia import Tendencia

ESTRATEGIAS = {"dca": DCA, "tendencia": Tendencia, "reversion": Reversion, "ruptura": Ruptura, "rejilla": Rejilla}


def crear_estrategia(tipo: str, nombre: str, par: str, parametros: dict | None = None):
    if tipo not in ESTRATEGIAS:
        raise ValueError(f"Estrategia desconocida '{tipo}'. Opciones: {list(ESTRATEGIAS)}")
    return ESTRATEGIAS[tipo](nombre, par, parametros)
