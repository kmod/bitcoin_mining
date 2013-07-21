import threading
import time

import serial # easy_install pyserial


# Baud rates linux seems to support:
# 0 50 75 110 134 150 200 300 600 1200 1800 2400 4800 9600 19200 38400 57600 115200 230400 460800 576000 921600 1152000 1500000 3000000...
def test(br):
    ser = serial.Serial("/dev/ttyUSB0", br, timeout=.1)
    try:
        ser.read(1)
    except serial.serialutil.SerialException:
        return False
    finally:
        ser.close()
    return True

# for i in xrange(0, 10000000, 1200):
    # if test(i):
        # print i

ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=4)
print ser.portstr
ser.write("hello")

def read_thread():
    while True:
        c = ser.read(1)
        print "R", repr(c)

t = threading.Thread(target=read_thread)
t.setDaemon(True)
t.start()

i = 0
while True:
    time.sleep(1)
    print "W", repr(chr(i&0xff))
    ser.write(chr(i&0xff))
    i += 1
    # ser.write(c)
