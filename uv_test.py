import  veml6075
from machine import I2C, Pin

i2c = I2C(sda=Pin(6), scl=Pin(5))
sensor = veml6075.VEML6075(i2c=i2c)

sensor.uv_index