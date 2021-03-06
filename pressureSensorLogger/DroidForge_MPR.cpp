/*!
 * 
 * Modified by DroidForge for use with different variant of pressure sensor
 *  By: JP Thomas
 *      05/16/2020
 *      
 * Original File Header:
 * @file Adafruit_MPRLS.cpp
 *
 * @mainpage Adafruit MPRLS Pressure sensor
 *
 * @section intro_sec Introduction
 *
 * Designed specifically to work with the MPRLS sensor from Adafruit
 * ----> https://www.adafruit.com/products/3965
 *
 * These sensors use I2C to communicate, 2 pins (SCL+SDA) are required
 * to interface with the breakout.
 *
 * Adafruit invests time and resources providing this open source code,
 * please support Adafruit and open-source hardware by purchasing
 * products from Adafruit!
 *
 * @section dependencies Dependencies
 *
 *
 * @section author Author
 *
 * Written by Limor Fried/Ladyada for Adafruit Industries.
 *
 * @section license License
 *
 * MIT license, all text here must be included in any redistribution.
 *
 */

#if (ARDUINO >= 100)
#include "Arduino.h"
#else
#include "WProgram.h"
#endif
#include "Wire.h"

#include "DroidForge_MPR.h"

#define DEBUG false

/**************************************************************************/
/*!
    @brief constructor initializes default configuration value
    @param reset_pin Optional hardware reset pin, default set to -1 to skip
    @param EOC_pin Optional End-of-Convert indication pin, default set to -1 to
   skip
    @param PSI_min The minimum PSI measurement range of the sensor, default 0
    @param PSI_max The maximum PSI measurement range of the sensor, default 25
*/
/**************************************************************************/
Adafruit_MPRLS::Adafruit_MPRLS(int8_t reset_pin, int8_t EOC_pin,
                               uint8_t PSI_min, uint8_t PSI_max, enum mprTransFunc mprTFunc) {

  _reset = reset_pin;
  _eoc = EOC_pin;
  _PSI_min = PSI_min;
  _PSI_max = PSI_max;
  _mprTFunc = mprTFunc;
}

/**************************************************************************/
/*!
    @brief  setup and initialize communication with the hardware
    @param i2c_addr The I2C address for the sensor (default is 0x18)
    @param twoWire Optional pointer to the desired TwoWire I2C object. Defaults
   to &Wire
    @returns True on success, False if sensor not found
*/
/**************************************************************************/
boolean Adafruit_MPRLS::begin(uint8_t i2c_addr, TwoWire *twoWire) {
  _i2c_addr = i2c_addr;
  _i2c = twoWire;
  offsetError = 0;

  _i2c->begin();

  if (_reset != -1) {
    pinMode(_reset, OUTPUT);
    digitalWrite(_reset, HIGH);
    digitalWrite(_reset, LOW);
    delay(10);
    digitalWrite(_reset, HIGH);
  }
  if (_eoc != -1) {
    pinMode(_eoc, INPUT);
  }

  delay(10); // startup timing

  // Serial.print("Status: ");
  uint8_t stat = readStatus();
  // Serial.println(stat);
  return !(stat & 0b10011110);
}

/**************************************************************************/
/*!
    @brief Read and calculate the pressure
    @returns The measured pressure, in hPa on success, NAN on failure
*/
/**************************************************************************/
float Adafruit_MPRLS::readPressure(enum outputUnits outUnits) {
  int32_t raw_psi = readData();
  if (raw_psi == 0xFFFFFFFF) {
    return NAN;
  }


  float psi;
  // All is good, calculate the PSI and convert to hPA
  switch (_mprTFunc){
    case TRANSFER_FUNCTION_A: //10% to 90% of 2^24 counts
      psi = (raw_psi - A_COUNT_MIN - offsetError) * (_PSI_max - _PSI_min);
      psi /= (float)(A_COUNT_MAX - A_COUNT_MIN);
      psi += _PSI_min;
      break;
    case TRANSFER_FUNCTION_B: //2.5% to 22.5% of 2^24 counts
      psi = (raw_psi - B_COUNT_MIN - offsetError) * (_PSI_max - _PSI_min);
      psi /= (float)(B_COUNT_MAX - B_COUNT_MIN);
      psi += _PSI_min;
      break;
    case TRANSFER_FUNCTION_C: //20% to 80% of 2^24 counts
      psi = (raw_psi - C_COUNT_MIN - offsetError) * (_PSI_max - _PSI_min);
      psi /= (float)(C_COUNT_MAX - C_COUNT_MIN);
      psi += _PSI_min;
      break;
  }

  switch (outUnits){
    case PSI:
      return psi;
      break;
    case HPA:
      return psi * 6894.7572932;
      break;
    case BAR:
      return psi * 0.068947572932;
      break;
    case MBAR:
      return psi * 68.947572932;
      break;
    case KPA:
      return psi * 6.8947572932;
      break;
    case CMH2O:
      return psi * 70.3069578296;
      break;
    case INH2O:
      return psi * 27.6799048425;
      break;
    case MMHG:
      return psi * 51.71492;
      break;
  }
  return psi;
}

/**************************************************************************/
/*!
    @brief Zero the pressure
    @param dataPeriod the data sampling period in milliseconds (number of milliseconds between reads)
    @returns None

    Note: dataPeriod was required as the sensor zero error is dependant on the data rate. Thus the 
    values used to calculate the zero point must be sampled at the same rate as the user application
*/
/**************************************************************************/
void Adafruit_MPRLS::autoZero(uint32_t dataPeriod){
  if(DEBUG)Serial.println("Zeroing the device using period: " + String(dataPeriod));
  uint32_t start_time = millis();
  int32_t raw_psi = readData();
  if(DEBUG)Serial.println(raw_psi);
  if (raw_psi == 0xFFFFFFFF) {
    return;
  }
  raw_psi = 0;
  for(int i = 0; i<NUM_AUTO_ZERO_SAMPLES; i++){
    while((millis()-start_time)<dataPeriod){
      //wait for the next sample to match the data sampling rate
    }
    start_time = millis();
    if(DEBUG)Serial.println("start_time: "+String(start_time));
    int32_t tempP = readData();
    if(DEBUG)Serial.print(tempP);
    if(DEBUG)Serial.print("\t\t");
    if(i>=NUM_AUTO_ZERO_SAMPLES_IGNORE){
      raw_psi += tempP;
    }
    if(DEBUG)Serial.println(raw_psi);
  }
  raw_psi /= NUM_AUTO_ZERO_SAMPLES-NUM_AUTO_ZERO_SAMPLES_IGNORE;
  if(DEBUG)Serial.print("Final: ");
  if(DEBUG)Serial.println(raw_psi);
  
  switch (_mprTFunc){
    case TRANSFER_FUNCTION_A: //10% to 90% of 2^24 counts
        offsetError = raw_psi - A_COUNT_MIN;
      break;
    case TRANSFER_FUNCTION_B: //2.5% to 22.5% of 2^24 counts
        offsetError = raw_psi - B_COUNT_MIN;
      break;
    case TRANSFER_FUNCTION_C: //20% to 80% of 2^24 counts
        offsetError = raw_psi - C_COUNT_MIN;
      break;
  }
  delay(dataPeriod);
}

/**************************************************************************/
/*!
    @brief Read 24 bits of measurement data from the device
    @returns -1 on failure (check status) or 24 bits of raw ADC reading
*/
/**************************************************************************/
uint32_t Adafruit_MPRLS::readData(void) {
  _i2c->beginTransmission(_i2c_addr);
  _i2c->write(0xAA); // command to read pressure
  _i2c->write((byte)0x0);
  _i2c->write((byte)0x0);
  _i2c->endTransmission();

  // Use the gpio to tell end of conversion
  if (_eoc != -1) {
    while (!digitalRead(_eoc)) {
      delay(1);
    }
  } else {
    // check the status byte
    uint8_t stat;
    while ((stat = readStatus()) & MPRLS_STATUS_BUSY) {
      // Serial.print("Status: "); Serial.println(stat, HEX);
      delay(1);
    }
  }
  _i2c->requestFrom(_i2c_addr, (uint8_t)4);

  uint8_t status = _i2c->read();
  if (status & MPRLS_STATUS_MATHSAT) {
    return 0xFFFFFFFF;
  }
  if (status & MPRLS_STATUS_FAILED) {
    return 0xFFFFFFFF;
  }

  uint32_t ret;
  ret = _i2c->read();
  ret <<= 8;
  ret |= _i2c->read();
  ret <<= 8;
  ret |= _i2c->read();

  return ret;
}

/**************************************************************************/
/*!
    @brief Read just the status byte, see datasheet for bit definitions
    @returns 8 bits of status data
*/
/**************************************************************************/
uint8_t Adafruit_MPRLS::readStatus(void) {
  _i2c->requestFrom(_i2c_addr, (uint8_t)1);

  return _i2c->read();
}
