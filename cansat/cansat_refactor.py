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

def setup_pins() -> dict:
    # Initialise LoRa module
    lora = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
    lora.begin(freq=868)

    # TODO: Set this up
    #lora.setBlockingCallback(False, on_lora_event)

    # Setup I2C pins and initialise sensors
    # Frequency must be 100kHz to allow the infrared sensor to work
    i2c_pins = machine.I2C(sda=machine.Pin(SDA_PIN), scl=machine.Pin(SCL_PIN), freq=100_000)
    bme_sensor = bme.BME280(i2c=i2c_pins)
    ir_sensor = mlx90614.MLX90614(i2c=i2c_pins)
    uv_sensor = veml6075.VEML6075(i2c=i2c_pins)

    # ---- SD CARD ----

    # Setup SPI pins and initialise the SD Card reader
    spi_bus = machine.SPI(2, sck=36, mosi=34, miso=33)
    cs_pin = machine.Pin(47)
    sd_card = sdcard.SDCard(spi_bus, cs_pin)

    # Mount the SD Card as a virtual filesystem and create the output file
    vfs=os.VfsFat(sd_card)
    os.mount(vfs, SD_CARD_DIR)
    sd_file = open(f"{SD_CARD_DIR}/output_data.csv", "w")
    sd_file.write("timestamp,temperature,pressure,humidity,infrared,ultraviolet\n")

    return {
        "lora" : lora,
        "bme_sensor" : bme_sensor,
        "ir_sensor" : ir_sensor,
        "uv_sensor" : uv_sensor,
        "output_file" : sd_file
    }

# def on_lora_event(events):
#     if events & SX1262.RX_DONE:
#         message, error = lora.recv()
#         # Add more here
#         message = message.decode()
#         error = SX1262.STATUS[error]
#         if message.startswith("RESEND"):
#             target_timestamp = int(message.split(" ")[-1])
#             # Read from the SD Card
#             timestamp = -1
#             while timestamp != target_timestamp:
#                 txt = sd_file.readline()
#                 timestamp = txt.split(",")[0]
#
#             data = txt.split(",")[1:]
#             for i, val in enumerate(data):
#                 data_type = ["t", "p", "h", "i", "u"][i]
#                 lora.send(f"{identifier}:d:{data_type},{target_timestamp},{val}".encode())

class CollectedData:
    def __init__(self, timestamp, bme_reading, ir_reading, uv_reading) -> None:
        # Convert data to the correct units
        self.timestamp = timestamp
        self.temperature = bme_reading[0]
        self.pressure = bme_reading[1] / 100
        self.humidity = bme_reading[2]
        self.ir = ir_reading
        self.uv = uv_reading

    # Returns csv strings for each piece of data to be sent in packets
    def get_temp_string(self) -> str:
        return f"{identifier},data:t,{self.timestamp},{self.temperature}\n"

    def get_pressure_string(self) -> str:
        return f"{identifier},data:p,{self.timestamp},{self.pressure}\n"

    def get_humidity_string(self) -> str:
        return f"{identifier},data:h,{self.timestamp},{self.humidity}\n"

    def get_ir_string(self) -> str:
        return f"{identifier},data:i,{self.timestamp},{self.ir}\n"

    def get_uv_string(self) -> str:
        return f"{identifier},data:u,{self.timestamp},{self.uv}\n"

    # Just a list containing the returned strings of the above functions
    def get_csv_data_strings(self) -> list[str]:
        return [self.get_pressure_string(), self.get_pressure_string(), self.get_humidity_string(), self.get_ir_string(), self.get_uv_string()]

    # For debug, to print the data to the console
    def __str__(self) -> str:
        return f"Time: {self.timestamp}\nTemperature: {self.temperature}°C\nPressure: {self.pressure}hPa\nHumidity: {self.humidity}%RH\nIR: {self.IR}°C\nUV Index: {self.UV}"

# Returns a class containing data collected from each sensor
def collect_data(components: dict) -> CollectedData:
    timestamp = time.time()
    bme_data = components["bme_sensor"].read_compensated_data()
    ir_data = components["ir_sensor"].read_ambient_temp()
    uv_data = components["uv_sensor"].uv_index

    return CollectedData(timestamp, bme_data, ir_data, uv_data)


def main():
    # Initialises all components and stores them in a dictionary
    components = setup_pins()

    start_time = time.time()

    while time.time() - start_time < RUNTIME_SECONDS:
        data = collect_data(components)
        print("--------")
        print(data)
        print("--------")

        # Encode each packet and transmit to the ground
        data_strs = data.get_csv_data_strings()
        for string in data_strs:
            lora.send(string.encode())

        # Save data to SD card
        sd_file.write(f"{data.timestamp},{data.temperature},{data.pressure},{data.humidity},{data.ir},{data.uv}\n")

        # Wait until the next measurement should be taken
        time.sleep(MEASUREMENT_FREQ_SECONDS)

    sd_file.close()

if __name__ == "__main__":
    main()
