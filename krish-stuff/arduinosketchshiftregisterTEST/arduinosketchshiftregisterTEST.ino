// 74HC595 LED control via Serial (works with PowerShell input)

const int dataPin  = 11;  // SER (DS)
const int latchPin = 10;  // RCLK
const int clockPin = 13;  // SRCLK

void setup() {
  pinMode(dataPin, OUTPUT);
  pinMode(latchPin, OUTPUT);
  pinMode(clockPin, OUTPUT);
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    char input = Serial.read();

    if (input >= '1' && input <= '8') {
      int ledNum = input - '1';      // convert '1'..'8' → 0..7
      byte ledState = 1 << ledNum;

      digitalWrite(latchPin, LOW);
      shiftOut(dataPin, clockPin, MSBFIRST, ledState);
      digitalWrite(latchPin, HIGH);

      Serial.print("LED ");
      Serial.print(ledNum + 1);
      Serial.println(" is ON");
    }
    else if (input == '0') {
      digitalWrite(latchPin, LOW);
      shiftOut(dataPin, clockPin, MSBFIRST, 0);
      digitalWrite(latchPin, HIGH);
      Serial.println("All LEDs OFF");
    }
  }
}