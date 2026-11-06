from .dca import DCA
from .tendencia import Tendencia

ESTRATEGIAS = {"dca": DCA, "tendencia": Tendencia}


def crear_estrategia(tipo: str, nombre: str, par: str, parametros: dict | None = None):
    if tipo not in ESTRATEGIAS:
        raise ValueError(f"Estrategia desconocida '{tipo}'. Opciones: {list(ESTRATEGIAS)}")
    return ESTRATEGIAS[tipo](nombre, par, parametros)
