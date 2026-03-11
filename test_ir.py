import machine
import mlx90614
import time

SCL_PIN = 4
SDA_PIN = 3

i2c = machine.I2C(sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=100000)
ir_sensor = mlx90614.MLX90614(i2c=i2c)

for x in range(30):
    try:
        ir_data = ir_sensor.read_ambient_temp()
        print(ir_data)
    except Exception as e:
        print(e)
    time.sleep(1)