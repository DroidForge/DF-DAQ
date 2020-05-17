#include <Wire.h>
#include "Maxtec_ADS1015.h"

#define mEnable 5
#define mA0 6
#define mA1 7
#define mA2 8

#define Status 13

Maxtec_ADS1115 AD1(0x48);
Maxtec_ADS1115 AD2(0x49);

int MUX[] = {0,0,0};

int16_t Trash;
int16_t AD1Out[32];
int16_t AD2Out[32];

int16_t Calibration = 1;
int16_t Calibration1 = 0;
int16_t Calibration2 = 0;

String Out1 = "";
String Out2 = "";

char Delim = ',';
long pMillis = 0;
long TimePassed = 0;
unsigned long cMillis = 0;
long SampleTime = 0;
boolean toggle = true; //LED Runtime

String inString = "";
boolean takeReading = false;
unsigned long SampleDelay = 200;
 
void setup() {
  pinMode(mEnable, OUTPUT);   //MUX Enable Line
  pinMode(mA0, OUTPUT);       //MUX A0 Select Line
  pinMode(mA1, OUTPUT);       //MUX A1 Select Line
  pinMode(mA2, OUTPUT);       //MUX A2 Select Line
  pinMode(Status, OUTPUT);    //Status LED
  
  digitalWrite(mEnable, LOW); //Disable the MUXs
  Serial.begin(250000);       //Start the Serial

  //Start the A to D's 
  AD1.begin();
  AD2.begin();

  //Load default settings to the A to D's
  AD1.setMode(MODE_SINGLE);
  AD1.setDs(DS_860SPS);
  AD2.setMode(MODE_SINGLE);
  AD2.setDs(DS_860SPS);

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
        Trash = AD2.readADC_SingleEnded(0);  //There is a Read error after the A to D has been railed
        takeReading = true;           //Start Taking Readings
       }
      else if(inString[0] == 'V'){ //Version Command
        digitalWrite(Status, HIGH);     //Turn the Status Light ON
        Serial.println("SN0001 - 0.2"); //Send the current Firmware Code
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
    } 
    if((cMillis - pMillis) > SampleDelay){ //Limit the loop time to match the rate
      pMillis = cMillis; //Reset the timing clock
      digitalWrite(mEnable, HIGH);  //Enable the MUXs
      delayMicroseconds(5);         //Give the MUXs some time to turn on
      Trash = AD1.readADC_SingleEnded(0);  //Throw away the first A to D reading 
      Trash = AD2.readADC_SingleEnded(0);  //There is a Read error after the A to D has been railed
      for(int i = 0; i<32; i++){ //Loop through Board 1 and Board 2 (32 Channels)
  
        //Binary count through all 8 MUX configurations 
        MUX[0] = bitRead(i,0);//[x][-][-]
        MUX[1] = bitRead(i,1);//[-][x][-]
        MUX[2] = bitRead(i,2);//[-][-][x]
    
        ToggleMux(MUX[0], MUX[1], MUX[2]); //Switch the MUX to the next channel
        delayMicroseconds(5); //Allow time for the MUX to switch
  
        //Read Board 1 and Board 2
        if(i < 8){ //Board 1, Channel 1 - 8
          switch (i){
            case (0)://1
              Calibration1 = 217;
              Calibration2 = 225;
            break;
            case (1)://2
              Calibration1 = 215;
              Calibration2 = 223;
            break;
            case (2)://3
              Calibration1 = 216;
              Calibration2 = 223;
            break;
            case (3)://4
              Calibration1 = 215;
              Calibration2 = 222;
            break;
            case (4)://5
              Calibration1 = 219;
              Calibration2 = 227;
            break;
            case (5)://6
              Calibration1 = 205;
              Calibration2 = 213;
            break;
            case (6)://7
              Calibration1 = 216;
              Calibration2 = 218;
            break;
            case (7)://8
              Calibration1 = 213;
              Calibration2 = 215;
            break;
          }
          AD1Out[i] = AD1.readADC_SingleEnded(0) - (Calibration1 * Calibration); //Read the ADC and include Calibration Offset
          AD2Out[i] = AD2.readADC_SingleEnded(0) - (Calibration2 * Calibration); //Read the ADC and include Calibration Offset
        }
        else if (i < 16){ //Board 1, Channel 9 - 16
          switch (i){
            case (8)://9
              Calibration1 = 208;
              Calibration2 = 207;
            break;
            case (9)://10
              Calibration1 = 220;
              Calibration2 = 217;
            break;
            case (10)://11
              Calibration1 = 220;
              Calibration2 = 219;
            break;
            case (11)://12
              Calibration1 = 206;
              Calibration2 = 208;
            break;
            case (12)://13
              Calibration1 = 221;
              Calibration2 = 219;
            break;
            case (13)://14
              Calibration1 = 220;
              Calibration2 = 218;
            break;
            case (14)://15
              Calibration1 = 208;
              Calibration2 = 212;
            break;
            case (15)://16
              Calibration1 = 219;
              Calibration2 = 219;
            break;
          }
          AD1Out[i] = AD1.readADC_SingleEnded(1) - (Calibration1 * Calibration); //Read the ADC and include Calibration Offset
          AD2Out[i] = AD2.readADC_SingleEnded(1) - (Calibration2 * Calibration); //Read the ADC and include Calibration Offset
        }
        else if (i < 24){ //Board 2, Channel 1 - 8
          switch (i){
            case (16)://17
              Calibration1 = 214;
              Calibration2 = 222;
            break;
            case (17)://18
              Calibration1 = 213;
              Calibration2 = 220;
            break;
            case (18)://19
              Calibration1 = 214;
              Calibration2 = 222;
            break;
            case (19)://20
              Calibration1 = 213;
              Calibration2 = 220;
            break;
            case (20)://21
              Calibration1 = 215;
              Calibration2 = 223;
            break;
            case (21)://22
              Calibration1 = 202;
              Calibration2 = 209;
            break;
            case (22)://23
              Calibration1 = 209;
              Calibration2 = 216;
            break;
            case (23)://24
              Calibration1 = 206;
              Calibration2 = 213;
            break;
          }
          AD1Out[i] = AD1.readADC_SingleEnded(2) - (Calibration1 * Calibration); //Read the ADC and include Calibration Offset
          AD2Out[i] = AD2.readADC_SingleEnded(2) - (Calibration2 * Calibration); //Read the ADC and include Calibration Offset
        }
        else if (i < 32){ //Board 2, Channel 9 - 16
          switch (i){
            case (24)://25
              Calibration1 = 196;
              Calibration2 = 201;
            break;
            case (25)://26
              Calibration1 = 206;
              Calibration2 = 212;
            break;
            case (26)://27
              Calibration1 = 209;
              Calibration2 = 216;
            break;
            case (27)://28
              Calibration1 = 196;
              Calibration2 = 202;
            break;
            case (28)://29
              Calibration1 = 209;
              Calibration2 = 216;
            break;
            case (29)://30
              Calibration1 = 210;
              Calibration2 = 215;
            break;
            case (30)://315
              Calibration1 = 200;
              Calibration2 = 204;
            break;
            case (31)://32
              Calibration1 = 206;
              Calibration2 = 213;
            break;
          }          
          AD1Out[i] = AD1.readADC_SingleEnded(3) - (Calibration1 * Calibration); //Read the ADC and include Calibration Offset
          AD2Out[i] = AD2.readADC_SingleEnded(3) - (Calibration2 * Calibration); //Read the ADC and include Calibration Offset
        }
      }
      digitalWrite(mEnable, LOW); //Disable the MUXs
      Out1 = ""; //Start with blank Outupt string
      Out2 = ""; //Start with blank Outupt string
      for(int j = 0; j < 32; j++){ //Loop through the collected data in AD1Out and AD2Out
        Out1 = Out1 + String(AD1Out[j]) + Delim; //Build Output 
        if(j == 31) //Last Character
          Out2 = Out2 + String(AD2Out[j]); //Build Output String
        else 
          Out2 = Out2 + String(AD2Out[j]) + Delim; //Build Output String
        }
      Serial.println(Out1 + Out2); //Send out the collected data via serial
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
