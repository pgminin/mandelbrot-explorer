"""
Main window of the Mandelbrot Explorer.
Professional dark GUI with interactive canvas, English UI, 14pt+ fonts,
and a mathematical theory dialog.
"""
import os
import copy
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QPushButton, QComboBox, QStatusBar,
    QSizePolicy, QFileDialog, QFrame, QDialog,
    QScrollArea, QDialogButtonBox, QTextBrowser
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QPixmap, QImage, QFont

from fractal.coloring import get_palette_names
from rendering.renderer import MandelbrotRenderer
from utils.viewport import Viewport


# ─── Render worker (background thread) ───────────────────────────────────────

class RenderWorker(QThread):
    finished = pyqtSignal(QImage)

    def __init__(self, renderer, viewport, width, height, max_iter, palette, scale=1.0):
        super().__init__()
        self.renderer = renderer
        self.viewport = viewport
        self.width    = width
        self.height   = height
        self.max_iter = max_iter
        self.palette  = palette
        self.scale    = scale
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        if self._cancelled:
            return
        vp = copy.copy(self.viewport)
        img = self.renderer.render(
            vp, self.width, self.height,
            self.max_iter, self.palette, scale=self.scale
        )
        if not self._cancelled:
            self.finished.emit(img)


# ─── Interactive canvas ───────────────────────────────────────────────────────

class MandelbrotCanvas(QLabel):
    """Canvas widget handling mouse events and fractal display."""

    zoom_requested = pyqtSignal(float, float, float)
    pan_requested  = pyqtSignal(float, float)

    ZOOM_IN_FACTOR  = 0.35
    ZOOM_OUT_FACTOR = 1.0 / 0.35

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #050510;")
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._drag_last: QPoint | None = None

    def wheelEvent(self, event):
        delta  = event.angleDelta().y()
        factor = self.ZOOM_IN_FACTOR if delta > 0 else self.ZOOM_OUT_FACTOR
        pos    = event.position()
        self.zoom_requested.emit(pos.x(), pos.y(), factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_last = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drag_last is not None:
            dx = event.pos().x() - self._drag_last.x()
            dy = event.pos().y() - self._drag_last.y()
            self._drag_last = event.pos()
            self.pan_requested.emit(float(dx), float(dy))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_last = None
            self.setCursor(Qt.CursorShape.CrossCursor)


# ─── Stylesheet (base 14px / ~11pt, all interactive elements ≥ 14px) ─────────

DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #0d0d1a;
    color: #e0e0f0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 14px;
}
QLabel {
    color: #c0c0e0;
    font-size: 14px;
}
QPushButton {
    background-color: #1e1e3a;
    color: #a0c0ff;
    border: 1px solid #3040a0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2a2a55;
    border-color: #6080ff;
    color: #c0d8ff;
}
QPushButton:pressed {
    background-color: #3a3a70;
}
QComboBox {
    background-color: #1a1a30;
    color: #c0d0ff;
    border: 1px solid #3040a0;
    border-radius: 5px;
    padding: 5px 12px;
    font-size: 14px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a30;
    color: #c0d0ff;
    font-size: 14px;
    selection-background-color: #2a3580;
}
QSlider::groove:horizontal {
    height: 5px;
    background: #2a2a50;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    background: #5060d0;
    border: 1px solid #7080ff;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
}
QSlider::sub-page:horizontal {
    background: #4050c0;
    border-radius: 2px;
}
QStatusBar {
    background-color: #08081a;
    color: #7080b0;
    border-top: 1px solid #202040;
    font-size: 14px;
}
QScrollBar:vertical {
    background: #0d0d1a;
    width: 10px;
}
QScrollBar::handle:vertical {
    background: #2a2a55;
    border-radius: 5px;
    min-height: 20px;
}
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #202040;
}
"""

# ─── Mathematical theory content ──────────────────────────────────────────────

THEORY_HTML = """
<style>
  body  { background:#0d0d1a; color:#dde0ff;
          font-family:'Segoe UI',Arial,sans-serif;
          font-size:15px; line-height:1.8; margin:20px 28px; }
  h1    { color:#7080ff; font-size:24px; letter-spacing:1px; margin-bottom:6px; }
  h2    { color:#5090e0; font-size:18px; margin-top:32px; margin-bottom:8px;
          border-bottom:1px solid #1e2060; padding-bottom:5px; }
  h3    { color:#60b0d0; font-size:16px; margin-top:20px; }
  .tag  { display:inline-block; background:#1a1a40; color:#8090ff;
          border:1px solid #2a3080; border-radius:4px;
          padding:3px 12px; font-size:13px; margin-bottom:12px; }
  .math { background:#0a0a25; border-left:3px solid #4050c0;
          padding:12px 20px; margin:14px 0;
          font-family:'Courier New',monospace;
          font-size:15px; color:#a0c0ff; border-radius:0 6px 6px 0; }
  .box  { background:#12123a; border:1px solid #2a2a60;
          border-radius:8px; padding:16px 20px; margin:16px 0; }
  .fact { color:#80e0b0; font-weight:700; }
  ul    { padding-left:24px; margin:10px 0; }
  li    { margin-bottom:8px; }
  hr    { border:none; border-top:1px solid #1a1a40; margin:24px 0; }
  p     { margin:10px 0; }
</style>

<h1>&#128302; The Mandelbrot Set</h1>
<span class="tag">Complex Dynamics</span>
<span class="tag">Fractal Geometry</span>
<span class="tag">Chaos Theory</span>

<h2>1. The Core Iteration</h2>
<p>
The Mandelbrot set is defined by a deceptively simple rule.
For each point <b>c</b> in the complex plane, we start at zero and
repeatedly apply the quadratic map:
</p>
<div class="math">z&#8320; = 0
z&#8345;&#8331;&#8321; = z&#8345;&#178; + c</div>
<p>
A point <b>c</b> <em>belongs</em> to the Mandelbrot set if and only if
the sequence |z&#8345;| stays bounded forever &#8212; it never escapes to infinity.
In practice we use an <b>escape radius R = 2</b>: once |z&#8345;| &gt; 2,
the orbit is guaranteed to diverge, and <b>c</b> is outside the set.
</p>

<h2>2. Why the Complex Plane?</h2>
<p>
Complex numbers <b>c = a + bi</b> live in a 2-D plane, so the iteration
naturally produces a 2-D picture. The squaring operation z&#178; couples the
real and imaginary parts in a <em>non-linear</em> way:
</p>
<div class="math">z&#178; = (a + bi)&#178; = (a&#178; &#8722; b&#178;) + 2abi</div>
<p>
This non-linearity is the engine of the fractal's infinite complexity:
a tiny change in the starting point <b>c</b> can lead to completely
different long-term behaviour &#8212; the hallmark of <b>chaos</b>.
</p>

<h2>3. The Boundary: Where the Magic Lives</h2>
<div class="box">
<span class="fact">Key insight:</span> The interior (black region) is where
orbits stay bounded. The exterior is where they escape to infinity.
<b>All the fractal detail lives right on the boundary between the two.</b>
</div>
<p>Zoom into the boundary and you will find:</p>
<ul>
  <li>Infinite self-similar filaments and antenna-like decorations</li>
  <li>Miniature copies of the entire set (&#147;baby Mandelbrots&#148;) nested at every scale</li>
  <li>Spiral galaxies, lightning-bolt tendrils, and sea-horse valleys</li>
</ul>
<p>
This boundary has a <b>fractal dimension of exactly 2</b> &#8212; it is so
infinitely crinkled that it fills area rather than tracing a simple curve.
</p>

<h2>4. Smooth Colouring</h2>
<p>
Naive colouring assigns an integer iteration count <em>n</em> to each
escaping point, producing harsh colour bands.
This viewer uses the <b>smooth (continuous) iteration count</b> formula:
</p>
<div class="math">&#957; = n &#8722; log&#8322;( log&#8322;( |z&#8345;| ) )</div>
<p>
Since the orbit magnitude grows roughly as |z| &#8776; R<sup>n</sup>,
the double logarithm removes the discrete jumps and produces a seamless,
band-free gradient that reveals far more structure.
</p>

<h2>5. Connection to Julia Sets</h2>
<p>
For every complex parameter <b>c</b> there is a companion fractal called the
<b>Julia set J(c)</b>, generated by the same iteration but with c fixed
and z&#8320; varying across the plane.
</p>
<ul>
  <li>If <b>c</b> is <em>inside</em> the Mandelbrot set &#8594; J(c) is a connected, intricate shape</li>
  <li>If <b>c</b> is <em>outside</em> &#8594; J(c) shatters into a disconnected &#147;Cantor dust&#148;</li>
</ul>
<p>
The Mandelbrot set is therefore the <b>parameter space</b> of all Julia sets &#8212;
a single picture that encodes infinitely many fractals at once.
</p>

<h2>6. Self-Similarity and Scale Invariance</h2>
<p>
Zoom in by a factor of 10&#8312; and the set looks just as intricate as at scale 1.
This <b>scale invariance</b> is a mathematical consequence of the iteration
having the same form at every level of magnification.
The set is <b>statistically self-similar</b>: not perfectly periodic,
but statistically indistinguishable across scales &#8212; an infinitely
deep well of novelty.
</p>

<h2>7. Chaos Theory: the Fractal as a Map of Unpredictability</h2>
<p>
Chaos theory studies <b>deterministic systems whose long-term behaviour is
unpredictable</b> because it depends with extreme sensitivity on the initial
conditions. The map z &#8594; z&#178; + c is a textbook example.
</p>
<div class="box">
<span class="fact">Sensitive dependence on initial conditions:</span>
Take two points <b>c</b> and <b>c&#8217;</b> that are arbitrarily close together &#8212;
one just inside the boundary of the set, one just outside.
Their orbits diverge completely: one stays bounded forever, the other
escapes to infinity. No matter how small the separation, the long-term
outcome is opposite. This <em>is</em> chaos.
</div>
<p>
The infinitely jagged boundary is not merely a visual curiosity &#8212; it is the
<b>geometric signature of this sensitivity</b>. Here is why: if the boundary
were smooth, a small perturbation &#949; would produce a proportional, predictable
change in behaviour. But the system is chaotic, so no matter how small &#949; is,
you always find points on both sides of the boundary within distance &#949;.
The only geometry consistent with <em>infinite sensitivity at every point</em>
is an infinitely crinkled curve &#8212; a fractal. The jaggedness is therefore
not a cause of the chaos but its inevitable geometric consequence.
</p>
<p>
Importantly, chaos lives <b>on the boundary and outside it</b>, not inside.
The black interior is paradoxically the most orderly region: orbits there
converge to stable cycles and behave predictably. The boundary is the
exact frontier between order and chaos.
</p>

<h2>8. The Feigenbaum Connection: Period-Doubling and Universal Chaos</h2>
<p>
There is an even more explicit bridge to classical chaos theory.
If you slice the Mandelbrot set along the real axis (Im&nbsp;=&nbsp;0) and plot
how the stable orbit cycles change as <b>c</b> decreases from 0 to &#8722;2,
you recover the famous <b>period-doubling bifurcation diagram</b>:
</p>
<div class="math">period 1 &#8594; 2 &#8594; 4 &#8594; 8 &#8594; 16 &#8594; &#8230; &#8594; chaos</div>
<p id="bifurcation-anchor">
Each &#147;bulb&#148; branching off the main cardioid of the Mandelbrot set corresponds
to one of these doublings. The rate at which the bifurcations accumulate is
governed by the <b>Feigenbaum constant &#948; &#8776; 4.669</b>, discovered by
Mitchell Feigenbaum in 1975. Remarkably, this constant is <em>universal</em>:
it appears in every dynamical system that transitions to chaos through
period-doubling &#8212; from fluid turbulence and electronic oscillators to
heartbeat models and the logistic map of population biology.
</p>
<div class="box">
<span class="fact">The deeper unity:</span> The Mandelbrot set is not just
one fractal among many. It is the <b>complete parameter map</b> of all
quadratic complex maps &#8212; every point answers the question
&#147;is this system stable or chaotic?&#148; The boundary between the two answers
is infinitely complex because the transition from order to chaos
<em>never happens cleanly, at any scale</em>.
</div>

<h2>9. Why Is It So Fascinating?</h2>
<div class="box">
<ul>
  <li>&#127756; <b>Infinite complexity from a two-line formula</b> &#8212;
      arguably the most information ever encoded in such a short rule.</li>
  <li>&#128257; <b>Universality</b> &#8212; the same structure appears in population biology,
      fluid turbulence, electrical circuits, and financial time series.</li>
  <li>&#127807; <b>Connection to nature</b> &#8212; branching patterns identical to those in the set
      appear in coastlines, lightning, trees, blood vessels, and snowflakes.</li>
  <li>&#129518; <b>Open mathematics</b> &#8212; whether the Mandelbrot set is locally connected
      (the <em>MLC conjecture</em>) remains one of the great unsolved problems
      in complex dynamics.</li>
  <li>&#127912; <b>Aesthetic power</b> &#8212; the set was among the first mathematical objects
      to be called genuinely beautiful by non-mathematicians, bridging art and science.</li>
</ul>
</div>

<h2>10. Key Historical Milestones</h2>
<ul>
  <li><b>1905&#8211;1918</b> &#8212; Pierre Fatou and Gaston Julia study iterated complex maps,
      but lack computers to visualise them.</li>
  <li><b>1975</b> &#8212; Mitchell Feigenbaum discovers the universal constant &#948; &#8776; 4.669
      governing period-doubling routes to chaos.</li>
  <li><b>1978&#8211;1980</b> &#8212; Robert Brooks, Peter Matelski, and Beno&#238;t Mandelbrot
      produce the first computer plots of the set.</li>
  <li><b>1980</b> &#8212; Mandelbrot publishes the first detailed study at IBM Research.</li>
  <li><b>1982</b> &#8212; Mandelbrot coins the word <em>fractal</em> (from Latin
      <em>fractus</em> = broken, irregular).</li>
  <li><b>1985</b> &#8212; Adrien Douady and John H. Hubbard prove the set is connected
      and develop the rigorous mathematical framework.</li>
  <li><b>Today</b> &#8212; Deep zooms reaching 10<sup>2000</sup>&#215; are computed using
      arbitrary-precision arithmetic; the boundary remains inexhaustible.</li>
</ul>

<hr>
<p style="color:#404080; font-size:13px; text-align:center;">
  Use the scroll wheel to zoom &#183; Drag to pan &#183; The boundary is infinite &#8212; explore freely.
</p>
"""


class BifurcationDialog(QDialog):
    """
    Window showing the period-doubling bifurcation diagram for the real
    slice of the Mandelbrot set: z -> z^2 + c, c in [-2, 0.25], Im=0.
    Rendered with matplotlib embedded in a Qt canvas.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📈 Bifurcation Diagram — Real Slice of Mandelbrot Set")
        self.resize(1000, 620)
        self.setStyleSheet(DARK_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        # Title label
        title = QLabel("Period-Doubling Bifurcation Diagram  (z → z² + c,  Im = 0)")
        title.setStyleSheet("color:#7080ff; font-size:15px; font-weight:700;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Matplotlib canvas
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("QtAgg")

        self._fig, self._ax = plt.subplots(figsize=(11, 5.5))
        self._canvas = FigureCanvas(self._fig)
        layout.addWidget(self._canvas, stretch=1)

        # Status / hint
        hint = QLabel(
            "Each vertical slice shows the long-term orbit values for that value of c.  "
            "Vertical dashed lines mark the period-doubling bifurcation points."
        )
        hint.setStyleSheet("color:#5060a0; font-size:13px;")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

        # Render (slightly deferred so window appears first)
        QTimer.singleShot(50, self._render)

    def _render(self):
        from fractal.bifurcation import compute_bifurcation, BIFURCATION_POINTS

        ax = self._ax
        fig = self._fig

        # Dark background matching the app theme
        fig.patch.set_facecolor("#0a0a1a")
        ax.set_facecolor("#06060f")

        # Status message while computing
        ax.text(0.5, 0.5, "Computing…", transform=ax.transAxes,
                ha="center", va="center", color="#5060a0", fontsize=14)
        self._canvas.draw()

        # Compute
        c_vals, z_vals = compute_bifurcation(n_c=1400, n_transient=600, n_record=350)

        ax.cla()
        ax.set_facecolor("#06060f")

        # Main scatter — tiny dots, semi-transparent for density effect
        ax.scatter(c_vals, z_vals, s=0.08, c="#4a90d9", alpha=0.18, linewidths=0)

        # Bifurcation point annotations
        from fractal.bifurcation import BIFURCATION_POINTS
        colours = ["#ff6060", "#ff9040", "#ffd040", "#80e080", "#60d0d0"]
        for (label, cx), col in zip(BIFURCATION_POINTS.items(), colours):
            ax.axvline(x=cx, color=col, linewidth=0.9, alpha=0.75, linestyle="--")
            ax.text(cx + 0.012, 1.72, label, color=col,
                    fontsize=8.5, rotation=90, va="top", alpha=0.90)

        # Feigenbaum annotation
        chaos_c = BIFURCATION_POINTS["Chaos onset"]
        ax.annotate(
            "Chaos onset\n(Feigenbaum point\n≈ −1.4012)",
            xy=(chaos_c, 0), xytext=(chaos_c - 0.38, -1.55),
            color="#a0ffa0", fontsize=9,
            arrowprops=dict(arrowstyle="->", color="#a0ffa0", lw=1.2),
        )

        # Axes styling
        ax.set_xlabel("Parameter  c  (real axis)", color="#8090c0", fontsize=12)
        ax.set_ylabel("Orbit values  z  (after transient)", color="#8090c0", fontsize=12)
        ax.set_title(
            "Period-doubling route to chaos  ·  z → z² + c",
            color="#9090e0", fontsize=13, pad=10
        )
        ax.tick_params(colors="#5060a0", labelsize=10)
        for spine in ax.spines.values():
            spine.set_edgecolor("#2a2a50")
        ax.set_xlim(-2.05, 0.35)
        ax.set_ylim(-2.1, 2.1)
        ax.grid(color="#1a1a35", linewidth=0.5, alpha=0.6)

        # Period labels along the top
        period_regions = [
            ((-0.75, 0.25),  "Period 1",  "#c0c0ff"),
            ((-1.25, -0.75), "Period 2",  "#c0c0ff"),
            ((-1.368,-1.25), "Period 4",  "#c0c0ff"),
            ((-1.401,-1.368),"Period 8+", "#c0c0ff"),
            ((-2.0,  -1.401),"Chaos",     "#ff8080"),
        ]
        for (x0, x1), lbl, col in period_regions:
            mx = (x0 + x1) / 2
            ax.text(mx, 1.92, lbl, ha="center", color=col,
                    fontsize=9, alpha=0.85)

        fig.tight_layout()
        self._canvas.draw()


class TheoryDialog(QDialog):
    """Modal dialog with the mathematical theory of the Mandelbrot set."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📐 Mathematical Theory — Mandelbrot Set")
        self.resize(780, 680)
        self.setStyleSheet(DARK_STYLE + """
            QDialog { background-color: #0d0d1a; }
            QTextBrowser {
                background-color: #0d0d1a;
                border: none;
                font-size: 15px;
            }
            QDialogButtonBox QPushButton {
                min-width: 110px;
                padding: 8px 28px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(0)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(THEORY_HTML)
        browser.setFont(QFont("Segoe UI", 11))
        layout.addWidget(browser)

        # Bottom button row: bifurcation diagram + close
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(16, 0, 16, 0)
        btn_row.setSpacing(10)

        btn_bifurc = QPushButton("📈  Show Bifurcation Diagram")
        btn_bifurc.setStyleSheet(
            "background-color:#0a1e10; color:#60e090;"
            "border:1px solid #206040; font-size:14px; font-weight:600;"
            "padding:8px 20px;"
        )
        btn_bifurc.clicked.connect(lambda: BifurcationDialog(self).exec())

        btn_close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_close.rejected.connect(self.accept)

        btn_row.addWidget(btn_bifurc)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)


# ─── Main application window ──────────────────────────────────────────────────

class ViewerWindow(QMainWindow):
    """Main application window."""

    DEFAULT_MAX_ITER = 256
    DEFAULT_PALETTE  = "Cosmic Inferno"

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔬 Mandelbrot Explorer")
        self.resize(1160, 790)
        self.setStyleSheet(DARK_STYLE)

        self.viewport = Viewport()
        self.renderer = MandelbrotRenderer()
        self._worker: RenderWorker | None = None
        self._render_timer = QTimer()
        self._render_timer.setSingleShot(True)
        self._render_timer.timeout.connect(self._do_render)

        self._build_ui()
        self._schedule_render(delay_ms=50)

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.canvas = MandelbrotCanvas()
        self.canvas.zoom_requested.connect(self._on_zoom)
        self.canvas.pan_requested.connect(self._on_pan)
        root.addWidget(self.canvas, stretch=1)
        root.addWidget(self._build_side_panel())

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._lbl_coords = QLabel("Re: —   Im: —")
        self._lbl_zoom   = QLabel("Zoom: 1×")
        self.status.addWidget(self._lbl_coords, 1)
        self.status.addPermanentWidget(self._lbl_zoom)

        self.canvas.setMouseTracking(True)
        _orig = self.canvas.mouseMoveEvent
        def _track(event):
            _orig(event)
            self._update_coord_label(event.pos().x(), event.pos().y())
        self.canvas.mouseMoveEvent = _track

    def _build_side_panel(self) -> QWidget:
        panel = QWidget()
        panel.setFixedWidth(248)
        panel.setStyleSheet("background-color:#080815; border-left:1px solid #1a1a35;")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(14)

        # Title
        title = QLabel("MANDELBROT\nEXPLORER")
        title.setStyleSheet(
            "color:#6070e0; font-size:16px; font-weight:700; letter-spacing:1px;"
        )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(self._sep())

        # Max iterations
        layout.addWidget(self._lbl("Max Iterations"))
        iter_row = QHBoxLayout()
        self._iter_slider = QSlider(Qt.Orientation.Horizontal)
        self._iter_slider.setRange(32, 2048)
        self._iter_slider.setValue(self.DEFAULT_MAX_ITER)
        self._iter_val_lbl = QLabel(str(self.DEFAULT_MAX_ITER))
        self._iter_val_lbl.setFixedWidth(46)
        self._iter_val_lbl.setStyleSheet("color:#8090ff; font-weight:700; font-size:14px;")
        self._iter_slider.valueChanged.connect(lambda v: (
            self._iter_val_lbl.setText(str(v)),
            self._schedule_render(delay_ms=400)
        ))
        iter_row.addWidget(self._iter_slider)
        iter_row.addWidget(self._iter_val_lbl)
        layout.addLayout(iter_row)

        layout.addWidget(self._sep())

        # Colour palette
        layout.addWidget(self._lbl("Colour Palette"))
        self._palette_combo = QComboBox()
        self._palette_combo.addItems(get_palette_names())
        self._palette_combo.setCurrentText(self.DEFAULT_PALETTE)
        self._palette_combo.currentTextChanged.connect(
            lambda _: self._schedule_render(delay_ms=100)
        )
        layout.addWidget(self._palette_combo)

        layout.addWidget(self._sep())

        # Viewport info
        self._zoom_info = QLabel("Zoom: 1×\n\nRe: [-2.5, 1.0]\nIm: [-1.5, 1.5]")
        self._zoom_info.setStyleSheet("color:#5060a0; font-size:13px;")
        self._zoom_info.setWordWrap(True)
        layout.addWidget(self._zoom_info)

        layout.addWidget(self._sep())

        # Navigation
        for label, slot in [
            ("↺   Reset View",  self._on_reset),
            ("🔍+  Zoom In",    lambda: self._zoom_center(0.35)),
            ("🔍−  Zoom Out",   lambda: self._zoom_center(1 / 0.35)),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            layout.addWidget(btn)

        layout.addWidget(self._sep())

        # Theory button (highlighted)
        btn_theory = QPushButton("📐  Mathematical Theory")
        btn_theory.setStyleSheet(
            "background-color:#0e1e3a; color:#70b0ff;"
            "border:1px solid #204080; font-size:14px; font-weight:600;"
        )
        btn_theory.clicked.connect(self._on_show_theory)
        layout.addWidget(btn_theory)

        # Screenshot
        btn_shot = QPushButton("📷  Save Screenshot")
        btn_shot.clicked.connect(self._on_screenshot)
        layout.addWidget(btn_shot)

        layout.addStretch()

        hint = QLabel("Scroll wheel \u2192 zoom\nDrag \u2192 pan the fractal")
        hint.setStyleSheet("color:#2a2a60; font-size:13px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        return panel

    def _lbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#9090c0; font-size:14px;")
        return lbl

    def _sep(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:#1a1a35;")
        return line

    # ── Rendering ────────────────────────────────────────────────────────────

    def _schedule_render(self, delay_ms: int = 150):
        self._render_timer.start(delay_ms)

    def _do_render(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
        w, h = self.canvas.width(), self.canvas.height()
        if w < 4 or h < 4:
            return
        self._start_worker(w, h,
                           self._iter_slider.value(),
                           self._palette_combo.currentText(),
                           scale=0.25, is_preview=True)

    def _start_worker(self, w, h, max_iter, palette, scale, is_preview):
        vp = copy.copy(self.viewport)
        worker = RenderWorker(self.renderer, vp, w, h, max_iter, palette, scale)
        if is_preview:
            worker.finished.connect(
                lambda img: self._on_preview_done(img, w, h, max_iter, palette)
            )
        else:
            worker.finished.connect(self._on_render_done)
        worker.start()
        self._worker = worker

    def _on_preview_done(self, img, w, h, max_iter, palette):
        self._show_image(img)
        vp = copy.copy(self.viewport)
        worker = RenderWorker(self.renderer, vp, w, h, max_iter, palette, scale=1.0)
        worker.finished.connect(self._on_render_done)
        worker.start()
        self._worker = worker

    def _on_render_done(self, img):
        self._show_image(img)
        self._update_zoom_info()

    def _show_image(self, img):
        px = QPixmap.fromImage(img).scaled(
            self.canvas.width(), self.canvas.height(),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation,
        )
        self.canvas.setPixmap(px)

    # ── Interactions ──────────────────────────────────────────────────────────

    def _on_zoom(self, px, py, factor):
        self.viewport.zoom_at(px, py, self.canvas.width(), self.canvas.height(), factor)
        self._schedule_render(delay_ms=80)

    def _on_pan(self, dx, dy):
        self.viewport.pan(dx, dy, self.canvas.width(), self.canvas.height())
        self._schedule_render(delay_ms=50)

    def _on_reset(self):
        self.viewport.reset()
        self._schedule_render(delay_ms=50)

    def _zoom_center(self, factor):
        self._on_zoom(self.canvas.width() / 2, self.canvas.height() / 2, factor)

    def _on_show_theory(self):
        TheoryDialog(self).exec()

    def _on_screenshot(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", "mandelbrot.png",
            "PNG Images (*.png);;JPEG Images (*.jpg)"
        )
        if path:
            w, h = self.canvas.width(), self.canvas.height()
            img = self.renderer.render(
                copy.copy(self.viewport), w, h,
                self._iter_slider.value(),
                self._palette_combo.currentText(),
                scale=2.0,
            )
            img.scaled(w, h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ).save(path)
            self.status.showMessage(f"Screenshot saved: {path}", 4000)

    # ── UI updates ────────────────────────────────────────────────────────────

    def _update_coord_label(self, px, py):
        re, im = self.viewport.screen_to_complex(
            px, py, self.canvas.width(), self.canvas.height()
        )
        sign = "+" if im >= 0 else ""
        self._lbl_coords.setText(f"c = {re:.8f} {sign}{im:.8f}i")

    def _update_zoom_info(self):
        z  = self.viewport.zoom_level()
        vp = self.viewport
        if z >= 1e6:
            z_str = f"{z:.2e}x"
        elif z >= 1000:
            z_str = f"{z:,.0f}x"
        else:
            z_str = f"{z:.2f}x"
        self._lbl_zoom.setText(f"Zoom: {z_str}")
        self._zoom_info.setText(
            f"Zoom: {z_str}\n\n"
            f"Re: [{vp.x_min:.6g}, {vp.x_max:.6g}]\n"
            f"Im: [{vp.y_min:.6g}, {vp.y_max:.6g}]"
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_render(delay_ms=200)
