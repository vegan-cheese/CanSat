import machine
from sx1262 import SX1262
import time
import bme280_float as bme
SCL_PIN = 48
SDA_PIN = 47
v_control = machine.Pin(36, machine.Pin.OUT, machine.Pin.PULL_UP)
v_control.value(0)
i2c_pins = machine.I2C(sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=100_000)


while True:
    time.sleep(1)
    try:
        bme_sensor = bme.BME280(i2c=i2c_pins)
    except OSError as e:
        print("Connection failed!", e)
    else:
        print(bme_sensor.read_compensated_data())