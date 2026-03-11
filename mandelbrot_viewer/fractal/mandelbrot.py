"""
Motore di calcolo dell'insieme di Mandelbrot con NumPy vectorization.
"""
import numpy as np


def compute_mandelbrot(
    x_min: float, x_max: float,
    y_min: float, y_max: float,
    width: int, height: int,
    max_iter: int = 256,
    escape_radius: float = 2.0
) -> np.ndarray:
    """
    Calcola l'insieme di Mandelbrot per il dominio specificato.

    Algoritmo: z(n+1) = z(n)^2 + c, con z0 = 0
    Usa il "smooth iteration count" per colorazione continua.

    Returns:
        Array 2D float con valori di iterazione smooth [0, max_iter]
        0 = interno all'insieme, valori positivi = velocità di divergenza
    """
    # Griglia del piano complesso
    x = np.linspace(x_min, x_max, width, dtype=np.float64)
    y = np.linspace(y_min, y_max, height, dtype=np.float64)
    C = x[np.newaxis, :] + 1j * y[:, np.newaxis]

    Z = np.zeros_like(C)
    iteration_count = np.zeros(C.shape, dtype=np.float64)
    not_escaped = np.ones(C.shape, dtype=bool)

    escape_r2 = escape_radius * escape_radius

    for i in range(max_iter):
        # Itera solo i punti non ancora scappati
        Z[not_escaped] = Z[not_escaped] ** 2 + C[not_escaped]
        escaped_now = not_escaped & (Z.real ** 2 + Z.imag ** 2 > escape_r2)
        iteration_count[escaped_now] = i + 1
        not_escaped[escaped_now] = False
        if not not_escaped.any():
            break

    # Smooth coloring: normalizzazione continua per punti sfuggiti
    escaped_mask = iteration_count > 0
    if escaped_mask.any():
        # Calcola smooth iteration count usando il modulo finale
        abs_z = np.abs(Z[escaped_mask])
        abs_z = np.maximum(abs_z, 1.0 + 1e-10)  # evita log(0)
        smooth = iteration_count[escaped_mask] - np.log2(np.log2(abs_z))
        iteration_count[escaped_mask] = smooth

    return iteration_count
