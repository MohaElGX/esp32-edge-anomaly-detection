"""
export_iforest_upy.py - Exporta un sklearn IsolationForest entrenado a un
modulo MicroPython (`if_data.py`) basado en arrays compactos.

Uso (desde el notebook o un script):

    from export_iforest_upy import export_isolation_forest_micropython
    export_isolation_forest_micropython(clf, "firmware/if_data.py",
                                        feature_names=["HORA", "TEMP", ...])

Despues, sube a la placa: if_data.py (o if_data.mpy), isolation_forest.py.
"""

import re


def export_isolation_forest_micropython(clf, out_path="if_data.py",
                                        threshold=None, feature_names=None):
    """
    clf:           sklearn.ensemble.IsolationForest ya entrenado.
    out_path:      archivo .py de salida.
    threshold:     umbral sobre el score s(x) en (0, 1]. Si es None se usa
                   -clf.offset_, que es el que implementa sklearn con
                   `contamination`. Conviene recalibrarlo con
                   update_threshold() porque el port usa float32 y
                   redondeo a 6 decimales.
    feature_names: nombres de las columnas, en el orden de entrenamiento.
    """
    if threshold is None:
        threshold = -float(clf.offset_)

    estimators = clf.estimators_
    n_features = int(clf.n_features_in_)
    psi = int(clf.max_samples_)
    if feature_names is not None and len(feature_names) != n_features:
        raise ValueError("feature_names no coincide con n_features_in_")

    lines = [
        "# Auto-generado por tools/export_iforest_upy.py. No editar a mano.",
        "from array import array",
        "",
        f"N_TREES = {len(estimators)}",
        f"N_FEATURES = {n_features}",
        f"PSI = {psi}",
        f"THRESHOLD = {round(float(threshold), 6)}",
    ]
    if feature_names is not None:
        lines.append(f"FEATURES = {tuple(feature_names)!r}")
    lines.append("")

    names = {"FEAT": [], "THR": [], "LEFT": [], "RIGHT": [], "NSAMP": []}
    total_nodes = 0

    for i, est in enumerate(estimators):
        tree = est.tree_
        n_nodes = len(tree.feature)
        total_nodes += n_nodes
        # Limites de los tipos de array elegidos
        assert n_nodes < 2**15, "demasiados nodos para array('h')"
        assert int(tree.n_node_samples.max()) < 2**16, "n_node_samples excede array('H')"

        # 'h' int16 con signo (-2 marca hoja) | 'f' float32 | 'H' uint16
        cols = {
            "FEAT": ("h", [int(v) for v in tree.feature]),
            "THR": ("f", [round(float(v), 6) for v in tree.threshold]),
            "LEFT": ("h", [int(v) for v in tree.children_left]),
            "RIGHT": ("h", [int(v) for v in tree.children_right]),
            "NSAMP": ("H", [int(v) for v in tree.n_node_samples]),
        }
        for key, (code, values) in cols.items():
            var = f"_{key.lower()}_{i}"
            lines.append(f"{var} = array('{code}', {tuple(values)})")
            names[key].append(var)
        lines.append("")

    for key, vars_ in names.items():
        lines.append(f"{key} = ({', '.join(vars_)})")

    with open(out_path, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    est_ram = total_nodes * 12      # 2 + 4 + 2 + 2 + 2 bytes por nodo
    print(f"Exportados {len(estimators)} arboles, {total_nodes} nodos.")
    print(f"RAM estimada de los arrays: ~{est_ram / 1024:.1f} KB")
    print(f"Umbral inicial: {round(float(threshold), 6)}")
    print(f"Archivo: {out_path}")


def update_threshold(path, threshold):
    """Reescribe la constante THRESHOLD de un if_data.py ya generado."""
    with open(path, newline="") as f:
        src = f.read()
    new, n = re.subn(r"^THRESHOLD = .*$", f"THRESHOLD = {round(float(threshold), 6)}",
                     src, flags=re.M)
    if n != 1:
        raise ValueError("no se encontro exactamente una linea THRESHOLD")
    with open(path, "w", newline="") as f:
        f.write(new)
    print(f"THRESHOLD actualizado a {round(float(threshold), 6)} en {path}")
