/*
 * pressure sensor logger
 * 
 * Written by DroidForge
 *  By: JP Thomas
 *      05/16/2020
 *      
 *
 */

#include "DroidForge_MPR.h"
//#include "DataPackage.h"

#define DEBUG false
#define RESPOND true
#define VERSION_NUMBER "0.0.1"
#define DEVICE_INFO "DF_pressureSensorLogger"
#define DEVICE_TYPE "MPRSS0001PG00001C"
#define DEVICE_SETUP "P-PSI-1-50-10"
#define HELP_STRING DEVICE_INFO " v" VERSION_NUMBER "\nCommand Interface:\n"\
                    "All commands are single characters. Line ending is ignored\n"\
                    "'s' -> run\n"\
                    "'p' -> stop\n"\
                    "'r' -> single read\n"\
                    "'h' or '?' -> this help page\n"\
                    "'i' -> DEVICE_INFO (" DEVICE_INFO ")\n"\
                    "'v' -> VERSION_NUMBER (" VERSION_NUMBER ")\n"\
                    "'t' -> DEVICE_TYPE (" DEVICE_TYPE ")\n"\
                    "'o' -> SAMPLE_PERIOD (units: milliseconds, valid values: 1-60000)\n"\
                    "'z' -> run auto zero function (zeros sensor to current pressure level)\n"\
                    "'u'[DATA] -> returns current UNITS when only 'u' is sent.\n\tSending [DATA] after 'u' changes units based on the following values:\n"\
                        "\t0: PSI\n"\
                        "\t1: HPA\n"\
                        "\t2: KPA\n"\
                        "\t3: MBAR\n"\
                        "\t4: BAR\n"\
                        "\t5: CMH2O\n"\
                        "\t6: INH2O\n"\
                        "\t7: MMHG\n"\
                        "\tEx: \"u4\" sets units to millibar\n"


// You dont *need* a reset and EOC pin for most uses, so we set to -1 and don't connect
#define RESET_PIN  -1  // set to any GPIO pin # to hard-reset on begin()
#define EOC_PIN    -1  // set to any GPIO pin to read end-of-conversion by pin
#define PSI_MIN 0
#define PSI_MAX 1
Adafruit_MPRLS mpr = Adafruit_MPRLS(RESET_PIN, EOC_PIN, PSI_MIN, PSI_MAX, TRANSFER_FUNCTION_C);

#define DEFAULT_SAMPLE_PERIOD 500

bool running = false;
unsigned long start_time;
enum outputUnits currentUnits = PSI;
String unitStrings[NUM_UNITS];
uint16_t sample_period = DEFAULT_SAMPLE_PERIOD;

void setup() {
  unitStrings[PSI] = "PSI";
  unitStrings[HPA] = "HPA";
  unitStrings[KPA] = "KPA";
  unitStrings[MBAR] = "MBAR";
  unitStrings[BAR] = "BAR";
  unitStrings[CMH2O] = "CMH2O";
  unitStrings[INH2O] = "INH2O";
  unitStrings[MMHG] = "MMHG";


  // put your setup code here, to run once:
  Serial.begin(115200);
  //while(!Serial);
  if(DEBUG) Serial.println("Starting Pressure Sensor");
  if(!mpr.begin()){
    if(DEBUG) Serial.println("Failed to communicate with pressure sensor!");
    while(1){
      delay(10);
    }
  }
  if(DEBUG) Serial.println("Found pressure sensor");

  mpr.autoZero();
  start_time = millis();
}

void loop() {
  if(millis()-start_time > sample_period){
    start_time = millis();
    if(running){
      // put your main code here, to run repeatedly:
      float pressure_psi = mpr.readPressure(currentUnits);
      if(DEBUG){
        Serial.println("Pressure: " + String(pressure_psi, 5));
      }else{
        Serial.print(pressure_psi, 4);
        Serial.print(",");
        Serial.println((char)13);
      }
    }
  }
  
  if(Serial.available()){
    char command;
    command = Serial.read();
    if(command == 's'){ //start data streaming
      running = true;
    }
    else if(command == 'p'){ //stop data streaming
      running = false;
    }
    else if(command == 'z'){
      mpr.autoZero();
    }
    else if(command == 'h' || command == '?'){
      running = false;
      Serial.println(HELP_STRING);
    }
    if(!running){ //these commands can only be run when the data streaming is stopped
      if(command == 'i'){
        Serial.println(DEVICE_INFO);
      }
      else if(command == 'x'){
        Serial.println(DEVICE_SETUP);
      }
      else if(command == 'v'){
        Serial.println(VERSION_NUMBER);
      }
      else if(command == 't'){
        Serial.println(DEVICE_TYPE);
      }
      else if(command == 'r'){
        float pressure_psi = mpr.readPressure(currentUnits);
        Serial.println(pressure_psi, 4);
      }
      else if(command == 'o'){
        if(Serial.available()>1){
          String command_data;
          while(Serial.available()>0){
            int inChar = Serial.read();
            if(isDigit(inChar)){
              command_data += (char)inChar;
            }
            if(inChar == '\n'){
              uint16_t command_int = command_data.toInt();
              if(command_int > 0 && command_int < 60000){
                sample_period = command_int;
              }
            }
          }
        }
        Serial.println(sample_period);
      }
      else if(command == 'u'){
        if(Serial.available()){
          char command_data = Serial.read()-'0';
          if(command_data >= 0 && command_data < NUM_UNITS){
            currentUnits = (enum outputUnits)command_data;
          }
        }
        Serial.println(unitStrings[currentUnits]);
      }
    }
  }
}
