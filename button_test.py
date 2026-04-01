import machine
import time

led = machine.Pin(35, machine.Pin.OUT)

button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)

prev_state = button.value()
while True:
    new_state = button.value()
    if prev_state != new_state:
        led.value(not led.value())
    prev_state = new_state
    
    time.sleep(0.5)