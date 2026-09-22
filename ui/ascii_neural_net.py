"""
ui/ascii_neural_net.py - Widget de Asistente Red Neuronal 2D ASCII animada.

Renderiza un núcleo neural cibernético y visualización de capas de red neuronal en 2D
utilizando caracteres ASCII dinámicos, pulsos de sinapsis, métricas de inferencia y
estética cyberpunk / HUD reactiva con colores del tema activo.
"""

from __future__ import annotations

import math
import random
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout

from core.themes import ThemeManager


class AsciiNeuralNet(QWidget):
    """Visualizador 2D ASCII del núcleo neural de J.A.R.V.I.S."""

    def __init__(self, theme: ThemeManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme
        self._tick_count: int = 0
        self._status_text: str = "NÚCLEO NEURAL ACTIVO"
        self._synapse_activity: float = 0.85
        self._mode_name: str = "LISTO"

        self._setup_ui()

        # Timer interno para animación fluida de caracteres y pulsos (80ms ~ 12.5 fps)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_tick)
        self._anim_timer.start(80)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Contenedor para el arte ASCII central
        self._ascii_label = QLabel(self)
        self._ascii_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ascii_label.setTextFormat(Qt.TextFormat.PlainText)

        # Fuente monoespaciada para alineación perfecta de la matriz ASCII
        mono_font = QFont("Consolas", 10)
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        mono_font.setFamilies(["Consolas", "Courier New", "DejaVu Sans Mono", "monospace"])
        self._ascii_label.setFont(mono_font)

        layout.addWidget(self._ascii_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Barra inferior de telemetría neural
        self._telemetry_label = QLabel(self)
        self._telemetry_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tele_font = QFont("Consolas", 9)
        tele_font.setStyleHint(QFont.StyleHint.Monospace)
        self._telemetry_label.setFont(tele_font)
        layout.addWidget(self._telemetry_label, 0, Qt.AlignmentFlag.AlignCenter)

        self.refresh_theme()
        self._render_frame()

    def refresh_theme(self) -> None:
        them = self._theme.theme
        accent = them.accent
        dim = them.text_dim
        bg_card = them.card_bg
        border = them.card_border

        self.setStyleSheet(
            f"AsciiNeuralNet {{ background: transparent; }}"
        )
        self._ascii_label.setStyleSheet(
            f"background: transparent; color: {accent}; border: none; letter-spacing: 1px;"
        )
        self._telemetry_label.setStyleSheet(
            f"background: transparent; color: {dim}; border: none; letter-spacing: 2px;"
        )

    def set_status(self, status: str) -> None:
        self._status_text = status.upper()
        if "PENSANDO" in self._status_text or "INICIANDO" in self._status_text:
            self._synapse_activity = 1.0
        else:
            self._synapse_activity = 0.7

    def _on_tick(self) -> None:
        self._tick_count += 1
        self._render_frame()

    def _render_frame(self) -> None:
        t = self._tick_count * 0.15

        # Capas de la red: 4 nodos entrada, 6 nodos ocultos 1, 7 nodos ocultos 2, 5 nodos ocultos 3, 3 nodos salida
        # Representación 2D esquemática ASCII de sinapsis y tensores
        layers = [4, 6, 7, 5, 3]
        max_nodes = 7

        # Símbolos dinámicos de activación según energía / pulso sináptico
        pulse_syms = ["·", "•", "○", "◎", "●", "◆", "◇", "☼", "◈", "◉"]
        synapse_chars = ["─", "═", "━", "┄", "┈", "╴", "╸"]

        # Generar matriz de nodos interactivos
        rows = []
        rows.append("╭─── [ N E U R A L   C O R E   2 . D ] ───────────────────────────╮")
        rows.append("│                                                                 │")

        # Visualizar topología de 5 capas interconectadas con flujo de datos
        layer_names = ["INPUT [L0]", "HIDDEN [L1]", "DENSE [L2]", "ATTN [L3]", "OUTPUT [L4]"]
        header_row = f"│  {layer_names[0]:<11}  {layer_names[1]:<11}  {layer_names[2]:<11}  {layer_names[3]:<11}  {layer_names[4]:<11}│"
        rows.append(header_row)
        rows.append("│  ───────────  ───────────  ───────────  ───────────  ───────────│")

        for r in range(max_nodes):
            line_parts = ["│ "]
            for l_idx, count in enumerate(layers):
                offset = (max_nodes - count) // 2
                if offset <= r < offset + count:
                    node_idx = r - offset
                    # Pulso senoidal por nodo y capa
                    phase = t * 2.0 + (l_idx * 1.3) + (node_idx * 0.8)
                    wave = (math.sin(phase) + 1.0) / 2.0  # 0.0 a 1.0
                    
                    if wave > 0.8:
                        sym = "◈"
                    elif wave > 0.6:
                        sym = "◉"
                    elif wave > 0.4:
                        sym = "○"
                    elif wave > 0.2:
                        sym = "•"
                    else:
                        sym = "·"

                    weight_val = f"{wave:.2f}"
                    node_str = f"[{sym} {weight_val}]"
                else:
                    node_str = "         "

                line_parts.append(f" {node_str} ")

                if l_idx < len(layers) - 1:
                    # Conector sináptico animado entre capas
                    syn_phase = t * 3.0 + l_idx * 1.5 + r * 0.7
                    syn_active = (math.sin(syn_phase) + 1.0) / 2.0
                    if syn_active > 0.65:
                        con = "━━►"
                    elif syn_active > 0.35:
                        con = "───"
                    else:
                        con = "┄┄┄"
                    line_parts.append(con)

            line_parts.append(" │")
            rows.append("".join(line_parts))

        rows.append("│                                                                 │")
        
        # Animación del núcleo central de tensor
        cycle = int(t * 2) % 4
        bar_len = 24
        pos = int((math.sin(t * 1.8) * 0.5 + 0.5) * (bar_len - 4))
        bar = list("░" * bar_len)
        for b in range(pos, min(bar_len, pos + 4)):
            bar[b] = "█"
        bar_str = "".join(bar)
        
        hz = 42.8 + math.sin(t) * 1.2
        loss = 0.012 + math.sin(t * 0.8) * 0.003
        rows.append(f"│  SYNAPSE TENSOR: [{bar_str}]  INFER: {hz:.1f}Hz  LOSS: {loss:.4f} │")
        rows.append("╰─────────────────────────────────────────────────────────────────╯")

        self._ascii_label.setText("\n".join(rows))

        # Telemetría inferior
        status_dot = "●" if int(t * 3) % 2 == 0 else "○"
        self._telemetry_label.setText(
            f"{status_dot} {self._status_text}   |   NEURONS: 25   |   SYNAPSES: 136   |   PRECISION: FP16"
        )
