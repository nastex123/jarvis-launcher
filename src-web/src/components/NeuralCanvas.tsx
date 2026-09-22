"use client";

import { useEffect, useRef } from "react";
import { Application, Text, TextStyle } from "pixi.js";

interface NeuralCanvasProps {
  isThinking?: boolean;
}

export default function NeuralCanvas({ isThinking = false }: NeuralCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const appRef = useRef<Application | null>(null);
  const isThinkingRef = useRef(isThinking);

  // Mantener la referencia actualizada sin forzar re-montaje de PixiJS
  useEffect(() => {
    isThinkingRef.current = isThinking;
  }, [isThinking]);

  useEffect(() => {
    let isMounted = true;

    async function initPixi() {
      if (!containerRef.current) return;

      const app = new Application();
      await app.init({
        resizeTo: containerRef.current,
        backgroundAlpha: 0,
        antialias: true,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
      });

      if (!isMounted) {
        app.destroy(true, { children: true });
        return;
      }

      containerRef.current.appendChild(app.canvas);
      appRef.current = app;

      const stage = app.stage;

      // Estilo de texto monoespaciado para la matriz ASCII gigante a pantalla completa
      const asciiStyle = new TextStyle({
        fontFamily: ["JetBrains Mono", "SF Mono", "Consolas", "Courier New", "monospace"],
        fontSize: 12,
        lineHeight: 14,
        letterSpacing: 3,
        fill: 0x52525b, // Gris carbón atenuado en reposo
        align: "center",
      });

      const asciiText = new Text({
        text: "",
        style: asciiStyle,
      });
      stage.addChild(asciiText);

      // Tabla de luminancia ASCII estándar (orden de densidad)
      const asciiRamp = " .,-~:;=!*#$@";

      let A = 0; // Rotación eje X
      let B = 0; // Rotación eje Z/Y
      let mouseX = 0;
      let mouseY = 0;

      const onMouseMove = (e: MouseEvent) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.4;
        mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 0.4;
      };
      window.addEventListener("mousemove", onMouseMove);

      // Observador de cambio de tamaño dinámico para reaccionar al redimensionamiento del chat
      const resizeObserver = new ResizeObserver(() => {
        if (containerRef.current && appRef.current?.renderer) {
          const newW = containerRef.current.clientWidth;
          const newH = containerRef.current.clientHeight;
          if (newW > 0 && newH > 0) {
            appRef.current.renderer.resize(newW, newH);
          }
        }
      });
      if (containerRef.current) {
        resizeObserver.observe(containerRef.current);
      }

      let transitionProgress = 0; // 0 = reposo (esfera), 1 = pensando (vórtice)

      app.ticker.add((ticker) => {
        // Interpolación continua suave a lo largo de ~1.2 segundos (60 FPS = 72 frames)
        const targetProgress = isThinkingRef.current ? 1 : 0;
        const lerpSpeed = 0.022; // ~1.2s para convergencia completa
        transitionProgress += (targetProgress - transitionProgress) * lerpSpeed;

        // Velocidad ultralenta fija (zen: 0.003), y en pensamiento ritmo pausado y fluido (0.007)
        const mouseSpeed = (Math.abs(mouseX) + Math.abs(mouseY)) * 0.015;
        const currentSpeed = 0.003 + transitionProgress * 0.004 + mouseSpeed;
        const delta = ticker.deltaTime * currentSpeed;
        A += delta * 0.7 + mouseY * 0.005;
        B += delta * 1.0 + mouseX * 0.005;

        const screenW = app.screen.width;
        const screenH = app.screen.height;

        // Ancho y alto de celda de texto tipográfica (font 12px con letterSpacing)
        const cellW = 10;
        const cellH = 15;
        const aspectCorrection = cellH / cellW; // ~1.5 compensación geométrica para círculo perfecto

        const cols = Math.floor(screenW / cellW);
        const rows = Math.floor(screenH / cellH);

        const b: string[] = new Array(cols * rows).fill(" ");
        const z: number[] = new Array(cols * rows).fill(0);

        const cosA = Math.cos(A), sinA = Math.sin(A);
        const cosB = Math.cos(B), sinB = Math.sin(B);

        // Parámetros de morphing
        const t = transitionProgress; // Factor de mezcla [0, 1]
        const easeT = t * t * (3 - 2 * t); // Smoothstep cúbico

        // 1. Trazado de Esfera con Dispersión Morphing hacia Vórtice
        if (easeT < 0.98) {
          const sphereWeight = 1 - easeT;
          const tilt = 0.26;
          const cosTilt = Math.cos(tilt), sinTilt = Math.sin(tilt);
          const rotY = B;
          const cosR = Math.cos(rotY), sinR = Math.sin(rotY);

          // Radio base que se expande hacia el exterior durante la dispersión
          const sphereRadius = rows * (0.44 + easeT * 0.25);
          const K2 = sphereRadius * 2.8;

          const numMeridians = 8;
          const numParallels = 7;

          // Paralelos con dispersión radial
          for (let p = 1; p < numParallels; p++) {
            const lat = (p / numParallels) * Math.PI - Math.PI / 2;
            const cosLat = Math.cos(lat);
            const sinLat = Math.sin(lat);
            const rRing = sphereRadius * cosLat;
            const yBase = sphereRadius * sinLat;

            for (let lon = 0; lon < 6.28; lon += 0.09) {
              const cosLon = Math.cos(lon);
              const sinLon = Math.sin(lon);

              // Espiral de dispersión durante el morphing
              const morphAngle = easeT * Math.PI * 1.5;
              const effLon = lon + morphAngle;

              const pX0 = rRing * (Math.sin(effLon) * cosR + Math.cos(effLon) * sinR);
              const pZ0 = rRing * (Math.cos(effLon) * cosR - Math.sin(effLon) * sinR);
              const pY0 = yBase * (1 - easeT * 0.4);

              const pY = pY0 * cosTilt - pZ0 * sinTilt;
              const pZ = pY0 * sinTilt + pZ0 * cosTilt;

              if (pZ > -10 * easeT) {
                const zCoord = pZ + K2;
                const ooz = 1 / Math.max(1, zCoord);
                const xp = Math.floor(cols / 2 + (pX0 * ooz) * (K2 * aspectCorrection));
                const yp = Math.floor(rows / 2 + (pY * ooz) * K2);

                if (xp >= 0 && xp < cols && yp >= 0 && yp < rows) {
                  const idx = xp + yp * cols;
                  if (ooz > z[idx]) {
                    z[idx] = ooz;
                    b[idx] = easeT > 0.4 ? "·" : "-";
                  }
                }
              }
            }
          }

          // Meridianos con torsión morfológica
          for (let m = 0; m < numMeridians; m++) {
            const lon = (m / numMeridians) * Math.PI * 2;

            for (let lat = -Math.PI / 2 + 0.15; lat <= Math.PI / 2 - 0.15; lat += 0.08) {
              const cosLat = Math.cos(lat);
              const sinLat = Math.sin(lat);

              const morphTwist = easeT * lat * 2.0;
              const effLon = lon + morphTwist;

              const baseX = sphereRadius * cosLat * Math.sin(effLon);
              const baseZ = sphereRadius * cosLat * Math.cos(effLon);
              const baseY = sphereRadius * sinLat * (1 - easeT * 0.4);

              const pX = baseX * cosR + baseZ * sinR;
              const pZ0 = baseZ * cosR - baseX * sinR;
              const pY0 = baseY;

              const pY = pY0 * cosTilt - pZ0 * sinTilt;
              const pZ = pY0 * sinTilt + pZ0 * cosTilt;

              if (pZ > -10 * easeT) {
                const zCoord = pZ + K2;
                const ooz = 1 / Math.max(1, zCoord);
                const xp = Math.floor(cols / 2 + (pX * ooz) * (K2 * aspectCorrection));
                const yp = Math.floor(rows / 2 + (pY * ooz) * K2);

                if (xp >= 0 && xp < cols && yp >= 0 && yp < rows) {
                  const idx = xp + yp * cols;
                  if (ooz > z[idx]) {
                    z[idx] = ooz;
                    b[idx] = easeT > 0.4 ? "+" : "|";
                  }
                }
              }
            }
          }
        }

        // 2. Trazado del Vórtice Concéntrico con Emergencia Progresiva
        if (easeT > 0.02) {
          const vortexRings = 14;
          const particlesPerRing = 32;
          const vortexChars = ["*", "+", "%", "#", "=", ":", "·"];
          const time = B * 0.9;

          for (let ring = 1; ring <= vortexRings; ring++) {
            const ringFrac = ring / vortexRings;
            // El radio nace desde la esfera y se expande a su dimensión nominal
            const targetBase = rows * 0.48 * Math.pow(ringFrac, 0.85);
            const startBase = rows * 0.44 * ringFrac;
            const rBase = startBase + (targetBase - startBase) * easeT;

            const wave = Math.sin(time * 1.2 - ring * 0.5) * (1.2 * easeT);
            const r = rBase + wave;

            const ringSpeed = time * (0.8 - ringFrac * 0.4) + ring * 0.3;

            for (let i = 0; i < particlesPerRing; i++) {
              const theta = (i / particlesPerRing) * Math.PI * 2 + ringSpeed;
              const cosT = Math.cos(theta);
              const sinT = Math.sin(theta);

              const pX = r * cosT;
              const pY = r * sinT * 0.65 + Math.sin(theta * 4 + time * 2) * (ringFrac * 4 * easeT);
              const pZ = r * sinT * 0.35 * easeT;

              const zCoord = pZ + rows * 1.2;
              const ooz = 1 / Math.max(1, zCoord);

              const xp = Math.floor(cols / 2 + (pX * ooz) * (rows * 1.2 * aspectCorrection));
              const yp = Math.floor(rows / 2 + (pY * ooz) * (rows * 1.2));

              if (xp >= 0 && xp < cols && yp >= 0 && yp < rows) {
                const idx = xp + yp * cols;
                if (ooz > z[idx]) {
                  z[idx] = ooz;
                  const charIdx = (ring + i) % vortexChars.length;
                  b[idx] = vortexChars[charIdx];
                }
              }
            }
          }
        }

        // Construir el frame de texto para PixiJS
        let output = "";
        for (let r = 0; r < rows; r++) {
          let line = "";
          for (let c = 0; c < cols; c++) {
            line += b[c + r * cols];
          }
          output += line + "\n";
        }

        asciiText.text = output;

        // Centrado de la matriz
        asciiText.x = (screenW - asciiText.width) / 2;
        asciiText.y = (screenH - asciiText.height) / 2;

        // Interpolación continua de color: zinc (#52525b) -> blanco puro (#f4f4f5)
        const grayVal = Math.floor(0x52 + easeT * (0xf4 - 0x52));
        const colorHex = (grayVal << 16) | (grayVal << 8) | grayVal;
        asciiText.style.fill = colorHex;
      });

      return () => {
        window.removeEventListener("mousemove", onMouseMove);
        resizeObserver.disconnect();
      };
    }

    initPixi();

    return () => {
      isMounted = false;
      if (appRef.current) {
        appRef.current.destroy(true, { children: true });
        appRef.current = null;
      }
    };
  }, []);

  return (
    <div className="relative w-full h-full flex items-center justify-center pointer-events-none overflow-hidden">
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />
    </div>
  );
}
