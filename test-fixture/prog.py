#!/bin/python3

# Script to program and test sea-micro

import os
import time
import argparse
from colorama import Fore
import serial
from serial.tools import list_ports
import io
from multiprocessing import Process

def bootloader():
    ''' Flashes bootloader, using an external programmer connected to the ISP port on the test fixture.
        Defaults to AVRISPMKII, but can be used with a usbasp by changing the arg to -c.'''
    global mcu_reset
    mcu_reset = True

    bootloader = "avrdude -C avrdude.conf -v -p atmega32u4 -c avrispmkii -P usb -U flash:w:bootloader_atmega32u4_1.0.0.hex:i -U lfuse:w:0x5E:m -U hfuse:w:0xD9:m -U efuse:w:0xC3:m"
    
    retval = os.system(bootloader)

    if retval != 0:
        send_string(33) # Error
        print(f'{Fore.RED}#############################')
        print(f'{Fore.RED}FAIL AT WRITING BOOTLOADER!!!')
        print(f'{Fore.RED}#############################')
        exit()

    print(f'{Fore.BLUE}BOOTLOADER FLASHED{Fore.WHITE}')

def test_firmware():
    ''' Flash Test Firmware. Assumes atmel-dfu bootloader is already flashed to board. '''
    global mcu_reset

    if mcu_reset == False:
        send_string(255) # Hard reset
        mcu_reset = True
        time.sleep(2)

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
        mcu_reset = True
        retval = os.system(reset)

    if (retval != 0) and (retval != 256): # For some reason the reset retval is 256 on success
        send_string(33) # Error
        print(f'{Fore.RED}############################')
        print(f'{Fore.RED}FAIL AT FLASHING TEST FW !!!')
        print(f'{Fore.RED}############################')
        exit()

    print(f'{Fore.BLUE}TEST FIRMWARE FLASHED{Fore.WHITE}')

def send_string(string):
    serial_io.write(str(string) + "\r\n")
    serial_io.flush()

def test_keys():
    ''' Test all IO with test fixture.
        Transmit number according to pin location, which test fixture will pull low, simulating key press.
        DUT will then respond with the alpha character (A=1, B=2 etc) which we can check. '''
    global mcu_reset

    # Ensure board is out of reset
    if (mcu_reset == False):
        print(f'{Fore.BLUE}ENSURING 32U4 READY{Fore.WHITE}')
        os.system("dfu-programmer atmega32u4 reset")
        time.sleep(1)

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

    print(f'{Fore.BLUE}KEYS TEST PASSED{Fore.WHITE}')

if __name__ == "__main__":

    # Connect to test fixture
    serial_io = None
    uart = serial.Serial("/dev/ttyACM0", 115200, timeout=0.1)
    serial_io = io.TextIOWrapper(io.BufferedRWPair(uart, uart))

    # State if board is fresh or already has test FW on there
    mcu_reset = False

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--bootloader",    action='store_true')
    parser.add_argument("-f", "--qmk_firmware",  action='store_true')
    parser.add_argument("-t", "--test",          action='store_true')
    args = parser.parse_args()

    send_string(34) # Reset status LEDs

    if args.bootloader:
        bootloader()
        time.sleep(2)
    if args.qmk_firmware:
        test_firmware()
        time.sleep(2)
    if args.test:
        test_keys()        

    send_string(32) # Status OKAY
    print(f'{Fore.GREEN}###################')
    print(f'{Fore.GREEN}ALL STEPS PASSED!!!')
    print(f'{Fore.GREEN}###################{Fore.WHITE}')
