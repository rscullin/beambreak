# Bus 1 - BMS <-> ESC

## CAN Bus Info
The CAN Bus runs at 250k baud, with extended message IDs. The `SR_Battery.dbc` file contains mappings that any CAN tool should be able to use to "make sense" of the CAN traffic.

## Physical Connectors
Boosted uses a [5-Pin Higo L513AM](https://www.higoconnector.com/products/l313am-p-00-ar-1000/LK99K#title) connector, with two (larger) pins for power, and three pins for CAN/connection detection.

The Battery uses a female Higo L513AM P 00 AT 1000, and the ESC uses a male Higo L513AM P 00 B0 1000.

## Electrical Connections
All of the following are based on the colors used by Higo.
* Red - Switched Battery Positive (~30-50v)
* Black - Ground
* Yellow - CAN High
* Green - CAN Low
* Blue - Connection Detection -- this is 3.3v when nothing is connected to the BMS, and pulled to ground by the ESC to let the BMS know that something is connected

# Bus 2 - ESC <-> Accessory
The CAN Bus runs at 250k baud, with extended message IDs. Without an accessory connected, nothing other than a heartbeat seems to be sent on the CAN Bus. The ESC will cut 15v power after ~10 seconds of no heartbeat replies, but will continue to send heartbeat CAN frames. Without the latest ESC firmware (V2.7.2), there is no traffic on the Accessory Bus, and 15v is never supplied.