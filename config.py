import board

# 디스플레이 해상도 및 UI 설정
WIDTH = 240
HEIGHT = 240
UI_HEIGHT = 38
FPS = 20

# SPI 디스플레이 핀 설정 (기존 작동 확인된 핀)
CS_PIN = board.CE0
DC_PIN = board.D25
RST_PIN = board.D24
BL_PIN = board.D26

# 조이스틱 및 버튼 핀 설정
PIN_UP = board.D17
PIN_DOWN = board.D22
PIN_RIGHT = board.D27
PIN_LEFT = board.D23
PIN_CENTER = board.D4