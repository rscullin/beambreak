#!/usr/bin/env python3
import argparse
import sys
import can
from print_color import print
from struct import *

# Released under the MIT License. Copyright (c) 2023 Robert Scullin.
# https://beambreak.org / https://github.com/rscullin/beambreak

# pip3 install print_color python_can

# This script resets Boosted Board XR RLOD error conditions, usually caused by cell voltage imbalance.
# It also shows the voltages of all cells, as reported by the TI Battery Monitor ("AFE").
#
# If the cell delta is >500mV, the script doesn't bother trying to clear the error.
# NOTE that the pre-check has the potential to give a false positive -- if a cell is very out of spec (ex: 1.5v),
# the CAN Bus messages might not include that value in the lowest cell voltage.
# Nothing bad happens if you reset in this state, as the power cycle causes the battery to go back to RLOD.
#
# Technically this clears _all_ faults, but theoretically if they're catastrophic they'll
# get thrown again.
#
# This is, of course, at your own risk.

# This script uses python-can -- see https://python-can.readthedocs.io/en/stable/configuration.html
# for more information for your particular adapter.
#
# If you're using a `slcan`-based device, the "channel" is the path to the serial port.


def send_cli_command(can_interface: can.Bus, message: str):
    """
    Sends an ASCII command to the Battery's Serial/CLI Interface
    """

    # Add newline after the command
    message = message + "\r\n"

    can_cmd_bytes = bytearray()
    can_cmd_bytes.extend(message.encode())

    arbitration_base = 0x10246110

    # Single-line and multi-line cmds go to different "Long Command" addresses
    # 3 for single-line, 2->0 for multi-line, decremented every 8 bytes sent
    if len(can_cmd_bytes) <= 8:
        arbitration_base = arbitration_base + 0x100000

    # Send in 8 byte segments
    n = 8
    for i in range(0, len(can_cmd_bytes), n):
        can_cmd = can_cmd_bytes[i:i + n]

        section = int(i / 8)

        # Decrement the Long Command half-byte for every message sent that's grouped together,
        # And also increment the trailing rolling code
        arbitration_id = arbitration_base - (section * 0x100000) + section

        serial_cmd = can.Message(
            arbitration_id=arbitration_id, data=can_cmd, is_extended_id=True
        )
        can_interface.send(serial_cmd)


def util(arguments):
    with can.interface.Bus(bustype=arguments.interface, channel=arguments.channel, bitrate=250000) as bus:

        print(f"CAN Adapter Initialized! {arguments.interface} at {arguments.channel}")
        print()
        print("Waiting on CAN msg...")

        wait_for_initial_msg = True

        while wait_for_initial_msg:

            msg = bus.recv(1)
            if msg is not None:
                wait_for_initial_msg = False

        print("Got a message!")
        print()
        print("Waiting ~10 seconds for the battery to boot and start sending valid data.")

        # Enable Message Routing from the Battery to the CAN Bus
        bus.send(can.Message(arbitration_id=0x10346090, data=[0x01], is_extended_id=True))

        # Enable periodic keep-alive messages so that the Battery thinks there's an ESC connected
        bus.send_periodic(can.Message(arbitration_id=0x103434B0,
                                      data=[0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
                                      is_extended_id=True
                                      ), 1)

        # State management...
        enable_commands = False
        checked_voltage = False
        sent_reset = False
        should_exit = False

        # This is used as a makeshift "timer" throughout the code.
        # It's not ideal, but it is easy.
        can_frames_seen = 0

        try:
            while True:
                msg = bus.recv(1)
                if msg is not None:

                    can_frames_seen = can_frames_seen + 1

                    # Set the Long Command bits and the Rolling Code bits to 0 to make code saner
                    msg.arbitration_id = msg.arbitration_id & 0xFF0FFFF0

                    # Wait for the Battery to boot
                    if can_frames_seen > 10 * 250:
                        enable_commands = True

                    if enable_commands and not checked_voltage:
                        if msg.arbitration_id == 0x10034450:
                            checked_voltage = True
                            sent_reset = True

                            send_cli_command(bus, "GETAFECELLS")

                            cell_lowest_mv, cell_highest_mv, cell_total_mv = unpack('<HHHxx', msg.data)
                            cell_delta = cell_highest_mv - cell_lowest_mv

                            print("\n\nNOTE! For some reason the battery doesn't correctly report extremely out of spec"
                                  " cell voltages via CAN messages.\n"
                                  "Check the results of the individual cell voltages for more info.\n")

                            print(f"== Cell Voltages ==\n"
                                  f"- Lowest: {cell_lowest_mv}mV\n"
                                  f"- Highest: {cell_highest_mv}mV\n"
                                  f"- Total: {cell_total_mv}mV\n"
                                  f"\n"
                                  f"- Delta: {cell_delta}mV\n")

                            # The battery uses a 500mV delta as the RLOD condition
                            # If the battery actually has a > 500mV delta but doesn't correctly report it,
                            # resetting the error state will result in the error again on next power cycle
                            if cell_delta < 500:
                                print(f"Delta looks good ({cell_highest_mv - cell_lowest_mv}mV)!\n", color="green")
                                print(f"Sending `PFAILRESET` and restarting the battery.", color="green")
                                send_cli_command(bus, "PFAILRESET")
                                wait_until_frame = can_frames_seen + 1000
                            else:
                                print(f"The cell delta is too high! - {cell_highest_mv - cell_lowest_mv}mV "
                                      f"- Resetting can't fix this, so not going to attempt.\nExiting.", color="red")
                                # Set a delayed exit so that the CLI output of GETAFECELLS can be presented
                                wait_until_frame = can_frames_seen + 1000
                                should_exit = True

                    if sent_reset and not should_exit and can_frames_seen > wait_until_frame:
                        send_cli_command(bus, "REBOOT")
                        print(f"Done!", color="green")
                        wait_until_frame = can_frames_seen + 1000
                        should_exit = True

                    if should_exit and can_frames_seen > wait_until_frame:
                        # Send the command to power off the battery if the user wants
                        if arguments.power_off:
                            bus.send(can.Message(
                                arbitration_id=0x103434B0,
                                data=[0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
                                is_extended_id=True
                            ))
                        sys.exit()

                    # CLI Print handling
                    if msg.arbitration_id & 0x00000FF0 == 0x00000110:
                        try:
                            dec = msg.data.decode("ascii")
                            print(dec, end='', color='blue')
                        except UnicodeDecodeError:
                            # This is here to consume any weirdness of non-ascii characters
                            # This might not even be necessary anymore.
                            continue

        # Handle ctrl-c
        except KeyboardInterrupt:
            print()
            print("Program interrupted, exiting.")
            sys.exit()
            pass  # exit normally


if __name__ == "__main__":

    print("Boosted Board XR Battery Utility, v1")
    print("https://beambreak.org / https://github.com/rscullin/beambreak")
    print("")

    parser = argparse.ArgumentParser(
        prog='xr_battery_util.py',
        description='Resets RLODs on Boosted Board XR Batteries, via a CAN Bus Connection.'
                    'If the cell delta is > 500mV, the RLOD will return on power cycle.')

    parser.add_argument('-i',
                        '--interface',
                        help='Name of the `python-can` interface to use. Defaults to `slcan`',
                        default="slcan")
    parser.add_argument('-c',
                        '--channel',
                        help='"Channel" of the `python-can` interface to use. If you are using `slcan`, this is the '
                             'path to the serial adapter.',
                        default="/dev/tty.usbmodem1101",
                        required=False)
    parser.add_argument('-p',
                        '--power-off',
                        help='Power off the battery at the end of the script',
                        required=False,
                        default=False,
                        action='store_true')

    args = parser.parse_args()

    try:
        util(args)
    except KeyboardInterrupt:
        sys.exit()

# MIT License
#
# Copyright (c) 2023 Robert Scullin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
