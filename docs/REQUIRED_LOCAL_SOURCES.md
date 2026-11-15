# Missing original working hardware source files

The NASA data-preparation code and V9 dashboard source are preserved here. However, **do not invent or substitute** code for these original live-hardware components:

1. `esp32_veri_toplama_v3.py` — Python USB serial collector.
2. ESP32 V8 `.ino` sketch, including any auxiliary tabs/headers.
3. Arduino Uno LCD V7 `.ino` sketch, including any auxiliary tabs/headers.

Save any unsaved Arduino IDE sketches via **File > Save As** on the original Windows machine, preserving the sketch folder and all tabs. Then copy original sketch folders into `firmware/ESP32_V8/` and `firmware/Arduino_Uno_V7/`. Copy the working Python collector into repository root. Firmware compiled on the devices is not equivalent to recoverable original source.

Do not commit sensitive health check-ins, private serial logs, secrets or credentials. The absence of these original sources does not affect the reproducibility of the NASA data-cleaning program itself.