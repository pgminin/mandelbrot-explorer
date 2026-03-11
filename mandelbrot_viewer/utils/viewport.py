"""
Gestione del viewport: trasformazioni tra coordinate schermo e piano complesso.
"""
from dataclasses import dataclass, field


@dataclass
class Viewport:
    """
    Rappresenta la finestra del piano complesso attualmente visibile.
    """
    x_min: float = -2.5
    x_max: float = 1.0
    y_min: float = -1.5
    y_max: float = 1.5

    # Limiti di zoom (per evitare overflow floating point)
    MAX_ZOOM_DEPTH: float = 1e-13

    def width(self) -> float:
        return self.x_max - self.x_min

    def height(self) -> float:
        return self.y_max - self.y_min

    def center(self):
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)

    def screen_to_complex(self, px: float, py: float, screen_w: int, screen_h: int):
        """Converte coordinate pixel in punto del piano complesso."""
        re = self.x_min + (px / screen_w) * self.width()
        im = self.y_min + (py / screen_h) * self.height()
        return re, im

    def zoom_at(self, px: float, py: float, screen_w: int, screen_h: int, factor: float):
        """
        Zoom centrato sul punto schermo (px, py).
        factor < 1 → zoom in, factor > 1 → zoom out
        """
        # Limita zoom massimo
        if self.width() * factor < self.MAX_ZOOM_DEPTH:
            return

        # Punto complesso sotto il cursore (deve restare fisso)
        cx, cy = self.screen_to_complex(px, py, screen_w, screen_h)

        new_w = self.width() * factor
        new_h = self.height() * factor

        # Mantieni la proporzione schermo → cursore nel nuovo viewport
        rel_x = px / screen_w
        rel_y = py / screen_h

        self.x_min = cx - rel_x * new_w
        self.x_max = self.x_min + new_w
        self.y_min = cy - rel_y * new_h
        self.y_max = self.y_min + new_h

    def pan(self, dx_px: float, dy_px: float, screen_w: int, screen_h: int):
        """
        Sposta il viewport di (dx_px, dy_px) pixel.
        """
        dx = dx_px / screen_w * self.width()
        dy = dy_px / screen_h * self.height()
        self.x_min -= dx
        self.x_max -= dx
        self.y_min -= dy
        self.y_max -= dy

    def reset(self):
        """Ripristina il dominio iniziale."""
        self.x_min = -2.5
        self.x_max = 1.0
        self.y_min = -1.5
        self.y_max = 1.5

    def zoom_level(self) -> float:
        """Fattore di zoom corrente rispetto alla vista iniziale."""
        initial_w = 3.5  # x_max - x_min iniziale
        return initial_w / self.width()
