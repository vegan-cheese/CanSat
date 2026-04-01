from sx1262 import SX1262
import time
import machine
import _thread

IDENTIFIER = "coyac"

components = {}

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

def on_received_data(body_items):
    # The body consists of measured data
    timestamp = body_items[0]
    
    try:
        with open("data.csv", "a") as f:
            f.write(f",".join(body_items))
    except:
        print("Could not write data to file!")
    print(",".join(body_items))

# Callback function when the LoRa module receives a message
def on_lora_event(events):
    if events & SX1262.RX_DONE:
        # Format the packet
        try:
            packet, error = components["lora"].recv()
            packet = packet.decode("utf-8")
            error = SX1262.STATUS[error]
        except:
            print("Failed to receive packet!")
            return

        # TODO: Check lengths of split lists and return nothing if incorrect
        if error != SX12632.STATUS[0]:
            print(error)
        

        # Here is the format of the received string for data:
        # coyac,data:[TIMESTAMP],[DATA]
        
        split_packet = packet.split(":")
        header_items = split_packet[0].split(",")
        body_items = split_packet[1].split(",")

        # This data was not transmitted by our CanSat
        if header_items[0] != IDENTIFIER:
            return

        if header_items[1] == "data":
            on_received_data(body_items)

def flash_led(count):
    for i in range(count):
        components["led"].value(1)
        time.sleep(0.2)
        components["led"].value(0)
        time.sleep(0.2)

def main():
    global current_freq_index
    # Write the csv headers
    try:
        with open("data.csv", "w") as f:
            f.write("timestamp,temperature,pressure,humidity,infrared,ultraviolet\n")
    except:
        print("Failed to write headings for data file!")

    # Setup LoRa module pins
    try:
        components["lora"] = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
        components["lora"].begin(freq=FREQ_LIST[current_freq_index])
        components["lora"].setBlockingCallback(False, on_lora_event)
    except:
        print("Failed to initialise LoRa!")
        return
    
    try:
        components["button"] = machine.Pin(0, machine.Pin.IN, machine.Pin.PULL_UP)
        components["led"] = machine.Pin(35, machine.Pin.OUT)
    except:
        print("Failed to initialise button and LED pins!")
        return

    prev_button_state = components["button"].value()
    while True:
        time.sleep(0.5)
        new_button_state = components["button"].value()
        
        # Button has been released
        if new_button_state != prev_button_state and new_button_state == 1:
            current_freq_index += 1
            if current_freq_index >= len(FREQ_LIST):
                current_freq_index = 0
            print(f"Changing frequency to {FREQ_LIST[current_freq_index]} MHz")
            _thread.start_new_thread(flash_led, [current_freq_index + 1])
            try:
                components["lora"].setFrequency(FREQ_LIST[current_freq_index])
            except:
                print("Failed to change frequency")
                current_freq_index -= 1
                if current_freq_index < 0:
                    current_freq_index = len(FREQ_LIST) - 1
            components["lora"].setBlockingCallback(False, on_lora_event)
            
        prev_button_state = new_button_state

if __name__ == "__main__":
    main()
