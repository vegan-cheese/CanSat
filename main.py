from sx1262 import SX1262
import time
import bme280_float as bme
import mlx90614
import machine

'''def callback(events):
    if events & SX1262.RX_DONE:
        msg, err = sx.recv()
        error = SX1262.STATUS[err]
        print('Receive: {}, {}'.format(msg, error))
    elif events & SX1262.TX_DONE:
        print('TX done.')

sx = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
sx.begin(freq=868)

sx.setBlockingCallback(False, callback)'''

i2cbme = machine.I2C(sda=machine.Pin(40), scl=machine.Pin(41))
bme_sensor = bme.BME280(i2c=i2cbme)
#other_sensor = mlx90614.MLX90614(i2c=i2c)


bme_data = bme_sensor.read_compensated_data()
print(bme_data)
time.sleep(10)
