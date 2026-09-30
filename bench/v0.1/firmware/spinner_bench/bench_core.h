#pragma once
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

namespace bench {
constexpr uint8_t PIXELS = 32, CHANNELS = 96, DRIVERS = 6;
struct Frame {
  uint16_t word[DRIVERS];
  void clear() { memset(word, 0, sizeof(word)); }
  bool channel(uint16_t c) {
    if (c >= CHANNELS) return false;
    word[c / 16] |= uint16_t(1U) << (c % 16);
    return true;
  }
  bool pixel(uint16_t p, uint16_t mask) {
    if (p >= PIXELS || mask > 7) return false;
    for (uint8_t color = 0; color < 3; ++color)
      if (mask & (1U << color)) channel(3 * p + color);
    return true;
  }
  // First byte is U6[15:8]; last byte is U1[7:0].
  uint8_t wireByte(uint8_t n) const {
    uint16_t w = word[DRIVERS - 1 - n / 2];
    return n % 2 ? uint8_t(w) : uint8_t(w >> 8);
  }
};
enum Op { INVALID, OFF, HELP, CH, PIX, ALL, WALK, PULSE, SPEED };
struct Command { Op op; uint32_t a, b; };
inline bool number(const char *s, uint32_t &v) {
  if (!s || !*s) return false;
  v = 0;
  for (; *s; ++s) {
    if (*s < '0' || *s > '9' || v > 1000000UL) return false;
    v = v * 10 + uint8_t(*s - '0');
  }
  return true;
}
// Modifies the caller's line buffer. No heap allocation.
inline Command parse(char *line) {
  Command c = {INVALID, 0, 0};
  char *t[4] = {nullptr, nullptr, nullptr, nullptr};
  uint8_t n = 0;
  for (char *p = strtok(line, " \t"); p; p = strtok(nullptr, " \t")) {
    if (n == 4) return c;
    t[n++] = p;
  }
  if (!n) return c;
  if (n == 1) {
    if (!strcmp(t[0], "OFF")) c.op = OFF;
    if (!strcmp(t[0], "HELP")) c.op = HELP;
    if (!strcmp(t[0], "WALK")) c.op = WALK;
    return c;
  }
  if (!number(t[1], c.a)) return c;
  if (n == 2) {
    if (!strcmp(t[0], "CH") && c.a < CHANNELS) c.op = CH;
    if (!strcmp(t[0], "ALL") && c.a <= 7) c.op = ALL;
    if (!strcmp(t[0], "SPEED") && (c.a == 125000 || c.a == 250000 ||
        c.a == 500000 || c.a == 1000000 || c.a == 2000000 || c.a == 4000000))
      c.op = SPEED;
    return c;
  }
  if (n != 3 || !number(t[2], c.b)) return c;
  if (!strcmp(t[0], "PIX") && c.a < PIXELS && c.b <= 7) c.op = PIX;
  if (!strcmp(t[0], "PULSE") && c.a < CHANNELS && c.b >= 20 && c.b <= 500)
    c.op = PULSE;
  return c;
}
}
