from sx1262 import SX1262
import time
import bme280_float as bme
import mlx90614
import veml6075
import machine
import sdcard
import vfs
import os
import _thread

v_control = machine.Pin(36, machine.Pin.OUT, machine.Pin.PULL_UP)
v_control.value(0)

# If others are using the same frequency as us, what should identify our messages from theirs
IDENTIFIER = "coyac"

# Pins to use for I2C components
SCL_PIN = 48
SDA_PIN = 47

# The interval at which the CanSat takes measurements in seconds
MEASUREMENT_FREQ_SECONDS = 0.5

# The directory that the SD Card will be mounted to on the controller
SD_CARD_DIR = "/sd_card"

FREQ_LIST = [
    863,
    864,
    865,
    866,
    867,
    868,
    869,
    870
]
current_freq_index = 0

components = {}

def setup_pins() -> dict:
    # Initialise LoRa module
    lora = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
    lora.begin(freq=FREQ_LIST[current_freq_index])

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
    spi_bus = machine.SPI(2, sck=6, mosi=5, miso=4)
    cs_pin = machine.Pin(7)
    sd_card = sdcard.SDCard(spi_bus, cs_pin)

    # Mount the SD Card as a virtual filesystem and create the output file
    vfs=os.VfsFat(sd_card)
    os.mount(vfs, SD_CARD_DIR)
    sd_file = open(f"{SD_CARD_DIR}/output_data.csv", "w")
    sd_file.write("timestamp,temperature,pressure,humidity,infrared,ultraviolet\n")
    sd_file.close()
    
    led = machine.Pin(35, machine.Pin.OUT)
    button = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)

    return {
        "lora" : lora,
        "bme_sensor" : bme_sensor,
        "ir_sensor" : ir_sensor,
        "uv_sensor" : uv_sensor,
        "led": led,
        "button": button
    }

def change_frequency(freq):
    components["lora"].setfrequency(freq)
    # Send Confirmation

def on_lora_event(events):
    if events & SX1262.RX_DONE:
        # Format the packet
        try:
            packet, error = lora.recv()
            packet = packet.decode("utf-8")
            error = SX1262.STATUS[error]
        except:
            print("Failed to receive packet!")
            return

        # TODO: Check lengths of split lists and return nothing if incorrect

        # Here is the format of the received string for data:
        split_packet = packet.split(":")
        header_items = split_packet[0].split(",")
        body_items = split_packet[1].split(",")

        # This data was not transmitted by our CanSat
        if header_items[0] != IDENTIFIER:
            return
        
        if header_items[1] == "change":
            #Change frequency
            change_frequency(body_items)
            
        elif header_items[1] == "resend":
            # Resend Data
            pass

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
        return f"{IDENTIFIER},data:t,{self.timestamp},{self.temperature}\n"

    def get_pressure_string(self) -> str:
        return f"{IDENTIFIER},data:p,{self.timestamp},{self.pressure}\n"

    def get_humidity_string(self) -> str:
        return f"{IDENTIFIER},data:h,{self.timestamp},{self.humidity}\n"

    def get_ir_string(self) -> str:
        return f"{IDENTIFIER},data:i,{self.timestamp},{self.ir}\n"

    def get_uv_string(self) -> str:
        return f"{IDENTIFIER},data:u,{self.timestamp},{self.uv}\n"

    # Just a list containing the returned strings of the above functions
    def get_csv_data_strings(self) -> list[str]:
        return [self.get_pressure_string(), self.get_pressure_string(), self.get_humidity_string(), self.get_ir_string(), self.get_uv_string()]
    
    def get_csv_string(self) -> str:
        return f"{IDENTIFIER},data:{self.timestamp},{self.temperature},{self.pressure},{self.humidity},{self.ir},{self.uv}\n"

    # For debug, to print the data to the console
    def __str__(self) -> str:
        return f"Time: {self.timestamp}\nTemperature: {self.temperature}°C\nPressure: {self.pressure}hPa\nHumidity: {self.humidity}%RH\nIR: {self.ir}°C\nUV Index: {self.uv}"

# Returns a class containing data collected from each sensor
def collect_data(components: dict, start_time) -> CollectedData:
    timestamp = (time.time_ns() - start_time) // 10000
    bme_data = components["bme_sensor"].read_compensated_data()
    ir_data = components["ir_sensor"].read_ambient_temp()
    uv_data = components["uv_sensor"].uv_index

    return CollectedData(timestamp, bme_data, ir_data, uv_data)

def transmit_data(components, data_strs):
    for string in data_strs:
            components["lora"].send(string.encode("utf-8"))
            print(string)

def flash_led(count, components):
    for i in range(count):
        components["led"].value(1)
        time.sleep(0.2)
        components["led"].value(0)
        time.sleep(0.2)

def main():
    global current_freq_index, components
    # Initialises all components and stores them in a dictionary
    components = setup_pins()

    start_time = time.time_ns()
    prev_button_state = components["button"].value()

    while True:
        
        new_button_state = components["button"].value()
        if new_button_state != prev_button_state and new_button_state == 1:
            current_freq_index += 1
            if current_freq_index >= len(FREQ_LIST):
                current_freq_index = 0
            print(f"Changing frequency to {FREQ_LIST[current_freq_index]} MHz")
            _thread.start_new_thread(flash_led, [current_freq_index + 1, components])
            try:
                #components["lora"].setFrequency(FREQ_LIST[current_freq_index])
                pass
            except:
                print("Failed to change frequency!")
                current_freq_index -= 1
                if current_freq_index < 0:
                    current_freq_index = len(FREQ_LIST) - 1
            # components["lora"].setBlockingCallback(False, on_lora_event)
        prev_button_state = new_button_state
        
        try:
            data = collect_data(components, start_time)
        except:
            print("Failed to read sensors!")
            data = CollectedData(time.time_ns(), -1, [-1, -1, -1], -1, -1)

        print("--------")
        print(data.get_csv_string())

        # Encode each packet and transmit to the ground
        # = data.get_csv_data_strings()
        #_thread.start_new_thread(transmit_data, (components, data_strs))
        components["lora"].send(data.get_csv_string().encode())

        # Save data to SD card
        try:
            with open(f"{SD_CARD_DIR}/output_data.csv", "a") as f:
                f.write(f"{data.timestamp},{data.temperature},{data.pressure},{data.humidity},{data.ir},{data.uv}\n")
        except:
            print("Failed to write data to SD Card!")

        # Wait until the next measurement should be taken
        time.sleep(MEASUREMENT_FREQ_SECONDS)

    #components["output_file"].close()

if __name__ == "__main__":
    main()
