# First article bring-up - Smart Spinner v0.4

1. Bare-board inspection: outline, 23.2 mm center hole, four M2 holes, impedance-independent continuity, no copper inside RF keep-out.
2. Populate power only. Feed VBAT from a current-limited bench supply at 3.7 V / 100 mA. Verify no short.
3. Verify +3V3 within 3.25-3.35 V; then verify boost soft-start and +5V_LED with LEDs disconnected.
4. Raise current limit in steps. Check switch node with oscilloscope and measure U3/L1/C bulk temperature after 10 minutes at 0.5 A and 1.0 A.
5. Populate/debug nRF module through SWD. Confirm BLE advertising and current below 10 mA with LEDs disabled.
6. Populate Hall and IMU. Log Hall period and IMU gyro while turning in a guarded low-speed fixture.
7. Populate one LED per chain, run RGB orientation test, then populate remaining top pixels.
8. Attach one tip board at a time. Run a walking-one pixel test and verify all four 20-pixel top chains and all four 12-pixel tip chains independently.
9. Enforce firmware brightness/current limit before battery operation. Full-white unrestricted frames are forbidden.
10. Install matched protected cells and mechanically retain them. Static-balance to less than 0.10 g equivalent at 45 mm.
11. Dynamic test behind a polycarbonate guard at 300, 600, 900 and 1200 RPM; stop on vibration, temperature rise, RF loss or frame slip.
12. Only after the first article passes may the remaining nine assemblies be released.
