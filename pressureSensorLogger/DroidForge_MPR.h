/*!
 * 
 * Modified by DroidForge for use with different variant of pressure sensor
 *  By: JP Thomas
 *      05/16/2020
 *      
 * Original file header:
 * @file Adafruit_MPRLS.h
 *
 * Designed specifically to work with the MPRLS sensors from Adafruit
 * ----> https://www.adafruit.com/products/3965
 *
 * These sensors use I2C to communicate, 2 pins (SCL+SDA) are required
 * to interface with the breakout.
 *
 * Adafruit invests time and resources providing this open source code,
 * please support Adafruit and open-source hardware by purchasing
 * products from Adafruit!
 *
 * Written by Limor Fried/Ladyada for Adafruit Industries.
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

#define MPRLS_DEFAULT_ADDR (0x18)   ///< Most common I2C address
#define MPRLS_STATUS_POWERED (0x40) ///< Status SPI powered bit
#define MPRLS_STATUS_BUSY (0x20)    ///< Status busy bit
#define MPRLS_STATUS_FAILED (0x04)  ///< Status bit for integrity fail
#define MPRLS_STATUS_MATHSAT (0x01) ///< Status bit for math saturation

enum mprTransFunc{
  TRANSFER_FUNCTION_A, //10% to 90% of 2^24 counts
  TRANSFER_FUNCTION_B, //2.5% to 22.5% of 2^24 counts
  TRANSFER_FUNCTION_C  //20% to 80% of 2^24 counts
};

#define A_COUNT_MIN 0x19999A
#define A_COUNT_MAX 0xE66666
#define B_COUNT_MIN 0x066666
#define B_COUNT_MAX 0x39999A
#define C_COUNT_MIN 0x333333
#define C_COUNT_MAX 0xCCCCCD

#define NUM_AUTO_ZERO_SAMPLES 1

enum outputUnits{
  PSI,
  HPA,
  KPA,
  MBAR,
  BAR,
  CMH2O,
  INH2O,
  MMHG,
  NUM_UNITS
};


/**************************************************************************/
/*!
    @brief  Class that stores state and functions for interacting with MPRLS
   sensor IC
*/
/**************************************************************************/
class Adafruit_MPRLS {
public:
  Adafruit_MPRLS(int8_t reset_pin = -1, int8_t EOC_pin = -1,
                 uint8_t PSI_min = 0, uint8_t PSI_max = 25, enum mprTransFunc mprTFunc = TRANSFER_FUNCTION_A);

  boolean begin(uint8_t i2c_addr = MPRLS_DEFAULT_ADDR,
                TwoWire *twoWire = &Wire);

  uint8_t readStatus(void);
  float readPressure(enum outputUnits outUnits = HPA);
  void autoZero(void);

private:
  uint32_t readData(void);
  int32_t offsetError;

  uint8_t _i2c_addr;
  int8_t _reset, _eoc;
  uint8_t _PSI_min, _PSI_max;
  enum mprTransFunc _mprTFunc;

  TwoWire *_i2c;
};
