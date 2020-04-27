# Boosted Board Reverse Engineering
BeamBREak is an attempt at REing the various components of Boosted Board's electronics to keep boards running, due to their uncertian future.

Feel free to raise an issue or send me a message on Twitter [@robertscullin](https://twitter.com/robertscullin) if you have questions or more info.

## Firmware
[Known Firmware Versions](Known%20Firmware%20Versions.md) is a list of V2+ firmware versions seen. Please note: as of April 2020, there is no known way to update you board or battery firmware, as Boosted shut down the authorization and firmware update server.

## CAN Bus
The Boosted Board has two CAN Buses, running at 250kbaud. One is used for BMS<->ESC communication, and the other is used for the Accessory Port.

The [CAN Bus](CAN%20Bus/) folder has a DBC file, which is my attempt at making sense of the BMS<->ESC messages, and a [README](CAN%20Bus/README.md) with more info about the physical connectors and research info. Right now, I only have partial mappings for the SR Battery, as the XR battery uses different message IDs.

Additionally, the Accessory port is partially documented, including an Arduino sketch to emulate the Beams.

## Batteries
The [Hardware](Hardware/) folder has information about the [XR battery pack](Hardware/XR%20Battery.md), including the cells and some of the major ICs used by the pack. I'll get photos of the internals of the battery shortly.