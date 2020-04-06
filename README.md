# Boosted Board Reverse Engineering
BeamBREak is an attempt at REing the various components of Boosted Board's electronics to keep boards running, due to their uncertian future.

Feel free to raise an issue or send me a message on Twitter [@robertscullin](https://twitter.com/robertscullin) if you have questions or more info.

## CAN Bus
The Boosted Board has two CAN Buses, running at 250kbaud. One is used for BMS<->ESC communication, and the other is used for the Accessory Port.

The `CAN Bus` folder has a DBC file, which is my attempt at making sense of the BMS<->ESC messages, and a README with more info about the physical connectors and research info. Right now, I only have partial mappings for the SR Battery, as the XR battery uses different messsage IDs.