#include "../firmware/spinner_bench/bench_core.h"
#include <cassert>
#include <cstdio>
#include <string>

bench::Command parse(std::string s) { return bench::parse(&s[0]); }
int main() {
  // Independent receiver model: each rising edge inserts SDI into OUT0;
  // previous OUT15 propagates to the next chip.
  for (int channel = 0; channel < 96; ++channel) {
    bench::Frame f; f.clear(); assert(f.channel(channel));
    bool rx[96] = {};
    for (int b = 0; b < 12; ++b) for (int bit = 7; bit >= 0; --bit) {
      for (int c = 95; c > 0; --c) rx[c] = rx[c - 1];
      rx[0] = (f.wireByte(b) >> bit) & 1;
    }
    for (int c = 0; c < 96; ++c) assert(rx[c] == (c == channel));
  }
  for (int p = 0; p < 32; ++p) for (int mask = 0; mask < 8; ++mask) {
    bench::Frame f; f.clear(); assert(f.pixel(p, mask));
    for (int c = 0; c < 96; ++c)
      assert(bool(f.word[c / 16] & (1U << (c % 16))) ==
             (c / 3 == p && bool(mask & (1U << (c % 3)))));
  }
  bench::Frame f; f.clear(); assert(!f.channel(96)); assert(!f.pixel(32, 1));
  assert(!f.pixel(0, 8));
  for (auto s : {"OFF", "HELP", "WALK", "CH 0", "CH 95", "PIX 31 7", "ALL 7",
                 "PULSE 95 20", "PULSE 0 500", "SPEED 125000", "SPEED 4000000"})
    assert(parse(s).op != bench::INVALID);
  for (auto s : {" ", "ON", "CH -1", "CH 96", "CH 0 junk", "PIX 32 7", "PIX 0 8",
                 "PIX 0", "PULSE 0 19", "PULSE 0 501", "ALL 8", "ALL 7 1",
                 "SPEED 8000000", "SPEED 99999999999999", "OFF junk", "CH 1x"})
    assert(parse(s).op == bench::INVALID);
  puts("PASS: 96 independent shift-chain cases; 256 RGB masks; bounds and parser cases");
}
