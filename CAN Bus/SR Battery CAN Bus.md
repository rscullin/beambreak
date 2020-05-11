# SR Battery CAN Bus

The SR Battery and ESC have about a dozen IDs they regularly send. Some of the messages have been decoded, while others are a mystery. This is fairly incomplete, but there's enough to emulate a battery and get the ESC to function.

This data is available as a [DBC File](SR_Battery.dbc), and is more or less the source of truth. If you have updates, please create an issue, and I'll update this table and the DBC file.

For physical connector information, see the [CAN Bus Readme](Readme.md). Data is sent at 250kbps, with Extended IDs.

## Warning
This info is provided as-is, with no guarantees or warranties, and is the result of staring at IDs and changing paramaters. You can potentially injure yourself or your board if you emulate a SR battery, as only "good" states have been understood. The ESC relies on the SR Battery to correctly report the SoC, and possibly other values -- if you only ever tell the ESC that the battery is at 50% (for example), it'll happily charge the pack when braking, possibly above a safe level. This information has been collected with my board in pieces on the floor, and not by riding. I don't know what happens if certain values are omitted or changed, and I suggest testing before relying on an emulated SR battery.


## SR Battery Emulation
[sr\_battery\_emulator.py](sr_battery_emulator.py) is a Proof of Concept SR Battery Emulator, that works well enough to get the wheels to spin on the Board. Out of the box, it will emulate a SR battery at 42% SoC, and sends enough messages to satisfy the ESC' internal sanity and safety checks.

I used a SR Battery with the CAN Bus disconnected to provide power while testing. You _can_ use a bench power supply, but be mindful that the motors will regen on coast, and most power supplies won't handle that well. Any power source in the ~35-40V range should be fine.


You'll need `python-can` and a supported CAN interface to use it -- see the file for more info on running and configuring it.


## Table of Known SR/ESC Message IDs
**Note:** "Essential" is from the perspective of "what is needed to make the ESC work". One-shots may not be essential, but they're easy enough to send and mostly figured out.

**Note 2:** IDs that end in `n` use a rolling ID -- they'll start at a value, and each subsequent message increments the ID until it hits `F`, then it rolls back over to `0`.


| ID         | Source | Frequency     | Essential   | Len | Description (ish)                                          |
| ---------- | ------ | ------------ | ----------- | --- | --------------------------------------------------------- |
| 0x0B57ED00 | SR     | One Shot     |             | 8   | Batt version                                         |
| 0x0B57ED01 | SR     | One Shot     |             | 8   | Batt SN                                                          |
| 0x0B57ED02 | SR     | 0.25s        | Y           | 8   |                                                           |
| 0x0B57ED03 | SR     | One Shot     |             | 8   |                                                           |
| 0x0B57ED0F | ESC    | One Shot     |             | 8   | ESC Version + SN                                          |
| 0x0B57ED10 | SR     | 0.25s        | Y           | 8   |                                                           |
| 0x0B57ED11 | SR     | 2s           | N           | 8   |                                                           |
| 0x0B57ED12 | SR     | 0.25s        | N           | 8   |                                                           |
| 0x0B57ED13 | SR     | 0.25s        | N           | 8   |                                                           |
| 0x0B57ED14 | SR     | 0.25s        | N (But yes) | 8   | State of Charge                                           |
| 0x0B57ED15 | SR     | 0.1s         |             | 8   | Charge status, counter, rnd?                              |
| 0x0B57ED1F | ESC    | 0.1s         | Y*          | 8   | ESC Power Control / Ping. W/O, SR shuts down after 10 min.
| 0x0B57EDC0 | SR     | Event        |             | 8   | SR Button Presses Counter, BT Pair                                 |
| 0x0B57EDC1 | ESC    | Event        | N           | 8   | SR Batt LED Control (Blue/Green/Blue pulse)               |
| 0x0B57EDC2 | SR     | 1s           |             | 8   |                                                           |
| 0x1034316n | ESC    |              | N           | 3   |                                                           |
| 0x1034344n | ESC    |              | N           | 8   | ESC Version + SN -- May only be sent if a SR battery isn't attached ? |
| 0x103B31An | ESC    | Event, Start | N           | 3   | Current Speed Mode, more?                                 |

## Description of Message IDs
**Note:** This isn't a full list -- the DBC file is the source of truth. Consider this annotations for things that might not be obvious.

### `0x0B57ED00` - SR Firmware Version
 Len 8, sent on power on by SR
 
```
01 04 01 33 66 34 35 31
      ^^ SR Battery Point Version (1)
   ^^ SR Battery Minor Version (4)
^^ SR Battery Major Version (1)
```

### `0x0B57ED01` - SR Serial
 Len 8, sent on power on by SR
 
```
EE FF C0 00 F7 8A 01 01
^^ ^^ ^^ ^^ SR Serial, "00 C0 FF EE"
```

### `0x0B57ED02` - SR Motor Engage Health Check?
 Len 8, sent every 0.25s by SR
 
```
00 00 C4 09 00 00 00 00
No idea. Without this, wheels won't "engage"
```

### `0x0B57ED0F` - ESC Version and Serial
 Len 8, sent one shot by ESC
 
```
02 07 02 01 EE FF C0 DA
            ^^ ^^ ^^ ^^ ESC Serial, "DAC0FFEE"
      ^^ ESC Point Version (2)
   ^^ ESC Minor Version (7)
^^ ESC Major Version (2)
```

### `0x0B57ED10` - SR Battery Voltages
 Len 8, sent every 0.25s by SR
 
```
F5 0C 00 0D CD 9B 00 00
            ^^ ^^ Total Pack Voltage (39.885V), in millivolts (39885), Little Endian
      ^^ ^^ Highest Cell Voltage (3.328V), in millivolts (3328), Little Endian
^^ ^^ Lowest Cell Voltage (3.317V), in millivolts (3317), Little Endian
```

### `0x0B57ED14` - SR Battery SoC
 Len 8, sent every 0.25s by SR
 
```
D2 08 C4 09 5A 00 05 00
            ^^ Battery SoC (90%), 0-100, in hex
```


### `0x0B57ED1F` - ESC Power Control / Ping
Len 8, sent every 0.1s by ESC

```
00 00 00 00 00 00 00 00
^^ "Stay Powered On" -- needed to prevent SR battery from showing CAN error and idle shutting off after 10 minutes.

02 00 00 00 00 00 00 00
^^ SR Battery Power Off Command, as if the user turned off the Board via the remote

```

### `0x0B57EDC0` - SR Button Presses and Initiate BLE Pairing
 Len 8, sent on demand by SR
 
```
03 00 00 00 00 00 00 00
^^ Number of button presses (3), which counts up when pressed or held.

05 0E 00 00 00 00 00 00
   ^^ Initiate Bluetooth Pairing.
^^ Number of button presses (5)   
```

### `0x0B57EDC1` - SR Power LED Control
 Len 8, sent on demand by ESC
  
```
D0 07 00 00 01 00 00 00
             ^ LED Effect. 0 is Solid Green, 1 is Blue Breathing, 2 is Blue Solid
   ^^ Effect duration. LED will revert to green after this. No idea what the units are.  
```


### `0x103B31An` - Board Mode?
This appears to be board mode (speed) with more data. Not sure enough to know. Also not entirely sure why the battery needs to know the current mode, but it does.