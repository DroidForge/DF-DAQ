#include <Adafruit_NeoPixel.h>
#include <Wire.h>
#include "Maxtec_ADS1015.h"

#define LED_Data0 12
#define N_LEDS 16

#define mEnable 5
#define mA0 6
#define mA1 7
#define mA2 8

#define Status 13

//#define EEprom0 11
#define LED_Data0 12
//#define EEprom1 13
#define LED_Data1 14

Maxtec_ADS1115 AD1(0x48);

uint8_t power = 15;

int MUX[] = {0,0,0};

int16_t Trash;
int16_t AD1Out[32];

int16_t Calibration = 1;
int16_t Calibration1[] = {12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12};

String Out1 = "";

char Delim = ',';
long pMillis = 0;
long TimePassed = 0;
unsigned long cMillis = 0;
long SampleTime = 0;
boolean toggle = true; //LED Runtime

String inString = "";
boolean takeReading = false;
boolean updateNeoPix = true;
unsigned long SampleDelay = 1000;

Adafruit_NeoPixel strip = Adafruit_NeoPixel(N_LEDS, LED_Data0, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel strip2 = Adafruit_NeoPixel(N_LEDS, LED_Data1, NEO_GRB + NEO_KHZ800);

void setup() {
  strip.begin();
  strip2.begin();  
  pinMode(mEnable, OUTPUT);   //MUX Enable Line
  pinMode(mA0, OUTPUT);       //MUX A0 Select Line
  pinMode(mA1, OUTPUT);       //MUX A1 Select Line
  pinMode(mA2, OUTPUT);       //MUX A2 Select Line
  pinMode(Status, OUTPUT);    //Status LED
  
  digitalWrite(mEnable, LOW); //Disable the MUXs
  Serial.begin(250000);       //Start the Serial

  //Start the A to D
  AD1.begin();

  //Load default settings to the A to D
  AD1.setMode(MODE_SINGLE);
  AD1.setDs(DS_860SPS);

  for(int i = 0; i < 3; i++){ //Give time for the serial to Boot up
    digitalWrite(Status, HIGH);
    delay(25);
    digitalWrite(Status, LOW);
    delay(25);
    digitalWrite(Status, HIGH);
    delay(25);
    digitalWrite(Status, LOW);
    delay(25);
    digitalWrite(Status, HIGH);
    delay(25);
    digitalWrite(Status, LOW);
    delay(875);
  }

  //Boot up with the MUXs at Position [0][0][0]
  digitalWrite(mA0, LOW);
  digitalWrite(mA1, LOW);
  digitalWrite(mA2, LOW);     

  digitalWrite(Status, HIGH); //Turn the Status Light ON
}
 
void loop() {
  while(Serial.available() > 0){
    digitalWrite(Status, LOW);    //Turn the Status Light OFF
    char inChar = Serial.read();  //Read the Incomming String one Byte at a Time
    inString += (char)inChar;     //Append the Incomming Byte to a String

    if(inChar == '\n'){       //EOL Character, Stop Reading
      if(inString[0] == 'S'){ //Stream/Start Command
        digitalWrite(Status, LOW);    //Turn the Status Light OFF
        digitalWrite(mEnable, HIGH);  //Turn on the MUXs
        delayMicroseconds(5);         //Let the MUXs turn on
        Trash = AD1.readADC_SingleEnded(0);  //Throw away the first A to D reading 
        takeReading = true;           //Start Taking Readings
       }
      else if(inString[0] == 'V'){ //Version Command
        digitalWrite(Status, HIGH);     //Turn the Status Light ON
        Serial.println("SN0002 - 0.2"); //Send the current Firmware Code
       }
      else if(inString[0] == 'P'){ //Stop Command
        digitalWrite(Status, HIGH); //Turn the Status Light ON
        digitalWrite(mEnable, LOW); //Disable the MUXs
        takeReading = false;        //Stop Taking Readings
       }
      else if(inString[0] == 'R'){ //Rate Command
        SampleDelay = (inString[1] << 24) + (inString[2] << 16) + (inString[3] << 8) + (inString[4]);
        Serial.println(SampleDelay);
        for(int i = 0; i < 5; i++){ //Signal the Rate was changed
          digitalWrite(Status, HIGH); //Turn the Status Light ON
          delay(25);
          digitalWrite(Status, LOW); //Turn the Status Light OFF
          delay(25);
        }
        digitalWrite(Status, HIGH);//Turn the Status Light ON
      }
      else{ //Unknown Command, Blink Rapidly 3 Times
        digitalWrite(Status, LOW);
        delay(200);
        digitalWrite(Status, HIGH);
        delay(200);
        digitalWrite(Status, LOW);
        delay(200);
        digitalWrite(Status, HIGH);
        delay(200);
        digitalWrite(Status, LOW);
        delay(200);
        digitalWrite(Status, HIGH);
      }
      inString = "";  //Reset Incomming String
      break;
    }
  }

  if(takeReading){
    cMillis = millis(); //Get current millis time
    if((cMillis - SampleTime) > 500){ //Status Blink
      SampleTime = cMillis;
      digitalWrite(Status, toggle);
      toggle = !toggle;
      for(int j = 0; j < 32; j++){
        if(AD1Out[j] > 640)
          SetGreen(j, power);
        else if(AD1Out[j] < -640)
          SetRed(j, power);
        else 
          SetBlue(j, power);
      }
    } 
    if((cMillis - pMillis) > SampleDelay){ //Limit the loop time to match the rate
      pMillis = cMillis; //Reset the timing clock
      for(int i = 0; i<32; i++){ //Loop through Board 1 and Board 2 (32 Channels)
  
        //Binary count through all 8 MUX configurations 
        MUX[0] = bitRead(i,0);//[x][-][-]
        MUX[1] = bitRead(i,1);//[-][x][-]
        MUX[2] = bitRead(i,2);//[-][-][x]
    
        ToggleMux(MUX[0], MUX[1], MUX[2]); //Switch the MUX to the next channel
        delayMicroseconds(5); //Allow time for the MUX to switch
  
        //Read Board 1 and Board 2
        if(i < 8){ //Board 1, Channel 1 - 8
          AD1Out[i] = AD1.readADC_SingleEnded(0) + (Calibration1[i] * Calibration); //Read the ADC and include Calibration Offset
        }
        else if (i < 16){ //Board 1, Channel 9 - 16
          AD1Out[i] = AD1.readADC_SingleEnded(1) + (Calibration1[i] * Calibration); //Read the ADC and include Calibration Offset
        }
        else if (i < 24){ //Board 2, Channel 1 - 8
          AD1Out[i] = AD1.readADC_SingleEnded(2) + (Calibration1[i] * Calibration); //Read the ADC and include Calibration Offset

        }
        else if (i < 32){ //Board 2, Channel 9 - 16
          AD1Out[i] = AD1.readADC_SingleEnded(3) + (Calibration1[i] * Calibration); //Read the ADC and include Calibration Offset
        }
      }
      Out1 = ""; //Start with blank Outupt string
      for(int j = 0; j < 32; j++){ //Loop through the collected data in AD1Out and AD2Out
        if(j == 31) //Last Character
          Out1 = Out1 + String(AD1Out[j]); //Build Output String
        else 
          Out1 = Out1 + String(AD1Out[j]) + Delim; //Build Output String
        }
      Serial.println(Out1); //Send out the collected data via serial
    }
  }
  else{ //Idle Loop and Update LEDS at 5 Samp/Sec
    digitalWrite(mEnable, HIGH);  //Turn on the MUXs
    cMillis = millis(); //Get current millis time
    if((cMillis - pMillis) > 200){ //Limit the loop time to match the rate
      pMillis = cMillis; //Reset the timing clock
      for(int i = 0; i<32; i++){ //Loop through Board 1 and Board 2 (32 Channels)
  
        //Binary count through all 8 MUX configurations 
        MUX[0] = bitRead(i,0);//[x][-][-]
        MUX[1] = bitRead(i,1);//[-][x][-]
        MUX[2] = bitRead(i,2);//[-][-][x]
    
        ToggleMux(MUX[0], MUX[1], MUX[2]); //Switch the MUX to the next channel
        delayMicroseconds(5); //Allow time for the MUX to switch
  
        //Read Board 1 and Board 2
        if(i < 8){ //Board 1, Channel 1 - 8
          AD1Out[i] = AD1.readADC_SingleEnded(0) + (Calibration1[i] * Calibration); //Read the ADC and include Calibration Offset
        }
        else if (i < 16){ //Board 1, Channel 9 - 16
          AD1Out[i] = AD1.readADC_SingleEnded(1) + (Calibration1[i] * Calibration); //Read the ADC and include Calibration Offset
        }
        else if (i < 24){ //Board 2, Channel 1 - 8
          AD1Out[i] = AD1.readADC_SingleEnded(2) + (Calibration1[i] * Calibration); //Read the ADC and include Calibration Offset

        }
        else if (i < 32){ //Board 2, Channel 9 - 16
          AD1Out[i] = AD1.readADC_SingleEnded(3) + (Calibration1[i] * Calibration); //Read the ADC and include Calibration Offset
        }
      }
      for(int j = 0; j < 32; j++){
        if(AD1Out[j] > 640)
          SetGreen(j, power);
        else if(AD1Out[j] < -640)
          SetRed(j, power);
        else 
          SetBlue(j, power);
      }
    }
  }
}

//Takes in 3 (0/1) Ints and sets the MUX A0:2 Lines to match
static void ToggleMux(int b0, int b1, int b2){
  if(b0 == 1)
    digitalWrite(mA0, HIGH);
  else
    digitalWrite(mA0, LOW);

  if(b1 == 1)
    digitalWrite(mA1, HIGH);
  else
    digitalWrite(mA1, LOW);

  if(b2 == 1)
    digitalWrite(mA2, HIGH);
  else
    digitalWrite(mA2, LOW);    
}
static void ClearLEDs(){
  for(int i = 0; i<N_LEDS; i++){
    strip.setPixelColor(i, strip.Color(0,0,0));
    strip.show();
  }
}
static void SetBlue(int pixel, int power){
  int Bpower = power * 1.5;
  if(pixel < 16){
    strip.setPixelColor(pixel, strip.Color(0, 0, Bpower));
    strip.show();
  }
  else{
    strip2.setPixelColor(pixel-16, strip2.Color(0, 0, Bpower));
    strip2.show();
  }
}
static void SetGreen(int pixel, int power){
  if(pixel < 16){
    strip.setPixelColor(pixel, strip.Color(0, power, 0));
    strip.show();
  }
  else{
    strip2.setPixelColor(pixel-16, strip2.Color(0, power, 0));
    strip2.show();
  }
}
static void SetRed(int pixel, int power){
  if(pixel < 16){
    strip.setPixelColor(pixel, strip.Color(power, 0, 0));
    strip.show();
  }
  else{
    strip2.setPixelColor(pixel-16, strip2.Color(power, 0, 0));
    strip2.show();
  }
}
