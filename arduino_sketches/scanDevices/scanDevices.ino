/* MPU9250 Basic Example Code
 by: Kris Winer
 date: April 1, 2014
 license: Beerware - Use this code however you'd like. If you
 find it useful you can buy me a beer some time.
 Modified by Brent Wilkins July 19, 2016

 Demonstrate basic MPU-9250 functionality including parameterizing the register
 addresses, initializing the sensor, getting properly scaled accelerometer,
 gyroscope, and magnetometer data out. Added display functions to allow display
 to on breadboard monitor. Addition of 9 DoF sensor fusion using open source
 Madgwick and Mahony filter algorithms. Sketch runs on the 3.3 V 8 MHz Pro Mini
 and the Teensy 3.1.

 SDA and SCL should have external pull-up resistors (to 3.3V).
 10k resistors are on the EMSENSR-9250 breakout board.

 Hardware setup:
 MPU9250 Breakout --------- Arduino
 VDD ---------------------- 3.3V
 VDDI --------------------- 3.3V
 SDA ----------------------- A4
 SCL ----------------------- A5
 GND ---------------------- GND
 */

#include "quaternionFilters.h"
#include "MPU9250.h"

// Select SDA and SCL pins for I2C communication 
const uint8_t scl = D6;
const uint8_t sda = D7;

#define AHRS true         // Set to false for basic data read
#define SerialDebug true  // Set to true to get Serial output for debugging

// Pin definitions
int intPin = 12;  // These can be changed, 2 and 3 are the Arduinos ext int pins
int myLed  = 13;  // Set up pin 13 led for toggling

MPU9250 myIMU;

void setup()
{  
  Wire.begin(sda,scl);
  // TWBR = 12;  // 400 kbit/sec I2C speed
  Serial.begin(115200);


  // scan for i2c devices
  byte error, address;
  int nDevices;

  Serial.println("Scanning...");

  nDevices = 0;
  for(address = 1; address < 127; address++ )
  {
    // The i2c_scanner uses the return value of
    // the Write.endTransmisstion to see if
    // a device did acknowledge to the address.
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0)
    {
      Serial.print("I2C device found at address 0x");
      if (address<16)
        Serial.print("0");
      Serial.print(address,HEX);
      Serial.println("  !");

      nDevices++;
    }
    else if(error == 4)
    {
      Serial.print("Unknow error at address 0x");
      if (address<16)
        Serial.print("0");
      Serial.println(address,HEX);
    }
  }
  if (nDevices == 0)
    Serial.println("No I2C devices found\n");
  else
    Serial.println("done\n");


  
  // Read the WHO_AM_I register, this is a good test of communication
  byte c = myIMU.readByte(0x68/*MPU9250_ADDRESS*/, WHO_AM_I_MPU9250);
  byte d = myIMU.readByte(0x69/*MPU9250_ADDRESS*/, WHO_AM_I_MPU9250);
  Serial.print("MPU9250:top "); Serial.print("I AM "); Serial.print(c, HEX);
  Serial.print(" I should be "); Serial.println(0x73, HEX); 
  Serial.print("MPU9250:down "); Serial.print("I AM "); Serial.print(d, HEX);
  Serial.print(" I should be "); Serial.println(0x73, HEX);

  if (c == 0x73 && d == 0x73) // WHO_AM_I should always be 0x73
  {
    Serial.println("both MPU9250 are online...");

  }
  else
  {
    Serial.print("Could not connect to MPU9250:top 0x");
    Serial.println(c, HEX);
    Serial.print("Could not connect to MPU9250:down 0x");
    Serial.println(d, HEX);
    while(1) ; // Loop forever if communication doesn't happen
  }
}

void loop()
{
}
