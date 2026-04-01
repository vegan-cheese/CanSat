import machine
import sdcard
import vfs
import os

SD_CARD_DIR = "/sd_card"

spi = machine.SPI(2, sck=6, mosi=5, miso=4)
cs = machine.Pin(7)

sd_card = sdcard.SDCard(spi, cs)

vfs=os.VfsFat(sd_card)
os.mount(vfs, SD_CARD_DIR)

sd_file = open(f"{SD_CARD_DIR}/output_data.txt", "a")
sd_file.write("Hello")
sd_file.close()
vfs.umount()