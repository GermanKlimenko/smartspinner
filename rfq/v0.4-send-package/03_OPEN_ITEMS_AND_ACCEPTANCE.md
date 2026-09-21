# Open items and acceptance criteria

## Known open items

- Main PCB DRC currently reports 68 unconnected items.
- Tip PCB DRC currently reports 4 unconnected items.
- Exact manufacturer land patterns and pin-1 orientation require verification.
- TPS61023 boost, MCP73831 charging and local decoupling networks require final datasheet review.
- Raytac MDBT50Q-1MV2 antenna keep-out must be checked on every copper layer and against the enclosure.
- Silkscreen and cosmetic DRC warnings require review.
- BOM sourcing identifiers and acceptable alternates require supplier confirmation.

## Engineering acceptance before fabrication

- Editable KiCad project returned to the customer.
- Zero copper errors and zero unconnected items in DRC for both board types.
- ERC completed with every waiver documented.
- Exact footprints checked against selected MPN datasheets.
- Final four-layer stack-up and impedance assumptions documented.
- Antenna keep-out and RF placement reviewed.
- Power-path, charging, boost, switching and decoupling networks reviewed.
- Final Gerber, drill, IPC-356 or equivalent netlist, BOM, CPL and assembly drawings generated from the approved sources.
- Supplier DFM report completed and all findings resolved or accepted in writing.

## First-article acceptance

- Only one complete electronic set is assembled initially.
- Visual inspection and AOI completed.
- No short circuit on battery, 3.3 V or 5 V rails.
- Charging and protected battery operation verified with a laboratory supply before connecting a LiPo cell.
- MCU programming and BLE advertisement verified.
- Hall and IMU communication verified.
- All eight LED data streams verified at limited brightness.
- Current consumption and thermal behavior recorded.
- Mechanical fit and static balance checked before powered rotation.

No remaining units may be assembled until the customer approves first-article results.

