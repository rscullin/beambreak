# XR Battery
## Component Overview
The XR Battery (B2XR) is a 13S2P battery pack, with [LG INR18650HG2](https://12u5i3qsp9y22yzjwn5z1lil-wpengine.netdna-ssl.com/wp-content/uploads/2019/07/B2XR-MSDS.pdf) cells.

The main micrcontroller is a [Microchip dsPIC33EP512GP504](https://www.microchip.com/wwwproducts/en/dsPIC33EP512GP504), and has an [ISSI IS25LP128](http://www.issi.com/WW/pdf/IS25LP128.pdf) 128Mbit/16Mbyte flash chip connected via SPI.

Battery balancing and monitoring is handled by a [TI BQ76940](http://www.ti.com/lit/ds/symlink/bq76940.pdf), with a [TI BQ76200](http://www.ti.com/lit/ds/symlink/bq76200.pdf) acting as the main pack MOSFET monitor/controller.

## Notes
The charging input and board output are both switched by the MCU, and default to being open -- unlike the V1 boards, you can't charge a V2 XR pack if it's dead by spinning the motors to backfeed the battery.

The top side of the BMS board is covered in a non-laquer based conformal coating, with a moat to prevent it from covering test pads or the main board connections. You can peel/chip it away with a bit of effort.

Opening the XR battery involves a lot of pyring and unpleasant popping noises as the glue gives way. I used car [trim panel opening tools](https://www.crutchfield.com/S-8vtQidc32B1/p_126CR6LNGL/Bojo-Trim-Panel-Tools.html) for most of the prying/case seperating, and then resorted to a flat head screwdriver to give it the final nudge to be able to pull the pack from the housing. [This YouTube video](https://www.youtube.com/watch?v=XqM4JGT5Mbk) was my reference for opening the pack, albeit with less prying with a metal screwdriver.