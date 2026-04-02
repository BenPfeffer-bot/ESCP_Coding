"""
Extraire les discount factors Z(0, T) à partir des taux swap par.

On va utiliser la théorie appliqué dans le livre de Wilmott & Jha:
    Z(0, T_1) = 1 / (1 + r_s(T_1) * tau_1)
    Z(0, T_{j+1}) = (1 - r_s * tau * sum Z_i) / (1 + r_s * tau_j)
"""
import numpy as np
from settings import get_logger

logger = get_logger(name="Bootsrapper")
logger.info("test")

def bootstrap_discount_factors(maturities:np.ndarray):
    pass
