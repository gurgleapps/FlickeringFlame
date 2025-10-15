import config
from flame_ws2812 import FlameWS2812
import time

flame = FlameWS2812(
    config_module=config,
    target_fps=40,
    matrix_width=getattr(config, "WS2812_MATRIX_WIDTH", 8),  # None for 1D strip
    zigzag=getattr(config, "WS2812_ZIGZAG", True),
    origin=getattr(config, "WS2812_ORIGIN", "bottom-left"),
    mode="columns",   # or "heat"
)

while True:
    flame.step()
    time.sleep(0.01)
    print("i am alive")
