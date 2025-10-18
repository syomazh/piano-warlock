// Arduino streaming receiver for "E,<note>,<duration>\n" commands
// Non-blocking scheduling supports overlapping notes.

const unsigned long SERIAL_TIMEOUT_MS = 100; // not used but nice to know

// Map MIDI notes to Arduino pins. Update arrays to match wiring.
const int NOTE_COUNT = 12;
const int noteValues[NOTE_COUNT] = {60,61,62,63,64,65,66,67,68,69,70,71};
const int notePins[NOTE_COUNT]   = {2,3,4,5,6,7,8,9,10,11,12,13};

int findPinForNote(int note) {
  for (int i = 0; i < NOTE_COUNT; ++i) if (noteValues[i] == note) return notePins[i];
  return -1;
}

// active note slots
struct Active {
  bool inUse;
  int pin;
  unsigned long offAt; // millis time to turn off
};
const int MAX_ACTIVE = 32;
Active active[MAX_ACTIVE];

String inputBuf = "";

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NOTE_COUNT; ++i) {
    pinMode(notePins[i], OUTPUT);
    digitalWrite(notePins[i], LOW);
  }
  for (int i = 0; i < MAX_ACTIVE; ++i) {
    active[i].inUse = false;
  }
}

void loop() {
  // read incoming serial
  while (Serial.available()) {
    char c = (char)Serial.read();
    if (c == '\n') {
      processLine(inputBuf);
      inputBuf = "";
    } else if (c >= 32) {
      inputBuf += c;
      if (inputBuf.length() > 120) {
        // avoid runaway huge line
        inputBuf = "";
      }
    }
  }

  // Check active notes to turn off
  unsigned long now = millis();
  for (int i = 0; i < MAX_ACTIVE; ++i) {
    if (active[i].inUse && (long)(now - active[i].offAt) >= 0) {
      digitalWrite(active[i].pin, LOW);
      active[i].inUse = false;
    }
  }
}

void processLine(const String &line) {
  // Expect lines like: E,60,250
  if (line.length() == 0) return;
  if (line.charAt(0) != 'E') return;
  // crude parse
  int firstComma = line.indexOf(',');
  int secondComma = line.indexOf(',', firstComma+1);
  if (firstComma < 0 || secondComma < 0) return;
  String noteStr = line.substring(firstComma+1, secondComma);
  String durStr = line.substring(secondComma+1);
  int note = noteStr.toInt();
  unsigned long dur = (unsigned long)durStr.toInt();
  triggerNote(note, dur);
}

void triggerNote(int note, unsigned long dur_ms) {
  int pin = findPinForNote(note);
  if (pin < 0) return; // unmapped
  // find free active slot
  for (int i = 0; i < MAX_ACTIVE; ++i) {
    if (!active[i].inUse) {
      digitalWrite(pin, HIGH);
      active[i].inUse = true;
      active[i].pin = pin;
      active[i].offAt = millis() + dur_ms;
      return;
    }
  }
  // no free slot: ignore or replace oldest (we ignore for now)
}