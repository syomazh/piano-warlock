from midi_stream_to_arduino import play_midi

import serial
import time

ser = serial.Serial('COM5', 115200)
time.sleep(2)  # Wait for Arduino to reset
ser.write(b'E,60,500\n')
ser.close()

play_midi("krish-stuff/ode-to-joy.mid", port="COM5", baud=115200)