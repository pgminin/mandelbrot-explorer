"""
Renderer: converte i dati del frattale in QImage per PyQt6.
"""
import numpy as np
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QSize

from fractal.mandelbrot import compute_mandelbrot
from fractal.coloring import apply_colormap
from utils.viewport import Viewport


class MandelbrotRenderer:
    """
    Gestisce il rendering del frattale: calcolo + colorazione → QImage.
    Supporta progressive rendering (bassa → alta risoluzione).
    """

    def __init__(self):
        self._cached_image: QImage | None = None
        self._last_params: dict | None = None

    def render(
        self,
        viewport: Viewport,
        width: int,
        height: int,
        max_iter: int,
        palette: str,
        escape_radius: float = 2.0,
        scale: float = 1.0,  # < 1 per preview rapido
    ) -> QImage:
        """
        Renderizza il frattale e restituisce una QImage.

        Args:
            scale: fattore di downscaling per rendering progressivo (0.25, 0.5, 1.0)
        """
        render_w = max(4, int(width * scale))
        render_h = max(4, int(height * scale))

        # Calcolo Mandelbrot
        iteration_data = compute_mandelbrot(
            viewport.x_min, viewport.x_max,
            viewport.y_min, viewport.y_max,
            render_w, render_h,
            max_iter=max_iter,
            escape_radius=escape_radius,
        )

        # Colorazione
        rgb = apply_colormap(iteration_data, max_iter, palette)

        # Crea QImage dal buffer RGB
        rgb_contiguous = np.ascontiguousarray(rgb, dtype=np.uint8)
        h, w, _ = rgb_contiguous.shape

        image = QImage(
            rgb_contiguous.data,
            w, h,
            w * 3,
            QImage.Format.Format_RGB888
        ).copy()  # .copy() per ownership del buffer

        # Se la scala è < 1, ingrandiamo l'immagine al size reale
        if scale < 1.0:
            image = image.scaled(
                width, height,
                aspectRatioMode=__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.AspectRatioMode.IgnoreAspectRatio,
                transformMode=__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.TransformationMode.FastTransformation,
            )

        self._cached_image = image
        return image

    def get_cached(self) -> QImage | None:
        return self._cached_image
