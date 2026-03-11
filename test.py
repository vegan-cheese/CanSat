import bme280_float
import mlx90614
import veml6075
import sx1262
import machine
import os
import time
import sdcard

i2c_pins = machine.I2C(sda=machine.Pin(3), scl=machine.Pin(4))

# setup pins
sx = sx1262.SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
sx.begin(freq=868)

bme = None
ir = None
uv = None

try:
    bme = bme280_float.BME280(i2c=i2c_pins)
except Exception as e:
    print(f"error connecting to bme: {e}")

try:
    ir = mlx90614.MLX90614(i2c=i2c_pins)
except Exception as e:
    print(f"error connecting to ir: {e}")

try:
    uv = veml6075.VEML6075(i2c=i2c_pins)
except Exception as e:
    print(f"error connecting to uv: {e}")

class CollectedData:
    def __init__(self, timestamp, BME_reading, IR_reading, UV_reading) -> None:
        self.timestamp = timestamp
        self.temperature = BME_reading[0]
        self.pressure = BME_reading[1] / 100
        self.humidity = BME_reading[2]
        self.IR = IR_reading
        self.UV = UV_reading
    
    def get_csv_string(self) -> str:
        return f"{self.timestamp},{self.temperature},{self.pressure},{self.humidity},{self.IR},{self.UV}"
    
    def __str__(self) -> str:
        return f"Time: {self.timestamp}\nTemperature: {self.temperature}°C\nPressure: {self.pressure}hPa\nHumidity: {self.humidity}%RH\nIR: {self.IR}°C\nUV Index: {self.UV}"

def collect_data() -> CollectedData:
    timestamp = time.time()
    bme_data = bme.read_compensated_data()
    #ir_data = ir_sensor.read_ambient_temp()
    #uv_data = uv_sensor.uv_index
    
    return CollectedData(timestamp, bme_data, 3, 3)

t = 60
avg_temp = None
avg_pressure = None
avg_humidity = None

start_time = time.time()
# Send Data
while time.time() - start_time < t:
    data = collect_data()
    print("----")
    print(data)
    sx.send(data.get_csv_string())
    time.sleep(1)
    