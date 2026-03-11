from sx1262 import SX1262
import time
import machine

BUTTON_PIN = 67

fl_index = 5
freq_list = [
    400,
    500,
    600,
    700,
    800,
    868,
    900,
    "powersave"
]

powersave = False

def cb(events):
    if  events & SX1262.RX_DONE:
        msg, err = sx.recv()
        msg = msg.decode("utf-8")
        err = SX1262.STATUS[err]
        print(msg)

def toggle_power_save():
    pass

def on_button_press():
    fl_index += 1
    if type(freq_list[fl_index]) == int:
        # 
        sx.send(f"changefreq{freq_list[fl_index]}")
        sx.setFrequency(freq_list[fl_index])
    elif freq_list[fl_index] == "powersave":
        fl_index += 1
        toggle_power_save()

sx = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
sx.begin(freq=868)

button = machine.Pin(BUTTON_PIN, machine.Pin.IN)

sx.setBlockingCallback(False, cb)

while True:
    print(f"Testing {time.time()}")
    prev_button_state = 0
    if button.value() == 1:
        if prev_button_state == 0:
            on_button_press()
        prev_button_state = 1
    else:
        prev_button_state = 0
    time.sleep(0.5)