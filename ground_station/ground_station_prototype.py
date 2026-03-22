from sx1262 import SX1262
import time
import machine

IDENTIFIER = "coyac"

TIMEOUT_TIME = 3
MAX_TIMEOUTS = 3

class PartialData:
    def __init__(self, last_timeout_check):
        self.last_timeout_check = last_timeout_check
        self.timeout_count = 0
        self.data = {}

# Timestamps that have been fully received already
received_times: list[int] = []

# Dictionary mapping timestamps to data that has been partially received
cache: dict[int, PartialData] = {}

output_file = None

def on_received_data(body_items):
    # The body consists of measured data
    data_type = body_items[0]
    timestamp = body_items[1]
    data = body_items[2]

    # Data has already been fully received
    if timestamp in received_times:
        return

    # Data is partially received
    if timestamp in cache.keys():
        # This datatype has already been received for this timestamp
        if data_type in cache[timestamp].data.keys():
            return
        else:
            cache[timestamp].data[data_type] = data

            # If adding this new bit of data has completed the data for the timestamp
            if len(cache[timestamp].data.keys()) == 5:
                # Order the data and write it to the file
                completed_data = cache[timestamp].data
                # TODO: Check if all keys are these letters
                csv_str = f"{timestamp},{data["t"]},{data["p"]},{data["h"]},{data["i"]},{data["u"]}\n"
                output_file.write(csv_str)
                # Add to received times
                received_times.append(timestamp)
                # Remove from cache
                cache.pop(timestamp)
    # Data has not yet been received at all
    else:
        cache[timestamp] = PartialData(timestamp)
        cache[timestamp].data[data_type] = data

    for timestamp, partial_data in cache.values():
        # If full set of data not received within TIMEOUT_TIME, request resends
        if partial_data.last_timeout_check > timestamp + TIMEOUT_TIME:
            # Set the new timeout counter to start from the current time
            partial_data.last_timeout_check = timestamp
            partial_data.timeout_count += 1

            # If resend requests were sent more than 3 times with no outcome, delete the data for that timestamp
            if partial_data.timeout_count <= MAX_TIMEOUTS:
                # Resend requests for data that was not received
                for dt in ["t", "p", "h", "i", "u"]:
                    if not (dt in partial_data.data.keys()):
                        lora.send(f"{identifier},resend:{dt},{timestamp}".encode())
            else:
                cache.pop(timestamp)

# Callback function when the LoRa module receives a message
def on_lora_event(events):
    if events & SX1262.RX_DONE:
        # Format the packet
        packet, error = lora.recv()
        packet = packet.decode("utf-8")
        error = SX1262.STATUS[error]

        # TODO: Check lengths of split lists and return nothing if incorrect

        # Here is the format of the received string for data:
        # coyac,data:[TYPE],[TIMESTAMP],[DATA]
        split_packet = packet.split(":")
        header_items = split_packet[0].split(",")
        body_items = split_packet[1].split(",")

        # This data was not transmitted by our CanSat
        if header_items[0] != IDENTIFIER:
            return

        if header_items[1] == "data":
            on_received_data(body_items)

def main():
    # Write the csv headers
    output_file = open("data.csv", "a")
    output_file.write("timestamp,temperature,pressure,humidity,infrared,ultraviolet\n")

    # Setup LoRa module pins
    lora = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
    lora.begin(freq=868)
    lora.setBlockingCallback(False, on_lora_event)

    #TODO: Maybe close the file?

if __name__ == "__main__":
    main()
