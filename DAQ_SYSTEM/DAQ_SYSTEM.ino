String inString = "";

void setup() {
  // put your setup code here, to run once:
  Serial.begin(250000);
}

void loop() {
  // put your main code here, to run repeatedly:
  while(Serial.available() > 0){
    char inChar = Serial.read();  //Read the Incomming String one Byte at a Time
    inString += (char)inChar;     //Append the Incomming Byte to a String

    if(inChar == '\n'){   //EOL Character, Stop Reading
      if(inString[0] == 'V') Serial.println("SN0001 - 0.2");
      //else unknown string
    }
  }
}
