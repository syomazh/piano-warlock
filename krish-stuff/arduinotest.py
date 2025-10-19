import serial, time
ser = serial.Serial('COM5', 115200, timeout=1)
time.sleep(2)
ser.write(b'E,60,500\n')
ser.close()