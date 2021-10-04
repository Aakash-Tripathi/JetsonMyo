#!/usr/bin/env python3
import serial
import os


def main():
    ser = serial.Serial('COM4', 9600, timeout=1)
    ser.flush()

    found_ports = os.system("python -m serial.tools.list_ports -v")

    for i in range(256):
        number = ser.read() * 256 + ser.read()
        number = int.from_bytes(number, "big")
        if(number < 256):
            print(str(number))


if __name__ == '__main__':
    main()
