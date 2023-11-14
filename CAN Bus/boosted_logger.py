#!/usr/bin/env python3
import datetime
import argparse
import sys
import can

# Released under the MIT License. Copyright (c) 2023 Robert Scullin.
# https://beambreak.org / https://github.com/rscullin/beambreak

# pip3 install python_can

# This script is a helper for logging Boosted Board CAN Bus traffic.
#
# The CAN IDs have multiple changing components which can be ignored when analyzing data.
#
# Example:
#
#  0xFF0FFFF0 - Mask used for filtering
#  0x10374200
#           ^ Global rolling code, 0-F, every message sent by the device increments this
#       ^^^^ Src, Dest, Channel
#      ^ "Long Command" ID -- Starts at 3, decrements for messages that span multiple packets
#
# The Boosted Board systems use a rolling 0-F trailing ID as they transmits CAN Frames --
# ex: 0x10374200, 0x10234171, 0x10134172, 0x10334453, 0x10374204, etc.
#
# This makes analysis harder, as the same base messages ID will have different trailing IDs.
# This script "normalizes" all trailing 0-F IDs into a single 0 ID, as well as preserving
# the original IDs in a separate file.
#
# Additionally, the script normalizes the "Long Command" ID to always be 0. This is normally "3",
# but is decremented with multipart / long messages, to indicate that it's part of the same
# transmission.
#
# This script uses python-can -- see https://python-can.readthedocs.io/en/stable/configuration.html
# for more information for your particular adapter.
#
# If you're using a `slcan`-based device, the "channel" is the path to the serial port.


def log(arguments):
    with can.interface.Bus(bustype=arguments.interface, channel=arguments.channel, bitrate=250000) as bus:

        print(f"CAN Adapter Initialized! {arguments.interface} at {arguments.channel}")

        dt = datetime.datetime.now()
        logger_all = can.CanutilsLogWriter(f"{arguments.directory}/boosted_log_{dt.strftime('%s')}_all.log")
        logger_mod = can.CanutilsLogWriter(f"{arguments.directory}/boosted_log_{dt.strftime('%s')}_MOD.log")

        print(f"Logs opened as [boosted_log_{dt.strftime('%s')}_***_.log] -- Logging started!")

        can_frames_seen = 0

        print()

        try:
            while True:
                msg = bus.recv(1)
                if msg is not None:

                    can_frames_seen = can_frames_seen + 1

                    # Print a '.' every 250 frames to show _something_ is happening
                    if can_frames_seen % 250 == 0:
                        print('.', end="", flush=True)

                    logger_all.on_message_received(msg)

                    # Set the Long Command bits and the Rolling Code bits to 0 to make DBC Analysis saner
                    msg.arbitration_id = msg.arbitration_id & 0xFF0FFFF0
                    logger_mod.on_message_received(msg)

        except KeyboardInterrupt:
            logger_all.stop()
            logger_mod.stop()

            print()
            print()
            print(f"Logging stopped, received {can_frames_seen} frames.")

            pass  # exit normally


if __name__ == "__main__":

    print("Boosted Board CAN Bus Logger v1")
    print("https://beambreak.org / https://github.com/rscullin/beambreak")
    print("")

    parser = argparse.ArgumentParser(
        prog='boosted_logger.py',
        description='Logs Boosted Board CAN frames to disk as a `can-utils` log file (.log). Logs to both modified '
                    '(converts the rolling address to a fixed 0) and unmodified log files.',
        epilog='Prints a `.` every 250 received CAN frames.')

    parser.add_argument('-d',
                        '--directory',
                        help='Directory for writing log files. Defaults to the current directory.',
                        required=False,
                        default='./')
    parser.add_argument('-i',
                        '--interface',
                        help='Name of the `python-can` interface to use. Defaults to `slcan`',
                        default="slcan")
    parser.add_argument('-c',
                        '--channel',
                        help='"Channel" of the `python-can` interface to use. If you are using `slcan`, this is the '
                             'path to the serial adapter.',
                        required=True)

    args = parser.parse_args()

    try:
        log(args)
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
