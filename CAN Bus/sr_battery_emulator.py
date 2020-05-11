#!/usr/bin/env python3

# Boosted Boards SR Battery Emulator, v1
# Copyright Robert Scullin, 2020
# https://github.com/rscullin/beambreak/
# Released under the GPLv3 -- see footer for license statement

####################    IMPORTANT SAFETY INFORMATION    ####################

# There is NO WARRANTY whatsoever, and you are responsible for using this
# safely. I don't know what some of the messages mean, and this code
# only handles the "happy path" of needed messages. You should thoroughly
# test this code and error conditions before using it on a board in motion.

# Additionally, the ESC trusts the BMS' State of Charge. If you incorporate
# this into a BMS, you _must_ accurately report the State of Charge, as the
# ESC will dump power into the battery forever unless you tell it it's full.

# The SR battery is designed for LiFePO4 batteries, which have different cell
# and pack voltages than a LiIon pack. I don't know what happens if you report
# a lower voltage than the pack is actually providing.

# Everything is at your own risk.

####################  END IMPORTANT SAFETY INFORMATION  ####################

# This code pretends to be enough of a SR battery to get the ESC to let
# the motors engage. Nothing else is implemented, and I don't know what
# the remaining un-sent messages mean or do.

# You'll need python-can ( https://github.com/hardbyte/python-can ) ,
# ` pip3 install python-can `, and a supported CAN interface to use this code.
# This code was built and tested with a CANable Pro ( https://canable.io/ )
# under OS X, with the `slcan` firmware. Any other python-can supported
# interface should work, including SocketCAN devices under Linux.

# For more info on the CAN Ids and what they mean, please see the DBC
# file in the Beambreak repository.

import time

import can
from can.bus import BusState


# SR Variables
BatterySerial = [0x00, 0xC0, 0xFF, 0xEE]

MinCellMilliVolts = 3312    # 3312mV -> 3.312V
MaxCellMilliVolts = 3323    # 3323mV -> 3.323V
PackTotalMilliVolts = 39867 # 39867mV -> 39.867V

BatterySoCLevel = 42        # Max of 100


# Array conversions for later
MinCellMVArray = MinCellMilliVolts.to_bytes(2, 'big')
MaxCellMVArray = MaxCellMilliVolts.to_bytes(2, 'big')
PackTotalMVArray = PackTotalMilliVolts.to_bytes(2, 'big')


print("Boosted SR Battery Emulator, v1")
print("https://github.com/rscullin/beambreak")
print()
print("Starting up...")

def tx():

    # You'll need to change this to whatever interface you're using
    # See https://python-can.readthedocs.io/en/master/interfaces.html for help
    with can.interface.Bus(
        bustype="slcan", channel="/dev/tty.usbmodem14101", bitrate=250000
    ) as bus:
        
        print("CAN Bus initialized!")
        print("Waiting on a message from the ESC to continue")

        waitForInitialMsg = True

        while waitForInitialMsg:

            msg = bus.recv(1)
            if msg is not None:
                waitForInitialMsg = False
                time.sleep(0.25)
        
        print("Got a CAN message; starting simulation!")

        # One Shot

        ## Major, Minor, Revision, Unknown ->
        ID_00_batt_fw = can.Message(
            arbitration_id=0x0B57ED00, data=[0x01, 0x04, 0x01, 0x33, 0x66, 0x34, 0x35, 0x31], is_extended_id=True
        )

        # Battery Serial, Unknown ->
        ID_01_batt_sn = can.Message(
            arbitration_id=0x0B57ED01, data=[BatterySerial[3], BatterySerial[2], BatterySerial[1], BatterySerial[0], 0xf7, 0x8a, 0x01, 0x01], is_extended_id=True
        )

        ## Unknown ->
        ID_03 = can.Message(
                arbitration_id=0x0B57ED03, data=[0xD2, 0x0F, 0xCA, 0x08, 0x0C, 0x00, 0x00, 0x00], is_extended_id=True
        )

        bus.send(ID_00_batt_fw)
        bus.send(ID_01_batt_sn)
        bus.send(ID_03)

        try:
            print("Sending messages every 250ms forever...")
            while 1 == 1:
                
                print(".", end='')
                ## Unknown ->
                ID_02_motor_a = can.Message(
                    arbitration_id=0x0B57ED02, data=[0x00, 0x00, 0xC4, 0x09, 0x00, 0x00, 0x00, 0x00], is_extended_id=True
                )

                ## Lowest Cell millivolts, Highest Cell millivolts, Total Pack millivolts, Zero->
                ID_10_batt_info = can.Message(
                    arbitration_id=0x0B57ED10, data=[MinCellMVArray[1], MinCellMVArray[0], MaxCellMVArray[1], MaxCellMVArray[0], PackTotalMVArray[1], PackTotalMVArray[0], 0x00, 0x00], is_extended_id=True
                )

                #Unknowns, SoC level, Unknowns
                ID_14_batt_lvl = can.Message(
                    arbitration_id=0x0B57ED14, data=[0x9B, 0x07, 0xC4, 0x09, BatterySoCLevel, 0x00, 0x05, 0x00], is_extended_id=True
                )

                # Battery charging state, Unknown->
                ID_15_batt_chrg = can.Message(
                    arbitration_id=0x0B57ED15, data=[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7F, 0x00], is_extended_id=True
                )

                bus.send(ID_02_motor_a)
                bus.send(ID_10_batt_info)
                bus.send(ID_14_batt_lvl)
                bus.send(ID_15_batt_chrg)


                time.sleep(0.25)
        except KeyboardInterrupt:
            print()
            print('Done.')



if __name__ == "__main__":
    tx()
