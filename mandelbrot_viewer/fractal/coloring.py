"""
Sistema di colorazione continua per il frattale di Mandelbrot.
"""
import numpy as np


def _make_cosmic():
    """Palette 'inferno cosmico': viola → arancio → bianco."""
    stops = [
        (0.0,  (10,  2,  30)),
        (0.15, (90,  10, 120)),
        (0.35, (200, 50,  80)),
        (0.55, (240, 140,  20)),
        (0.75, (250, 220, 100)),
        (1.0,  (255, 255, 255)),
    ]
    return _build_lut(stops)


def _make_ocean():
    """Palette 'oceano': nero → blu → ciano → bianco."""
    stops = [
        (0.0,  (0,   0,  10)),
        (0.2,  (0,   30, 100)),
        (0.5,  (0,  100, 200)),
        (0.75, (50, 200, 230)),
        (1.0,  (220, 245, 255)),
    ]
    return _build_lut(stops)


def _make_fire():
    """Palette 'fuoco': nero → rosso → arancio → giallo."""
    stops = [
        (0.0,  (0,   0,   0)),
        (0.25, (120, 0,   0)),
        (0.5,  (220, 60,  0)),
        (0.75, (255, 160, 0)),
        (1.0,  (255, 255, 100)),
    ]
    return _build_lut(stops)


def _make_classic():
    """Palette classica bianco/nero con accenti blu."""
    stops = [
        (0.0,  (10,  20,  60)),
        (0.3,  (40,  80, 180)),
        (0.6,  (200, 220, 255)),
        (0.85, (255, 255, 255)),
        (1.0,  (80, 120, 200)),
    ]
    return _build_lut(stops)


def _make_neon():
    """Palette neon: nero → verde → magenta → cyan."""
    stops = [
        (0.0,  (0,   0,   0)),
        (0.2,  (0,  180,  50)),
        (0.45, (180,  0, 180)),
        (0.7,  (0,  200, 200)),
        (1.0,  (200, 255, 255)),
    ]
    return _build_lut(stops)


def _build_lut(stops, size=2048):
    """Costruisce una Look-Up Table RGB da una lista di color stops."""
    lut = np.zeros((size, 3), dtype=np.uint8)
    xs = np.linspace(0.0, 1.0, size)
    for channel in range(3):
        xp = [s[0] for s in stops]
        fp = [s[1][channel] for s in stops]
        lut[:, channel] = np.clip(np.interp(xs, xp, fp), 0, 255).astype(np.uint8)
    return lut


# Build LUTs at module load time
_LUT_CACHE = {name: factory() for name, factory in [
    ("Cosmic Inferno", _make_cosmic),
    ("Ocean", _make_ocean),
    ("Fire", _make_fire),
    ("Classic", _make_classic),
    ("Neon", _make_neon),
]}


def apply_colormap(iteration_data: np.ndarray, max_iter: int, palette: str = "Cosmic Inferno") -> np.ndarray:
    """
    Mappa i dati di iterazione in un'immagine RGB.

    Args:
        iteration_data: Array 2D con smooth iteration counts
        max_iter: Numero massimo di iterazioni (per normalizzazione)
        palette: Nome della palette da usare

    Returns:
        Array (H, W, 3) uint8 RGB
    """
    lut = _LUT_CACHE.get(palette, _LUT_CACHE["Cosmic Inferno"])
    lut_size = len(lut)

    # Normalizza in [0, 1]
    norm = np.zeros_like(iteration_data, dtype=np.float64)
    escaped = iteration_data > 0
    if escaped.any():
        vals = iteration_data[escaped]
        # Scala logaritmica per dettaglio visivo
        log_max = np.log1p(max_iter)
        norm[escaped] = np.clip(np.log1p(vals) / log_max, 0.0, 1.0)

    # Indici nella LUT
    indices = (norm * (lut_size - 1)).astype(np.int32)
    indices = np.clip(indices, 0, lut_size - 1)

    # Costruisce immagine RGB; i punti interni restano neri (indice 0 → colore scuro)
    rgb = lut[indices]
    return rgb


def get_palette_names():
    return list(_LUT_CACHE.keys())
