/* SmartSpinner B0.1 - STATIONARY ONLY; UNO R3 / ATmega328P 16 MHz.
 * SM16306SJ x6, 32 common-anode RGB, R_EXT = 3.74 kohm.
 * No motor, battery, BLE, automatic brightness, or production POV firmware.
 * S1 physical OFF is mandatory. Timeout is NOT a hardware safety system.
 */
#include <SPI.h>
#include "bench_core.h"
#if !defined(__AVR_ATmega328P__) || F_CPU != 16000000UL
#error "This firmware requires the 5 V, 16 MHz UNO R3 ATmega328P"
#endif

const uint8_t LE = 10, OE = 9, MARK = 8;
bench::Frame frame;
uint32_t spiHz = 125000, started = 0, lifetime = 0, lastStep = 0, lastPulse = 0;
bench::Op mode = bench::OFF;
uint8_t walkChannel = 0;
uint16_t pulseWidth = 50;
char input[64];
uint8_t used = 0;
bool discardLine = false;

void blank() { digitalWrite(OE, HIGH); digitalWrite(MARK, LOW); }
void sendFrame() {
  blank();
  digitalWrite(LE, LOW);
  SPI.beginTransaction(SPISettings(spiHz, MSBFIRST, SPI_MODE0));
  for (uint8_t n = 0; n < 12; ++n) SPI.transfer(frame.wireByte(n));
  SPI.endTransaction();
  digitalWrite(LE, HIGH);
  delayMicroseconds(2);
  digitalWrite(LE, LOW);
}
void stopOutputs() {
  blank(); mode = bench::OFF; frame.clear(); sendFrame();
}
void showStatic() { digitalWrite(OE, LOW); }
void help() {
  Serial.println(F("B0.1 STATIONARY ONLY; S1 OFF before wiring/power changes."));
  Serial.println(F("OFF | HELP | CH 0..95 | PIX 0..31 0..7 | ALL 0..7"));
  Serial.println(F("WALK | PULSE channel width_us(20..500)"));
  Serial.println(F("SPEED 125000|250000|500000|1000000|2000000|4000000"));
  Serial.println(F("Mask: R=1 G=2 B=4 W=7. CH/PIX/PULSE: 5s; ALL: 0.5s."));
}
void execute(char *line) {
  stopOutputs();
  bench::Command c = bench::parse(line);
  switch (c.op) {
    case bench::INVALID: Serial.println(F("ERR; outputs OFF")); return;
    case bench::HELP: help(); return;
    case bench::OFF: Serial.println(F("OFF")); return;
    case bench::SPEED:
      spiHz = c.a; Serial.print(F("SPI Hz=")); Serial.println(spiHz); return;
    case bench::CH: frame.channel(c.a); lifetime = 5000; break;
    case bench::PIX: frame.pixel(c.a, c.b); lifetime = 5000; break;
    case bench::ALL:
      for (uint8_t p = 0; p < bench::PIXELS; ++p) frame.pixel(p, c.a);
      lifetime = 500; break;
    case bench::WALK:
      walkChannel = 0; frame.channel(0); lifetime = 20000; lastStep = millis(); break;
    case bench::PULSE:
      frame.channel(c.a); pulseWidth = c.b; lifetime = 5000; break;
    default: return;
  }
  sendFrame();
  started = millis(); lastPulse = micros(); mode = c.op;
  if (mode != bench::PULSE) showStatic();
  Serial.println(F("RUN; S1 must be RUN to enable light"));
}
void setup() {
  // Set output latch BEFORE switching the pin to output.
  digitalWrite(OE, HIGH); pinMode(OE, OUTPUT);
  digitalWrite(MARK, LOW); pinMode(MARK, OUTPUT);
  digitalWrite(LE, LOW); pinMode(LE, OUTPUT); // SS output keeps AVR SPI master
  SPI.begin(); stopOutputs(); Serial.begin(115200); help();
}
void loop() {
  // Bound serial work so a continuously sending host cannot starve the timeout.
  for (uint8_t n = 0; n < 16 && Serial.available(); ++n) {
    char ch = Serial.read();
    if (ch == '\r') continue;
    if (ch == '\n') {
      if (!discardLine && used) { input[used] = 0; execute(input); }
      used = 0; discardLine = false;
    } else if (!discardLine) {
      if (used < sizeof(input) - 1) input[used++] = ch;
      else { discardLine = true; used = 0; stopOutputs(); }
    }
  }
  if (mode == bench::OFF) return;
  uint32_t now = millis();
  if (uint32_t(now - started) >= lifetime) {
    stopOutputs(); Serial.println(F("TIMEOUT; OFF")); return;
  }
  if (mode == bench::WALK && uint32_t(now - lastStep) >= 150) {
    lastStep = now;
    if (++walkChannel >= bench::CHANNELS) { stopOutputs(); return; }
    frame.clear(); frame.channel(walkChannel); sendFrame(); showStatic();
  }
  if (mode == bench::PULSE && uint32_t(micros() - lastPulse) >= 2000) {
    lastPulse = micros();
    // Marker goes HIGH in the same port write that makes OE LOW.
    // Measured pulse duration includes a small code overhead; verify on scope.
    noInterrupts();
    PORTB = (PORTB & ~_BV(PB1)) | _BV(PB0);
    delayMicroseconds(pulseWidth);
    PORTB = (PORTB | _BV(PB1)) & ~_BV(PB0);
    interrupts();
  }
}
