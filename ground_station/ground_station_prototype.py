from sx1262 import SX1262
import time
import machine

class PartiallyReceivedData:
    def __init__(self, waitTime, timestamp):
        self.waitTime = waitTime
        self.timestamp = timestamp
        self.data = []

cache: list[PartiallyReceivedData] = []
fullyRecievedTimestamps: list[int] = []

identifier = "coyac"

collected_data = {
}

def deserialise_received_message(message: str):
    # coyac:data,[TYPE],[TIMESTAMP],[DATA] 
    if not message.startswith(identifier):
        return

    split_str = message.split(",")
    value = split_str[-1]
    # Time, Value
    return [split_str[-2], {value}]

def get_packet_type(packet: str) -> str:
    return packet.split(":")[-1][0]


def on_lora_event(events):
    if events & SX1262.RX_DONE:
        packet, error = lora.recv()
        packet = packet.decode("utf-8")
        error = SX1262.STATUS[error]
        packet_type = get_packet_type(packet)
        ls = deserialise_received_message(packet)
        if ls is None:
            return
        csv_file = open("data.csv", "a")
        timestamp, data = ls
        if timestamp not in collected_data.keys():
            collected_data[timestamp] = [(packet_type, data)]
            cache.append(PartiallyReceivedData(timestamp, timestamp))
            cache[-1].data.append((packet_type, data))

        else:
            if len(collected_data[timestamp]) == 5:
                return
            collected_data[timestamp].append((packet_type, data))
            if len(collected_data[timestamp]) == 5:
                csv_ls = [timestamp]
                for data_type in ["t", "p", "h", "i", "u"]:
                    for data in collected_data[timestamp]:
                        if data[0] == data_type:
                            csv_ls.append(data[1])
                            break
                csv_file.write(",".join(csv_ls))
                
            for partial_data in cache:
                if partial_data.timestamp == timestamp:
                    partial_data.data.append((packet_type, data))
                    if len(partial_data.data) == 5:
                        cache.remove(partial_data)
                    break
        csv_file.close()
        for partial_data in cache:
            if partial_data.waitTime > 3 + timestamp:
                lora.send(f"RESEND {partial_data.timestamp}".encode())

        print(packet)

with open("data.csv", "w") as f:
    f.write("timestamp,temperature,pressure,humidity,infrared,ultraviolet")

lora = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)

lora.begin(freq=868)

lora.setBlockingCallback(False, on_lora_event)