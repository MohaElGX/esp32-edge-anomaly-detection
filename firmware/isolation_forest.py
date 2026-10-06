"""
isolation_forest.py - Inferencia de Isolation Forest en MicroPython.

Calcula el score de anomalia de Liu et al. (2008) recorriendo los arboles
exportados por tools/export_iforest_upy.py (modulo generado `if_data`).
Solo usa `math`, asi que funciona igual en CPython; eso permite validar el
port contra scikit-learn (ver tests/test_port_fidelity.py).

    s(x) = 2 ** ( -E[h(x)] / c(PSI) )

    s cercano a 1   -> anomalia
    s muy por debajo de 0.5 -> normal
"""

import math
import if_data as _d

_EULER_GAMMA = 0.5772156649
_c_cache = {}


def _c(n):
    """
    Longitud media de camino para aislar n puntos en un BST sin entrenar.
    Corrige las hojas con mas de una muestra y normaliza el score.

        c(n) = 2*H(n-1) - 2*(n-1)/n,   H(i) ~= ln(i) + gamma

    Se cachea por n: las hojas solo contienen entre 1 y PSI muestras.
    """
    v = _c_cache.get(n)
    if v is None:
        if n <= 1:
            v = 0.0
        elif n == 2:
            v = 1.0
        else:
            v = 2.0 * (math.log(n - 1) + _EULER_GAMMA) - 2.0 * (n - 1) / n
        _c_cache[n] = v
    return v


_C_PSI = _c(_d.PSI)


def _path_length(tree_idx, x):
    """Recorre un arbol desde la raiz hasta una hoja."""
    feat = _d.FEAT[tree_idx]
    thr = _d.THR[tree_idx]
    left = _d.LEFT[tree_idx]
    right = _d.RIGHT[tree_idx]
    nsamp = _d.NSAMP[tree_idx]

    node = 0
    depth = 0
    # feat[node] == -2 marca una hoja (convencion de sklearn tree_.feature)
    while feat[node] != -2:
        if x[feat[node]] <= thr[node]:
            node = left[node]
        else:
            node = right[node]
        depth += 1
    return depth + _c(nsamp[node])


def anomaly_score(x):
    """Score s(x) en (0, 1]. `x` debe seguir el orden de if_data.FEATURES."""
    if len(x) != _d.N_FEATURES:
        raise ValueError("se esperaban %d features, llegaron %d"
                         % (_d.N_FEATURES, len(x)))
    total = 0.0
    for t in range(_d.N_TREES):
        total += _path_length(t, x)
    return 2.0 ** (-(total / _d.N_TREES) / _C_PSI)


def is_anomaly(x, threshold=None):
    """Decision binaria. Usa if_data.THRESHOLD si no se pasa umbral."""
    t = _d.THRESHOLD if threshold is None else threshold
    return anomaly_score(x) > t


def predict(x, threshold=None):
    """(score, es_anomalia) calculando el score una sola vez."""
    t = _d.THRESHOLD if threshold is None else threshold
    s = anomaly_score(x)
    return s, s > t
