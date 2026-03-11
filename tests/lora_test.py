from sx1262 import SX1262

sx = SX1262(spi_bus=1, clk=9, mosi=10, miso=11, cs=8, irq=14, rst=12, gpio=13)
sx.begin(freq=868)

while True:
    sx.send(b"Hello")