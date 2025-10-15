Flickering Flame Effect
========================

This is a flickering flame effect implementation for WS2812 NeoPixel LEDs using CircuitPython. The effect simulates a realistic flame by varying the brightness and color of the LEDs over time.

Usage
-----

1. Connect your WS2812 LED strip to the specified GPIO pin on your CircuitPython board.
2. Install the required libraries (if not already installed).
3. Customize the `config.py` file to match your hardware setup.
4. Run the `code.py` script to start the flame effect.

Configuration
-------------


# 🔥 FlameWS2812 (CircuitPython)

A minimal, reusable **WS2812 / NeoPixel flame effect** for CircuitPython.  
Supports both **1D LED strips** and **2D matrices** with optional **zig-zag wiring** and configurable **origin**.

---

## ⚙️ Setup

1. Copy these files to your CircuitPython board:
   ```
   code.py
   config.py
   flame_ws2812.py
   ```
2. Edit `config.py` to match your setup:
   ```python
   WS2812_PIN = "GP16"
   WS2812_MATRIX_WIDTH = 8
   WS2812_ZIGZAG = False
   WS2812_NUM_PIXELS = 64
   ENABLE_WS2812 = True
   ```

---

## 🚀 Usage

The `code.py` example runs automatically:

```python
import config
from flame_ws2812 import FlameWS2812
import time

flame = FlameWS2812(config_module=config, mode="columns")
while True:
    flame.step()
    time.sleep(0.01)
```

---

## 🧠 Notes

- Works with or without a matrix.
- Set `mode="columns"` for stylized flames or `mode="heat"` for full heatmap.
- Adjustable flicker, spark, and cooling parameters in `flame_ws2812.py`.

---

## 🪪 License

MIT License — free for personal or commercial use.