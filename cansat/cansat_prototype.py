from sx1262 import SX1262
import time
import bme280_float as bme
import mlx90614
import veml6075
import machine
import sdcard
import vfs
import os

# If others are using the same frequency as us, what should identify our messages from theirs
identifier = "coyac"

# Pins to use for I2C components
SCL_PIN = 48
SDA_PIN = 47

# How long the program runs for
RUNTIME_SECONDS = 15

# The interval at which the CanSat takes measurements in seconds
MEASUREMENT_FREQ_SECONDS = 1.05

# The directory that the SD Card will be mounted to on the controller
SD_CARD_DIR = "/sd_card"

# Initialise LoRa module
lora = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
lora.begin(freq=868)

# Setup I2C pins and initialise sensors
# Frequency must be 100kHz to allow the infrared sensor to work
i2c_pins = machine.I2C(sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=100_000)
bme_sensor = bme.BME280(i2c=i2c_pins)
ir_sensor = mlx90614.MLX90614(i2c=i2c_pins)
uv_sensor = veml6075.VEML6075(i2c=i2c_pins)

# Setup SPI pins and initialise the SD Card reader
spi_bus = machine.SPI(2, sck=36, mosi=34, miso=33)
cs_pin = machine.Pin(47)
sd_card = sdcard.SDCard(spi_bus, cs_pin)

# Mount the SD Card as a virtual filesystem and create the output file
vfs=os.VfsFat(sd_card)
os.mount(vfs, SD_CARD_DIR)
sd_file = open(f"{SD_CARD_DIR}/output_data.csv", "w")


def on_lora_event(events):
    if events & SX1262.RX_DONE:
        message, error = lora.recv()
        # Add more here
        message = message.decode()
        error = SX1262.STATUS[error] 
        if message.startswith("RESEND"):
            target_timestamp = int(message.split(" ")[-1])
            # Read from the SD Card
            timestamp = -1
            while timestamp != target_timestamp:
                txt = sd_file.readline()
                timestamp = txt.split(",")[0]

            data = txt.split(",")[1:]
            for i, val in enumerate(data):
                data_type = ["t", "p", "h", "i", "u"][i]
                lora.send(f"{identifier}:d:{data_type},{target_timestamp},{val}".encode())

lora.setBlockingCallback(False, on_lora_event)

class CollectedData:
    def __init__(self, timestamp, bme_reading, ir_reading, uv_reading) -> None:
        self.timestamp = timestamp
        self.temperature = bme_reading[0]
        self.pressure = bme_reading[1] / 100
        self.humidity = bme_reading[2]
        self.ir = ir_reading
        self.uv = uv_reading

    def get_temp_string(self) -> str:
        return f"{identifier}:d:t,{self.timestamp},{self.temperature}\n"
    def get_pressure_string(self) -> str:
        return f"{identifier}:d:p,{self.timestamp},{self.pressure}\n"
    def get_humidity_string(self) -> str:
        return f"{identifier}:d:h,{self.timestamp},{self.humidity}\n"
    def get_ir_string(self) -> str:
        return f"{identifier}:d:i{self.timestamp},{self.ir}\n"
    def get_uv_string(self) -> str:
        return f"{identifier}:d:u,{self.timestamp},{self.uv}\n"

    def get_csv_data_strings(self) -> list[str]:
        return [self.get_pressure_string(), self.get_pressure_string(), self.get_humidity_string(), self.get_ir_string(), self.get_uv_string()]

    def __str__(self) -> str:
        return f"Time: {self.timestamp}\nTemperature: {self.temperature}°C\nPressure: {self.pressure}hPa\nHumidity: {self.humidity}%RH\nIR: {self.IR}°C\nUV Index: {self.UV}"

# Returns csv string containing data collected from each sensor
def collect_data() -> CollectedData:
    timestamp = time.time()
    bme_data = bme_sensor.read_compensated_data()
    ir_data = ir_sensor.read_ambient_temp()
    uv_data = uv_sensor.uv_indockingCallback(False, on_lora_event)

    return CollectedData(timestamp, bme_data, ir_data, uv_data)

start_time = time.time()

while time.time() - start_time < RUNTIME_SECONDS:
    data = collect_data()
    print("--------")
    print(data)
    print("--------")
    
    # convert data to byte string and transmit
    #lora.send(data.get_csv_data_strings().encode("utf-8"))
    data_strs = data.get_csv_data_strings()
    for string in data_strs:
        lora.send(string.encode())
    
    # save data to SD card
    write_str = f"{data.timestamp}"
    for data_str in data_strs:
        write_str += data_str.split(",")[-1]
    write_str += "\n"
    sd_file.write(write_str)
    time.sleep(MEASUREMENT_FREQ_SECONDS)

sd_file.close()
