"""
Bifurcation diagram for the real slice of the Mandelbrot set.

Along the real axis (Im = 0), the map z -> z^2 + c with c in [-2, 0.25]
is equivalent to the real quadratic family. For each value of c we iterate
to let transients die out, then record the subsequent orbit values.
The resulting plot is the famous period-doubling bifurcation diagram and
reveals exactly how the system transitions from order to chaos.
"""
import numpy as np


def compute_bifurcation(
    c_min: float = -2.0,
    c_max: float = 0.25,
    n_c: int = 1400,
    n_transient: int = 500,
    n_record: int = 300,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the bifurcation diagram by iterating z -> z^2 + c on the real line.

    For each c value:
      - Run n_transient iterations to discard transient behaviour
      - Record the next n_record orbit values

    Returns:
        (c_vals, z_vals): paired arrays of (c, z) points to scatter-plot.
    """
    c_arr = np.linspace(c_min, c_max, n_c)

    # Vectorised over all c simultaneously
    z = np.zeros(n_c)

    # Burn-in: discard transients
    for _ in range(n_transient):
        z = z * z + c_arr
        # Keep z bounded to avoid overflow in diverging orbits
        z = np.clip(z, -3.0, 3.0)

    # Record orbit points
    c_out = []
    z_out = []
    for _ in range(n_record):
        z = z * z + c_arr
        z = np.clip(z, -3.0, 3.0)
        c_out.append(c_arr.copy())
        z_out.append(z.copy())

    return np.concatenate(c_out), np.concatenate(z_out)


# Known period-doubling bifurcation points (c values on the real axis)
BIFURCATION_POINTS = {
    "Period 1→2":  -0.75,
    "Period 2→4":  -1.25,
    "Period 4→8":  -1.3681,
    "Period 8→16": -1.3940,
    "Chaos onset": -1.4012,   # accumulation point ≈ -1.401155...
}

FEIGENBAUM_DELTA = 4.669201609  # universal constant governing period-doubling rate
