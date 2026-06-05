// include the Servo library
#include <Servo.h>

Servo Servo1, Servo2;  // create a servo object

#define LASER_PIN 11

void setup() {
  Servo1.attach(9);   // attaches the servo on pin 10 to the servo object
  Servo2.attach(10);
  Serial.begin(9600);  // open a serial connection to your computer

  pinMode(LASER_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LASER_PIN, LOW);
}

void Blink(int n) {
  for(int i = 0; i < n; i++) { 
    digitalWrite(LED_BUILTIN, HIGH);  // turn the LED on (HIGH is the voltage level)
    delay(1000);                      // wait for a second
    digitalWrite(LED_BUILTIN, LOW);   // turn the LED off by making the voltage LOW
    delay(1000);                
  }
}

byte data[2];
byte numbytes;

void loop() {

   if (Serial.available() >= 2) {  //если есть доступные данные
        // считываем байт
        numbytes  = Serial.readBytes(data, 2);
        
        switch(data[0]) {
          case 1:
            Servo1.write(70);
            break;
          case 2:
            Servo1.write(120);
            break;
          case 3:
            Servo1.write(90);
            break;
          case 4:
            digitalWrite(LASER_PIN, LOW);
            break;
          case 5:
            digitalWrite(LASER_PIN, HIGH);
            break;
        }
        switch(data[1]) {
          case 1:
            Servo2.write(70);
            break;
          case 2:
            Servo2.write(120);
            break;
          case 3:
            Servo2.write(90);
            break;  
        }
        delay(10);
   }
}