"""
Minimal reusable WS2812 flame effect (CircuitPython)

- Pure NeoPixel flame (no display/eye code).
- Works on 1D strips or 2D matrices (with optional zig-zag wiring and origin selection).
- Column-style flame coloring *or* direct heat-map rendering, with subtle brightness shimmer.

USAGE
-----
    import config
    from flame_ws2812 import FlameWS2812

    flame = FlameWS2812(
        config_module=config,
        target_fps=40,
        matrix_width=getattr(config, "WS2812_MATRIX_WIDTH", 8),  # None for 1D strip
        zigzag=getattr(config, "WS2812_ZIGZAG", True),
        origin=getattr(config, "WS2812_ORIGIN", "bottom-left"), # tl,tr,bl,br
        mode="columns",  # or "heat"
    )
    flame.run()  # or call flame.step() yourself in your main loop

Config expectations (in your config.py):
- ENABLE_WS2812 (bool), WS2812_PIN (string name of board pin), WS2812_NUM_PIXELS (int)
- Optional: WS2812_MATRIX_WIDTH (int), WS2812_ZIGZAG (bool), WS2812_ORIGIN (str)
"""

import time
import random

try:
    import board
    import neopixel
except Exception as e:  # pragma: no cover
    raise RuntimeError("This module requires CircuitPython with neopixel + board available") from e


class FlameWS2812:
    def __init__(
        self,
        config_module,
        *,
        target_fps: int = 40,
        matrix_width: int | None = None,
        zigzag: bool = True,
        origin: str = "bottom-left",  # one of: "top-left", "top-right", "bottom-left", "bottom-right"
        mode: str = "columns",  # "columns" or "heat"
        shimmer_min: float = 0.15,
        shimmer_max: float = 1.0,
        shimmer_step: float = 0.02,
        cool_max: int = 20,
        spark_count: int = 2,
        spark_min: int = 160,
        spark_max: int = 255,
    ):
        self.cfg = config_module
        if not getattr(self.cfg, "ENABLE_WS2812", False):
            raise RuntimeError("ENABLE_WS2812 is False in config.py")

        self.target_fps = target_fps
        self.frame_duration = 1.0 / float(target_fps)

        self.num_pixels = getattr(self.cfg, "WS2812_NUM_PIXELS")
        pin_name = getattr(self.cfg, "WS2812_PIN")
        pin = getattr(board, pin_name)

        self.pixels = neopixel.NeoPixel(pin, self.num_pixels, brightness=0.5, auto_write=False)
        self.heat = [0] * self.num_pixels

        # Matrix/strip geometry
        self.width = matrix_width  # None => 1D strip
        self.zigzag = bool(zigzag)
        self.origin = origin.lower()
        self.height = (self.num_pixels // self.width) if self.width else 1

        # Render & physics params
        self.mode = mode  # "columns" or "heat"
        self.cool_max = int(cool_max)
        self.spark_count = int(spark_count)
        self.spark_min = int(spark_min)
        self.spark_max = int(spark_max)

        # brightness shimmer
        self.brightness = shimmer_min
        self.brightness_dir = abs(shimmer_step)
        self.shimmer_min = float(shimmer_min)
        self.shimmer_max = float(shimmer_max)

    # -------------------------- Mapping --------------------------
    def _index(self, row: int, col: int) -> int:
        """Map (row,col) to 1D index considering zigzag and origin.
        row=0 is top or bottom depending on origin.
        col=0 is left or right depending on origin.
        """
        if not self.width:
            # 1D strip: treat col as index
            return col

        width = self.width
        height = self.height

        # Flip based on origin
        if "top" in self.origin:
            base_row = row
        else:  # bottom origin
            base_row = (height - 1) - row
        if "left" in self.origin:
            base_col = col
        else:  # right origin
            base_col = (width - 1) - col

        # Zigzag handling
        if self.zigzag and (base_row % 2 == 1):
            base_col = (width - 1) - base_col

        return base_row * width + base_col

    # -------------------------- Colors ---------------------------
    @staticmethod
    def heat_ramp(v: int) -> tuple[int, int, int]:
        v = max(0, min(255, int(v)))
        if v > 0x40:
            v -= 0x40
            return (255, v, 0)  # orange -> yellow
        return (v + 16, 0, 0)   # deep red -> red

    # -------------------------- Physics --------------------------
    def _flame_physics(self) -> None:
        # cooling
        for i in range(self.num_pixels):
            self.heat[i] = max(0, self.heat[i] - random.randint(0, self.cool_max))
        # diffusion upwards along the 1D buffer
        for i in range(self.num_pixels - 1, 2, -1):
            self.heat[i] = (self.heat[i - 1] + self.heat[i - 2] + self.heat[i - 2]) // 3
        # base sparks
        for _ in range(self.spark_count):
            idx = random.randint(0, min(2, self.num_pixels - 1))
            self.heat[idx] = min(255, self.heat[idx] + random.randint(self.spark_min, self.spark_max))

    # -------------------------- Rendering ------------------------
    def _render_columns(self) -> None:
        if not self.width:
            # 1D: fall back to heat render to map physics directly
            self._render_heat()
            return

        width = self.width
        height = self.height

        # Brightness shimmer
        self.brightness += self.brightness_dir
        if self.brightness >= self.shimmer_max or self.brightness <= self.shimmer_min:
            self.brightness_dir *= -1
        self.pixels.brightness = self.brightness

        # Per-column color bands (yellow/orange/red) from base upwards
        for col in range(width):
            yellow_end = random.randint(1, min(2, height))
            orange_end = min(height, yellow_end + random.randint(1, 3))
            for row in range(height):
                idx = self._index(row, col)
                if row < yellow_end:
                    self.pixels[idx] = self.heat_ramp(random.randint(120, 150))
                elif row < orange_end:
                    self.pixels[idx] = self.heat_ramp(random.randint(85, 120))
                else:
                    self.pixels[idx] = self.heat_ramp(random.randint(0, 85))
        self.pixels.show()

    def _render_heat(self) -> None:
        # Brightness shimmer
        self.brightness += self.brightness_dir
        if self.brightness >= self.shimmer_max or self.brightness <= self.shimmer_min:
            self.brightness_dir *= -1
        self.pixels.brightness = self.brightness

        if not self.width:
            # 1D: map heat directly
            for i in range(self.num_pixels):
                self.pixels[i] = self.heat_ramp(self.heat[i])
        else:
            width = self.width
            height = self.height
            # project 1D heat up the columns (simple gradient per row)
            # bottom rows use hotter values; upper rows use cooler values
            for col in range(width):
                for row in range(height):
                    # sample a position along the heat buffer
                    src = min(self.num_pixels - 1, row + col)  # cheap varying sample
                    self.pixels[self._index(row, col)] = self.heat_ramp(self.heat[src])
        self.pixels.show()

    # -------------------------- Main loop ------------------------
    def step(self) -> None:
        start = time.monotonic()
        self._flame_physics()
        if self.mode == "columns":
            self._render_columns()
        else:
            self._render_heat()
        # cap FPS
        elapsed = time.monotonic() - start
        rem = self.frame_duration - elapsed
        if rem > 0:
            time.sleep(rem)

    def run(self, duration: float | None = None) -> None:
        start = time.monotonic()
        while True:
            self.step()
            if duration is not None and (time.monotonic() - start) >= duration:
                break


# Quick self-test when run directly (requires a suitable config.py)
if __name__ == "__main__":
    try:
        import config  # type: ignore
    except ImportError as e:
        raise SystemExit("This test runner expects a config.py next to the file.") from e

    flame = FlameWS2812(
        config_module=config,
        target_fps=40,
        matrix_width=getattr(config, "WS2812_MATRIX_WIDTH", None),
        zigzag=getattr(config, "WS2812_ZIGZAG", True),
        origin=getattr(config, "WS2812_ORIGIN", "bottom-left"),
        mode="columns",
    )
    flame.run()
