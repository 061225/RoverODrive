#!/usr/bin/env python3
import odrive
from odrive.enums import *

from UDPComms import Subscriber, Publisher, timeout
import time

import os
import threading

if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

cmd = Subscriber(8830, timeout = 0.3)
telemetry = Publisher(8810)

odrives = [ ['front' , "206C35733948", [-1, -1, 1, -1]],
            ['middle', "206230804648", [ 1,  1, 1, -1][]],
            ['back'  , "207D35903948", [-1, -1, 1, -1]] ]

def clear_errors(odrive):
    if odrive.axis0.error:
        print("axis 0", odrive.axis0.error)
        odrive.axis0.error = 0
    if odrive.axis1.error:
        print("axis 1", odrive.axis1.error)
        odrive.axis1.error = 0

    if odrive.axis0.motor.error:
        print("motor 0", odrive.axis0.motor.error)
        odrive.axis0.motor.error = 0
    if odrive.axis1.motor.error:
        print("motor 1", odrive.axis1.motor.error)
        odrive.axis1.motor.error = 0

    if odrive.axis0.encoder.error:
        print("encoder 0", odrive.axis0.encoder.error)
        odrive.axis0.encoder.error = 0
    if odrive.axis1.encoder.error:
        print("encoder 1", odrive.axis1.encoder.error)
        odrive.axis1.encoder.error = 0

def send_state(odrive, state):
        try:
            odrive.axis0.requested_state = state
        except:
            pass
        try:
            odrive.axis1.requested_state = state
        except:
            pass

def get_data(odrive):
        return [odrive.vbus_voltage,
                odrive.axis0.motor.current_control.Iq_measured,
                odrive.axis1.motor.current_control.Iq_measured]

def atomic_print(s):
    print(str(s)+'\n',end='')


def run_odrive(name, serial_number, d):
    # USBLock.acquire()
    atomic_print("looking for "+name+" odrive")
    odrive = odrive.find_any(serial_number=serial_number)
    atomic_print("found " +name+ " odrive")
    send_state(odrive, AXIS_STATE_IDLE)
    # USBLock.release()

    while True:
        try:
            UDPLock.acquire()
            msg = cmd.get()
            UDPLock.release()
            atomic_print(msg)
            clear_errors(odrive)

            if (msg['t'] == 0 and msg['f'] == 0):
                send_state(odrive, AXIS_STATE_IDLE)
            else:
                send_state(odrive, AXIS_STATE_CLOSED_LOOP_CONTROL)
                odrive.axis0.controller.vel_setpoint =  d[0]*msg['f'] +d[1]*msg['t'] 
                odrive.axis1.controller.vel_setpoint =  d[2]*msg['f'] +d[3]*msg['t']
                odrive.axis0.watchdog_feed()
                odrive.axis1.watchdog_feed()

        except timeout:
            atomic_print("Sending safe command")
            send_state(odrive, AXIS_STATE_IDLE)
            odrive.axis0.controller.vel_setpoint = 0
            odrive.axis1.controller.vel_setpoint = 0
        except AttributeError:
            atomic_print("Lost contact with "+name+" odrive!")
            odrive = odrive.find_any(serial_number=serial_number)
            atomic_print("found " + name + " odrive")

        except:
            atomic_print("shutting down "+ name)
            send_state(drive, AXIS_STATE_IDLE)
            odrive.axis0.controller.vel_setpoint = 0
            odrive.axis1.controller.vel_setpoint = 0
            raise
        finally:
            atomic_print("Exiting and Sending safe command")
            send_state(odrive, AXIS_STATE_IDLE)
            odrive.axis0.controller.vel_setpoint = 0
            odrive.axis1.controller.vel_setpoint = 0

if __name__ == "__main__"
    # USBLock = threading.Lock()
    UDPLock = threading.Lock()
    for odrive in odrives:
        thread = threading.Thread(target=run_odrive, arg=odrive daemon=True)
        thread.start()

    # if any thread shuts down (which it shouldn't) we exit the program
    # which exits all other threads to 
    while threading.active_count() == 4:
        pass