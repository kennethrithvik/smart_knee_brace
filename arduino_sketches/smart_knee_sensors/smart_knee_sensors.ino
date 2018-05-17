/*
  Hardware setup:
  MPU9250 Breakout --------- NodeMCU
  VCC --------------------- 3.3V
  SDA ----------------------- D7
  SCL ----------------------- D6
  GND ---------------------- GND
*/

#include <string>
#include "quaternionFilters.h"
#include "MPU9250.h"
#include <ESP8266WiFi.h> // Enables the ESP8266 to connect to the local network (via WiFi)
#include <PubSubClient.h> // Allows us to connect to, and publish to the MQTT broker

// WiFi
// Make sure to update this for your own WiFi network!
const char* ssid = "ASUS";
const char* wifi_password = "83419486";
// MQTT
// Make sure to update this for your own MQTT Broker!
const char* mqtt_server = "192.168.1.190";
const char* mqtt_topic = "knee_brace_nodemcu";
const char* mqtt_username = "knee_brace";
const char* mqtt_password = "knee_brace";
// The client id identifies the ESP8266 device. Think of it a bit like a hostname (Or just a name, like Greg).
const char* clientID = "knee_brace_nodemcu";

// Initialise the WiFi and MQTT Client objects
WiFiClient wifiClient;
PubSubClient client(mqtt_server, 1883, wifiClient); // 1883 is the listener port for the Broker


// Select SDA and SCL pins for I2C communication
const uint8_t scl = D6;
const uint8_t sda = D7;

#define AHRS false         // Set to false for basic data read
#define SerialDebug true  // Set to true to get Serial output for debugging
#define MPU9250_ADDRESS 0x69

MPU9250 myTopIMU;
MPU9250 myBottomIMU;
void scanDevices()
{
  // scan for i2c devices
  byte error, address;
  int nDevices;

  Serial.println("Scanning...");

  nDevices = 0;
  for (address = 1; address < 127; address++ )
  {
    // The i2c_scanner uses the return value of
    // the Write.endTransmisstion to see if
    // a device did acknowledge to the address.
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0)
    {
      Serial.print("I2C device found at address 0x");
      if (address < 16)
        Serial.print("0");
      Serial.print(address, HEX);
      Serial.println("  !");

      nDevices++;
    }
    else if (error == 4)
    {
      Serial.print("Unknow error at address 0x");
      if (address < 16)
        Serial.print("0");
      Serial.println(address, HEX);
    }
  }
  if (nDevices == 0)
    Serial.println("No I2C devices found\n");
  else
    Serial.println("done\n");
}

void setup()
{
  Wire.begin(sda, scl);
  // TWBR = 12;  // 400 kbit/sec I2C speed
  Serial.begin(115200);

  //WIFI CONNECTION
  Serial.print("Connecting to ");
  Serial.println(ssid);

  // Connect to the WiFi
  WiFi.begin(ssid, wifi_password);

  // Wait until the connection has been confirmed before continuing
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Debugging - Output the IP Address of the ESP8266
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Connect to MQTT Broker
  // client.connect returns a boolean value to let us know if the connection was successful.
  // If the connection is failing, make sure you are using the correct MQTT Username and Password (Setup Earlier in the Instructable)
  Serial.print("MQTT connecting");
  if (client.connect(clientID, mqtt_username, mqtt_password)) {
    Serial.println("Connected to MQTT Broker!");
    if (client.publish(mqtt_topic, "Transmission started!")) {
      Serial.println("Transmission started");
    }
  }
  else {
    Serial.println("Connection to MQTT Broker failed...");
  }
  scanDevices();

  // Read the WHO_AM_I register, this is a good test of communication
  byte c = myTopIMU.readByte(0x68/*MPU9250_ADDRESS*/, WHO_AM_I_MPU9250);
  byte d = myBottomIMU.readByte(0x69/*MPU9250_ADDRESS*/, WHO_AM_I_MPU9250);
  Serial.print("MPU9250:top "); Serial.print("I AM "); Serial.print(c, HEX);
  Serial.print(" I should be "); Serial.println(0x73, HEX);
  Serial.print("MPU9250:down "); Serial.print("I AM "); Serial.print(d, HEX);
  Serial.print(" I should be "); Serial.println(0x73, HEX);

  if (c == 0x73 || d == 0x73) // WHO_AM_I should always be 0x73
  {
    Serial.println("atleast one MPU9250 is online...");

    // Start by performing self test and reporting values
    myTopIMU.MPU9250SelfTest(myTopIMU.SelfTest);
    Serial.print("x-axis self test: acceleration trim within : ");
    Serial.print(myTopIMU.SelfTest[0], 1); Serial.println("% of factory value");
    Serial.print("y-axis self test: acceleration trim within : ");
    Serial.print(myTopIMU.SelfTest[1], 1); Serial.println("% of factory value");
    Serial.print("z-axis self test: acceleration trim within : ");
    Serial.print(myTopIMU.SelfTest[2], 1); Serial.println("% of factory value");
    Serial.print("x-axis self test: gyration trim within : ");
    Serial.print(myTopIMU.SelfTest[3], 1); Serial.println("% of factory value");
    Serial.print("y-axis self test: gyration trim within : ");
    Serial.print(myTopIMU.SelfTest[4], 1); Serial.println("% of factory value");
    Serial.print("z-axis self test: gyration trim within : ");
    Serial.print(myTopIMU.SelfTest[5], 1); Serial.println("% of factory value");

    // Calibrate gyro and accelerometers, load biases in bias registers
    myTopIMU.calibrateMPU9250(myTopIMU.gyroBias, myTopIMU.accelBias);

    myTopIMU.initMPU9250();
    // Initialize device for active mode read of acclerometer, gyroscope, and
    // temperature
    Serial.println("MPU9250 initialized for active data mode....");

    // Read the WHO_AM_I register of the magnetometer, this is a good test of
    // communication
    byte d = myTopIMU.readByte(AK8963_ADDRESS, WHO_AM_I_AK8963);
    Serial.print("AK8963 "); Serial.print("I AM "); Serial.print(d, HEX);
    Serial.print(" I should be "); Serial.println(0x48, HEX);

    // Get magnetometer calibration from AK8963 ROM
    myTopIMU.initAK8963(myTopIMU.magCalibration);
    // Initialize device for active mode read of magnetometer
    Serial.println("AK8963 initialized for active data mode....");
    if (SerialDebug)
    {
      //  Serial.println("Calibration values: ");
      Serial.print("X-Axis sensitivity adjustment value ");
      Serial.println(myTopIMU.magCalibration[0], 2);
      Serial.print("Y-Axis sensitivity adjustment value ");
      Serial.println(myTopIMU.magCalibration[1], 2);
      Serial.print("Z-Axis sensitivity adjustment value ");
      Serial.println(myTopIMU.magCalibration[2], 2);
    }

  } // if (c == 0x73)
  else
  {
    Serial.print("Could not connect to MPU9250:top 0x");
    Serial.println(c, HEX);
    Serial.print("Could not connect to MPU9250:down 0x");
    Serial.println(d, HEX);
    setup() ; // Loop forever if communication doesn't happen
  }
}

void loop()
{

  // If intPin goes high, all data registers have new data
  // On interrupt, check if data ready interrupt
  if (myTopIMU.readByte(0x68/*MPU9250_ADDRESS*/, INT_STATUS) & 0x01)
  {
    myTopIMU.readAccelData(myTopIMU.accelCount);  // Read the x/y/z adc values
    myTopIMU.getAres();

    // Now we'll calculate the accleration value into actual g's
    // This depends on scale being set
    myTopIMU.ax = (float)myTopIMU.accelCount[0] * myTopIMU.aRes; // - accelBias[0];
    myTopIMU.ay = (float)myTopIMU.accelCount[1] * myTopIMU.aRes; // - accelBias[1];
    myTopIMU.az = (float)myTopIMU.accelCount[2] * myTopIMU.aRes; // - accelBias[2];

    myTopIMU.readGyroData(myTopIMU.gyroCount);  // Read the x/y/z adc values
    myTopIMU.getGres();

    // Calculate the gyro value into actual degrees per second
    // This depends on scale being set
    myTopIMU.gx = (float)myTopIMU.gyroCount[0] * myTopIMU.gRes;
    myTopIMU.gy = (float)myTopIMU.gyroCount[1] * myTopIMU.gRes;
    myTopIMU.gz = (float)myTopIMU.gyroCount[2] * myTopIMU.gRes;

    myTopIMU.readMagData(myTopIMU.magCount);  // Read the x/y/z adc values
    myTopIMU.getMres();
    // User environmental x-axis correction in milliGauss, should be
    // automatically calculated
    myTopIMU.magbias[0] = +470.;
    // User environmental x-axis correction in milliGauss TODO axis??
    myTopIMU.magbias[1] = +120.;
    // User environmental x-axis correction in milliGauss
    myTopIMU.magbias[2] = +125.;

    // Calculate the magnetometer values in milliGauss
    // Include factory calibration per data sheet and user environmental
    // corrections
    // Get actual magnetometer value, this depends on scale being set
    myTopIMU.mx = (float)myTopIMU.magCount[0] * myTopIMU.mRes * myTopIMU.magCalibration[0] -
                  myTopIMU.magbias[0];
    myTopIMU.my = (float)myTopIMU.magCount[1] * myTopIMU.mRes * myTopIMU.magCalibration[1] -
                  myTopIMU.magbias[1];
    myTopIMU.mz = (float)myTopIMU.magCount[2] * myTopIMU.mRes * myTopIMU.magCalibration[2] -
                  myTopIMU.magbias[2];
  } // if (readByte(MPU9250_ADDRESS, INT_STATUS) & 0x01)

  // Must be called before updating quaternions!
  myTopIMU.updateTime();

  // Sensors x (y)-axis of the accelerometer is aligned with the y (x)-axis of
  // the magnetometer; the magnetometer z-axis (+ down) is opposite to z-axis
  // (+ up) of accelerometer and gyro! We have to make some allowance for this
  // orientationmismatch in feeding the output to the quaternion filter. For the
  // MPU-9250, we have chosen a magnetic rotation that keeps the sensor forward
  // along the x-axis just like in the LSM9DS0 sensor. This rotation can be
  // modified to allow any convenient orientation convention. This is ok by
  // aircraft orientation standards! Pass gyro rate as rad/s
  //  MadgwickQuaternionUpdate(ax, ay, az, gx*PI/180.0f, gy*PI/180.0f, gz*PI/180.0f,  my,  mx, mz);
  MahonyQuaternionUpdate(myTopIMU.ax, myTopIMU.ay, myTopIMU.az, myTopIMU.gx * DEG_TO_RAD,
                         myTopIMU.gy * DEG_TO_RAD, myTopIMU.gz * DEG_TO_RAD, myTopIMU.my,
                         myTopIMU.mx, myTopIMU.mz, myTopIMU.deltat);

  if (!AHRS)
  {
    myTopIMU.delt_t = millis() - myTopIMU.count;
    if (myTopIMU.delt_t > 500)
    {
      if (SerialDebug)
      {
        //client.publish(mqtt_topic, "Transmission started!")
        // Print acceleration values in milligs!
        char x_value[10];
        char y_value[10];
        char z_value[10];
        dtostrf(1000 * myTopIMU.ax, 4, 3, x_value);
        client.publish(mqtt_topic, "X-acceleration: "); client.publish(mqtt_topic, x_value);
        //client.publish(mqtt_topic, " mg ");
        dtostrf(1000 * myTopIMU.ay, 4, 3, y_value);
        client.publish(mqtt_topic, "Y-acceleration: "); client.publish(mqtt_topic, y_value);
        //client.publish(mqtt_topic, " mg ");
        dtostrf(1000 * myTopIMU.az, 4, 3, z_value);
        client.publish(mqtt_topic, "Z-acceleration: "); client.publish(mqtt_topic, z_value);
        //client.publish(mqtt_topic, " mg ");

        Serial.print("X-acceleration: "); Serial.print(1000 * myTopIMU.ax);
        Serial.print(" mg ");
        Serial.print("Y-acceleration: "); Serial.print(1000 * myTopIMU.ay);
        Serial.print(" mg ");
        Serial.print("Z-acceleration: "); Serial.print(1000 * myTopIMU.az);
        Serial.println(" mg ");

        // Print gyro values in degree/sec
        dtostrf(1000 * myTopIMU.gx, 4, 3, x_value);
        client.publish(mqtt_topic, "X-gyro rate:: "); client.publish(mqtt_topic, x_value);
        //client.publish(mqtt_topic, " degrees/sec ");
        dtostrf(1000 * myTopIMU.gy, 4, 3, y_value);
        client.publish(mqtt_topic, "Y-gyro rate:: "); client.publish(mqtt_topic, y_value);
        //client.publish(mqtt_topic, " degrees/sec ");
        dtostrf(1000 * myTopIMU.gz, 4, 3, z_value);
        client.publish(mqtt_topic, "Z-gyro rate:: "); client.publish(mqtt_topic, z_value);
        //client.publish(mqtt_topic, " degrees/sec ");

        Serial.print("X-gyro rate: "); Serial.print(myTopIMU.gx, 3);
        Serial.print(" degrees/sec ");
        Serial.print("Y-gyro rate: "); Serial.print(myTopIMU.gy, 3);
        Serial.print(" degrees/sec ");
        Serial.print("Z-gyro rate: "); Serial.print(myTopIMU.gz, 3);
        Serial.println(" degrees/sec");

        // Print mag values in degree/sec
        Serial.print("X-mag field: "); Serial.print(myTopIMU.mx);
        Serial.print(" mG ");
        Serial.print("Y-mag field: "); Serial.print(myTopIMU.my);
        Serial.print(" mG ");
        Serial.print("Z-mag field: "); Serial.print(myTopIMU.mz);
        Serial.println(" mG");

        myTopIMU.tempCount = myTopIMU.readTempData();  // Read the adc values
        // Temperature in degrees Centigrade
        myTopIMU.temperature = ((float) myTopIMU.tempCount) / 333.87 + 21.0;
        dtostrf(myTopIMU.temperature, 4, 3, x_value);
        // Print temperature in degrees Centigrade
        client.publish(mqtt_topic, "Temperature is "); client.publish(mqtt_topic, x_value);
        Serial.print("Temperature is ");  Serial.print(myTopIMU.temperature, 1);
        Serial.println(" degrees C");
      }

      myTopIMU.count = millis();
    } // if (myTopIMU.delt_t > 500)
  } // if (!AHRS)
  else
  {
    // Serial print and/or display at 0.5 s rate independent of data rates
    myTopIMU.delt_t = millis() - myTopIMU.count;

    // update LCD once per half-second independent of read rate
    if (myTopIMU.delt_t > 500)
    {
      if (SerialDebug)
      {
        Serial.print("ax = "); Serial.print((int)1000 * myTopIMU.ax);
        Serial.print(" ay = "); Serial.print((int)1000 * myTopIMU.ay);
        Serial.print(" az = "); Serial.print((int)1000 * myTopIMU.az);
        Serial.println(" mg");

        Serial.print("gx = "); Serial.print( myTopIMU.gx, 2);
        Serial.print(" gy = "); Serial.print( myTopIMU.gy, 2);
        Serial.print(" gz = "); Serial.print( myTopIMU.gz, 2);
        Serial.println(" deg/s");

        Serial.print("mx = "); Serial.print( (int)myTopIMU.mx );
        Serial.print(" my = "); Serial.print( (int)myTopIMU.my );
        Serial.print(" mz = "); Serial.print( (int)myTopIMU.mz );
        Serial.println(" mG");

        Serial.print("q0 = "); Serial.print(*getQ());
        Serial.print(" qx = "); Serial.print(*(getQ() + 1));
        Serial.print(" qy = "); Serial.print(*(getQ() + 2));
        Serial.print(" qz = "); Serial.println(*(getQ() + 3));
      }

      // Define output variables from updated quaternion---these are Tait-Bryan
      // angles, commonly used in aircraft orientation. In this coordinate system,
      // the positive z-axis is down toward Earth. Yaw is the angle between Sensor
      // x-axis and Earth magnetic North (or true North if corrected for local
      // declination, looking down on the sensor positive yaw is counterclockwise.
      // Pitch is angle between sensor x-axis and Earth ground plane, toward the
      // Earth is positive, up toward the sky is negative. Roll is angle between
      // sensor y-axis and Earth ground plane, y-axis up is positive roll. These
      // arise from the definition of the homogeneous rotation matrix constructed
      // from quaternions. Tait-Bryan angles as well as Euler angles are
      // non-commutative; that is, the get the correct orientation the rotations
      // must be applied in the correct order which for this configuration is yaw,
      // pitch, and then roll.
      // For more see
      // http://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
      // which has additional links.
      myTopIMU.yaw   = atan2(2.0f * (*(getQ() + 1) * *(getQ() + 2) + *getQ() *
                                     *(getQ() + 3)), *getQ() * *getQ() + * (getQ() + 1) * *(getQ() + 1)
                             - * (getQ() + 2) * *(getQ() + 2) - * (getQ() + 3) * *(getQ() + 3));
      myTopIMU.pitch = -asin(2.0f * (*(getQ() + 1) * *(getQ() + 3) - *getQ() *
                                     *(getQ() + 2)));
      myTopIMU.roll  = atan2(2.0f * (*getQ() * *(getQ() + 1) + * (getQ() + 2) *
                                     *(getQ() + 3)), *getQ() * *getQ() - * (getQ() + 1) * *(getQ() + 1)
                             - * (getQ() + 2) * *(getQ() + 2) + * (getQ() + 3) * *(getQ() + 3));
      myTopIMU.pitch *= RAD_TO_DEG;
      myTopIMU.yaw   *= RAD_TO_DEG;
      // Declination of SparkFun Electronics (40°05'26.6"N 105°11'05.9"W) is
      //   8° 30' E  ± 0° 21' (or 8.5°) on 2016-07-19
      // - http://www.ngdc.noaa.gov/geomag-web/#declination
      myTopIMU.yaw   -= 8.5;
      myTopIMU.roll  *= RAD_TO_DEG;

      if (SerialDebug)
      {
        Serial.print("Yaw, Pitch, Roll: ");
        Serial.print(myTopIMU.yaw, 2);
        Serial.print(", ");
        Serial.print(myTopIMU.pitch, 2);
        Serial.print(", ");
        Serial.println(myTopIMU.roll, 2);

        Serial.print("rate = ");
        Serial.print((float)myTopIMU.sumCount / myTopIMU.sum, 2);
        Serial.println(" Hz");
      }

      myTopIMU.count = millis();
      myTopIMU.sumCount = 0;
      myTopIMU.sum = 0;
    } // if (myTopIMU.delt_t > 500)
  } // if (AHRS)
  delay(500);
}
