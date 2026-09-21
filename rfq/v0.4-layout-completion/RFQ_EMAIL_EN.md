Subject: PCB layout completion + turnkey PCBA RFQ - SmartSpinner v0.4, 10 sets

Hello [COMPANY] Engineering Team,

My name is German Klimenko. I am developing SmartSpinner, a 100 mm four-arm persistence-of-vision display with Bluetooth connectivity.

I would like a quotation for two stages:

1. engineering completion of the supplied KiCad design, including schematic/detail review, closing all open DRC connections, exact-footprint verification, power-stage completion, RF keep-out review and DFM;
2. manufacture and turnkey assembly of 10 complete electronic sets after I approve the updated design.

Each set contains one four-arm main PCB with 80 top RGB pixels and four vertical tip PCBs with 12 RGB pixels each. The design uses eight independent LED data streams, an nRF52840 BLE module, BMI270 IMU, Hall index sensor, protected 1S LiPo input, 3.3 V logic and a switched 5 V LED rail.

The v0.4 package includes KiCad PCB sources, review Gerbers/drill, BOM, CPL, electrical architecture, fabrication drawing, power budget, DRC reports and a first-article test procedure. The current Gerbers are **not approved for fabrication**: the included release-status file records open central/interface connections that your layout engineer must close before DFM sign-off.

Project references:

- Website: https://germanklimenko.github.io/smartspinner/
- Repository: https://github.com/GermanKlimenko/smartspinner
- Electronics package: https://germanklimenko.github.io/smartspinner/project-files/SmartSpinner_v0_4_electronics_ERC.zip
- Mechanical package: https://germanklimenko.github.io/smartspinner/project-files/ticker_spinner_v0_3_complete_package.zip

Please quote separately:

- engineering/layout completion and number of included revision rounds;
- PCB fabrication for 10 main boards and 40 tip boards;
- components and alternates;
- SMT assembly, stencil/tooling and AOI;
- one first article plus the remaining production quantity;
- optional nRF52 programming and functional testing;
- shipping to Moscow, Russia, with no LiPo batteries included.

Please also confirm whether your engineers will return the updated editable KiCad project and a zero-error DRC report before fabrication.

Best regards,
German Klimenko
SmartSpinner project
https://germanklimenko.github.io/smartspinner/
