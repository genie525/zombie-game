import digitalio
import board
from adafruit_rgb_display import st7789
import config

def init_display():
    cs = digitalio.DigitalInOut(config.CS_PIN)
    dc = digitalio.DigitalInOut(config.DC_PIN)
    rst = digitalio.DigitalInOut(config.RST_PIN)
    
    # 백라이트 켜기
    bl = digitalio.DigitalInOut(config.BL_PIN)
    bl.switch_to_output()
    bl.value = True

    spi = board.SPI()
    disp = st7789.ST7789(
        spi,
        width=config.WIDTH,
        height=config.HEIGHT,
        rotation=0,
        cs=cs,
        dc=dc,
        rst=rst,
        baudrate=24000000,
    )
    return disp

def _make_btn(pin):
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    return btn

def init_inputs():
    return {
        "UP": _make_btn(config.PIN_UP),
        "DOWN": _make_btn(config.PIN_DOWN),
        "LEFT": _make_btn(config.PIN_LEFT),
        "RIGHT": _make_btn(config.PIN_RIGHT),
        "CENTER": _make_btn(config.PIN_CENTER),
    }