import serial
import time

ser = serial.Serial(
    port = "/dev/ttyUSB0",
    baudrate = 9600,
    timeout = 1)

def sendCommand(comm):
    command = f"{comm}\r\f"
    ser.write(command.encode())
    
def receive():
    line = ser.read_until("\r".encode())
    print(f"Message: {line.decode().strip()}")
    
if ser.isOpen():
    for i in range(100):
        receive()
        time.sleep(1)
    ser.close()
else:
    print("Port is not open!")