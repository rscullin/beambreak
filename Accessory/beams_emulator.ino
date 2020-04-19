// Boosted Beams Emulator PoC
// Copyright Robert Scullin, 2020
// Released under the GPLv3 -- see the end of the file the full GPLv3 header
// https://github.com/rscullin/beambreak / https://twitter.com/robertscullin

// This emulates the Boosted Beam Headlights, and control a strip of
// "Neopixel"-style addressable LEDs. It supports on/off/dimming, and will
// change the color of one LED when "off" to show CAN Bus traffic.

// This code has been tested on an Arduino Uno, with a generic MCP2515 board,
// and 8 WS2812B addressable LEDs on a strip.

// To run, you'll need libraries from:
// * https://github.com/FastLED/FastLED/
// * https://github.com/autowp/arduino-mcp2515

// Setup Pixel LED Library
#include <FastLED.h>
// And undefine SPI_CLOCK as it conflicts with the MCP2525 Library
#undef SPI_CLOCK

// Set up MCP2525 Library
#include <can.h>
#include <mcp2515.h>

// LED Setup
#define NUM_LEDS 8
#define DATA_PIN 6 // Neopixel data line
CRGB leds[NUM_LEDS];

// MCP2525 Setup
MCP2515 mcp2515(10); // MCP2525 CS Pin
struct can_frame frame;

void setup()
{
  // Initialize the LED Library
  delay(100);
  FastLED.addLeds<NEOPIXEL, DATA_PIN>(leds, NUM_LEDS);
  // Set a status LED to indicate it's initalized
  leds[0] = CHSV(125, 255, 40);
  FastLED.show();

  // Initalize the MCP2525 Library
  mcp2515.reset();
  // The Boosted Board uses 250kbps
  // Also, MCP_8MHZ is _vital_ for the Arduino UNO
  mcp2515.setBitrate(CAN_250KBPS, MCP_8MHZ);
  mcp2515.setNormalMode();

  delay(100);

  // Send the Boosted Accessory Handshake, as a Headlight
  frame.can_id = 0x10339200 | CAN_EFF_FLAG;
  frame.can_dlc = 8;
  frame.data[0] = 0xFE; // Accessory Init
  frame.data[1] = 0x00;
  frame.data[2] = 0x00;
  frame.data[3] = 0x00;
  frame.data[4] = 0x00;
  frame.data[5] = 0x00;
  frame.data[6] = 0x37; // Serial, LSB
  frame.data[7] = 0x13; // Serial, MSB
  mcp2515.sendMessage(&frame);

  // Set a Status LED to indicate we've sent the init frame
  leds[1] = CHSV(150, 255, 40);
  FastLED.show();
}

static uint8_t hue = 0;
bool headlightsOn = false;

void loop()
{

  // Read a frame...
  if (mcp2515.readMessage(&frame) == MCP2515::ERROR_OK)
  {
    // And do something it's valid

    // Cmd messages have a DLC of 8, and the 2nd byte is 0x4
    if (frame.can_dlc == 8 && frame.data[1] == 0x04)
    {
      // This is an On command
      if (frame.data[2] == 0x22)
      {
        FastLED.showColor(CRGB(frame.data[3], frame.data[3], frame.data[3]));
        headlightsOn = true;
      }
      // This is an Off command
      else if (frame.data[2] == 0x23)
      {
        leds[0] = CHSV(hue, 255, 25);
        FastLED.show();
        headlightsOn = false;
      }
    }
    // If headlights are off, and we get a CAN frame, cycle the status LED's
    // color
    else if (!headlightsOn)
    {
      hue = hue + 9;
      leds[7] = CHSV(hue, 255, 40);
      FastLED.show();
    }
  }
}

/*
 *   This program is free software: you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published by
 *   the Free Software Foundation, either version 3 of the License, or
 *   (at your option) any later version.
 *
 *   This program is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *   GNU General Public License for more details.
 *
 *   You should have received a copy of the GNU General Public License
 *   along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */
