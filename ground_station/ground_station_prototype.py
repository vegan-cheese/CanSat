from sx1262 import SX1262
import time
import machine

identifier = "coyac"

def deserialise_received_message(message: str):
    # coyac:data,t,[TIMESTAMP],[DATA]
    if message.startswith(identifier)


def on_lora_event(events):
    if events & SX1262.RX_DONE:
        packet, error = lora.recv()
        packet = packet.decode("utf-8")
        packet_type = get_packet_type(packet)
        error = SX1262.STATUS[error]
        print(packet)

lora = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)

lora.begin(freq=868)

lora.setBlockingCallback(False, on_lora_event)