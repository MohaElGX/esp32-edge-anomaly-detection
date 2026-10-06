"""
Valida que el port a MicroPython (if_data + isolation_forest.py) reproduce
los scores y las decisiones de scikit-learn.
"""
import importlib
import sys

import numpy as np
import pytest
from sklearn.ensemble import IsolationForest

from export_iforest_upy import export_isolation_forest_micropython, update_threshold

FEATURES = ["HORA", "TEMP", "MOVIMIENTO", "HUMEDAD", "LUZ"]


@pytest.fixture(scope="module")
def trained():
    rng = np.random.RandomState(0)
    n = 4000
    X = np.column_stack([
        rng.randint(0, 24, n),
        rng.normal(24, 2, n).round(),
        rng.binomial(1, 0.2, n),
        rng.normal(55, 5, n).round(),
        rng.normal(1500, 500, n).round().clip(0, 4095),
    ]).astype(float)
    clf = IsolationForest(n_estimators=15, max_samples=256,
                          contamination=0.01, random_state=42).fit(X)
    return clf, X


@pytest.fixture()
def port(trained, tmp_path):
    clf, _ = trained
    out = tmp_path / "if_data.py"
    export_isolation_forest_micropython(clf, str(out), feature_names=FEATURES)
    sys.path.insert(0, str(tmp_path))
    for m in ("if_data", "isolation_forest"):
        sys.modules.pop(m, None)
    mod = importlib.import_module("isolation_forest")
    yield mod, out
    sys.path.remove(str(tmp_path))
    for m in ("if_data", "isolation_forest"):
        sys.modules.pop(m, None)


def test_scores_match_sklearn(trained, port):
    clf, X = trained
    mod, _ = port
    sk = -clf.score_samples(X[:500])
    ported = np.array([mod.anomaly_score(row.tolist()) for row in X[:500]])
    # float32 + redondeo a 6 decimales: se tolera algun punto en un borde de split
    close = np.abs(sk - ported) < 1e-4
    assert close.mean() > 0.99


def test_default_threshold_is_sklearn_offset(trained, port):
    clf, _ = trained
    import if_data
    assert abs(if_data.THRESHOLD - (-clf.offset_)) < 1e-6
    assert if_data.FEATURES == tuple(FEATURES)


def test_wrong_feature_count_raises(port):
    mod, _ = port
    with pytest.raises(ValueError):
        mod.anomaly_score([1, 2, 3])


def test_update_threshold(port):
    _, out = port
    update_threshold(str(out), 0.5)
    assert "THRESHOLD = 0.5\n" in out.read_text()
