from sx1262 import SX1262
import time
import bme280_float as bme
import mlx90614
import machine

def cb(events):
    if events & SX1262.RX_DONE:
        msg, err = sx.recv()
        error = SX1262.STATUS[err]
        print('Receive: {}, {}'.format(msg, error))
    elif events & SX1262.TX_DONE:
        print('TX done.')

sx = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
sx.begin(freq=868)

sx.setBlockingCallback(False, cb)

i2c = machine.I2C(sda=machine.Pin(), scl=machine.Pin())
bme_sensor = bme.BME280(i2c=i2c)
other_sensor = mlx90614.MLX90614(i2c)

while True:
    sx.send(b'Ping')
    time.sleep(10)
