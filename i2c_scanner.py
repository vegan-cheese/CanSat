import machine
i2c = machine.I2C(scl=machine.Pin(4), sda=machine.Pin(3), freq=100000)

print('Scan i2c bus...')
devices = i2c.scan()

if len(devices) == 0:
  print("No i2c device !")
else:
  print('i2c devices found:',len(devices))

  for device in devices:
    print("Decimal address: ",device," | Hexa address: ",hex(device))
    
#addr = devices[0]
#chip_id = i2c.readfrom_mem(addr, 0xD0, 1)[0]
#print("Chip ID:", hex(chip_id))