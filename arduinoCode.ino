#include <Servo.h>
#include <AFMotor.h>

Servo steeringServo;
Servo crestServo;
AF_DCMotor rightMotor(1, MOTOR34_8KHZ);
AF_DCMotor leftMotor(2, MOTOR34_8KHZ);


int currentCrestPos = 0;
int crestDirection = 1;
unsigned long previousCrestMillis = 0;
int stepDelay = 15;

void setup() {
  Serial.begin(9600);
  steeringServo.attach(9);
  crestServo.attach(10);
  
  rightMotor.run(RELEASE);
  leftMotor.run(RELEASE);
  rightMotor.setSpeed(200);
  leftMotor.setSpeed(200);
  
  Serial.println("System Ready");
}

void loop() {
  // Handle serial input and control motors/steering
  if (Serial.available() > 0) {    
    String data = Serial.readStringUntil('\n');
    data.trim();
    
    int commaIndex = data.indexOf(',');
    if (commaIndex > 0 && data.length() > commaIndex+1) {
      String angleStr = data.substring(0, commaIndex);
      String cmdStr = data.substring(commaIndex + 1);
      
      if (angleStr.length() > 0 && cmdStr.length() > 0) {
        int angle = angleStr.toInt();
        int motorCommand = cmdStr.toInt();

        steeringServo.write(constrain(angle, 60, 110));

        uint8_t motorState = (motorCommand == 1) ? FORWARD : RELEASE;
        rightMotor.setSpeed(200);  // Refresh speed
        leftMotor.setSpeed(200);
        rightMotor.run(motorState);
        leftMotor.run(motorState);
        
        Serial.print("Steering: ");
        Serial.print(angle);
        Serial.print("° | Motors: ");
        Serial.println(motorState == FORWARD ? "RUNNING" : "STOPPED");
      }
    }
  }

  unsigned long currentMillis = millis();
  if (currentMillis - previousCrestMillis >= stepDelay) {
    previousCrestMillis = currentMillis;

    currentCrestPos += crestDirection;

    // Reverse direction at limits and clamp position
    if (currentCrestPos > 180) {
      currentCrestPos = 180;
      crestDirection = -1;
    } else if (currentCrestPos < 0) {
      currentCrestPos = 0;
      crestDirection = 1;
    }

    crestServo.write(currentCrestPos);
  }
}
