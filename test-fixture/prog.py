#!/bin/python3

# Script to program and test sea-micro

import os
import time
import argparse
from colorama import Fore
import serial
from serial.tools import list_ports
import io

def bootloader():
    ''' Flashes bootloader, using an external programmer connected to the ISP port on the test fixture.
        Defaults to AVRISPMKII, but can be used with a usbasp by changing the arg to -c.'''

    bootloader = "avrdude -v -p atmega32u4 -c avrispmkii -P usb -Uflash:w:ATMega32U4-dfu-bootloader.hex:i"
    
    retval = os.system(bootloader)

    if retval != 0:
        send_string(33) # Error
        print(f'{Fore.RED}#############################')
        print(f'{Fore.RED}FAIL AT WRITING BOOTLOADER!!!')
        print(f'{Fore.RED}#############################')
        exit()

def test_firmware():
    ''' Flash Test Firmware. Assumes atmel-dfu bootloader is already flashed to board. '''

    erase = "dfu-programmer atmega32u4 erase"
    flash = "dfu-programmer atmega32u4 flash sea_micro_test.hex"
    reset = "dfu-programmer atmega32u4 reset"

    print(f'{Fore.BLUE}ERASING DUT{Fore.WHITE}')
    retval = os.system(erase)

    if retval == 0:
        print(f'{Fore.BLUE}FLASHING DUT{Fore.WHITE}')
        retval = os.system(flash)

    if retval == 0:
        print(f'{Fore.BLUE}RESETTING DUT{Fore.WHITE}')
        retval = os.system(reset)

    if retval != 256: # For some reason the reset retval is 256 on success
        send_string(33) # Error
        print(f'{Fore.RED}############################')
        print(f'{Fore.RED}FAIL AT FLASHING QMK TEST!!!')
        print(f'{Fore.RED}############################')
        exit()

def send_string(string):
    serial_io.write(string)
    serial_io.flush()

def test_keys():
    ''' Test all IO with test fixture.
        Transmit number according to pin location, which test fixture will pull low, simulating key press.
        DUT will then respond with the alpha character (A=1, B=2 etc) which we can check. '''

    # Connect to test fixture
    uart = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
    serial_io = io.TextIOWrapper(io.BufferedRWPair(uart, uart))

    for char in range(1,19): # sea-micro has 18 IO

        alpha = chr(96 + char)

        # Transmit required char, and compare to what we want
        send_string(char)

        recv = input()
        print(f'Requested: {alpha} Received: {str(recv)}')

        if recv != alpha: # retry once

            print("Trying Again!")
            send_string(char)

            recv = input()
            print(f'Requested: {alpha} Received: {str(recv)}') 

            if recv != alpha:
                send_string(33) # Error
                print(f'{Fore.RED}###############')
                print(f'{Fore.RED}NOT TYPING {alpha} !!!')
                print(f'{Fore.RED}###############')
                exit()

if __name__ == "__main__":

    serial_io = None

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bootloader",    action='store_true')
    parser.add_argument("-f", "--qmk_firmware",  action='store_true')
    parser.add_argument("-t", "--test",          action='store_true')
    args = parser.parse_args()

    send_string(34) # Reset status LEDs

    if args.bootloader:
        bootloader()
        print(f'{Fore.BLUE}BOOTLOADER FLASHED{Fore.WHITE}')
        time.sleep(2)
    if args.qmk_firmware:
        test_firmware()
        print(f'{Fore.BLUE}TEST FIRMWARE FLASHED{Fore.WHITE}')
        time.sleep(2)
    if args.test:
        test_keys()
        print(f'{Fore.BLUE}KEYS TEST PASSED{Fore.WHITE}')

    send_string(32) # Status OKAY
    print(f'{Fore.GREEN}###################')
    print(f'{Fore.GREEN}ALL STEPS PASSED!!!')
    print(f'{Fore.GREEN}###################')
