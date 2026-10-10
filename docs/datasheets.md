# Reference documents

Datasheets and references for every part on the boards in this repo.
Generated from [`datasheets.json`](datasheets.json) by
[`tools/fetch_datasheets.py`](../tools/fetch_datasheets.py). **Don't edit by hand.**

PDFs are downloaded locally into `datasheets/` (git-ignored: vendor documents are
not redistributed in this public repo). Run `python tools/fetch_datasheets.py` to
get them. "Local" shows whether the last run saved a copy.

## espressif

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| ESP32-P4 | [ESP32-P4 datasheet](https://documentation.espressif.com/esp32-p4_datasheet_en.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| ESP32-P4 | [ESP32-P4 Technical Reference Manual](https://documentation.espressif.com/esp32-p4_technical_reference_manual_en.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| ESP32-P4 | [ESP32-P4 hardware design guidelines](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32p4/esp-hardware-design-guidelines-en-master-esp32p4.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| ESP32-C5 | [ESP32-C5 datasheet](https://documentation.espressif.com/esp32-c5_datasheet_en.pdf) | ADSB_Test | yes (2026-10-10) |
| ESP32-C5 | [ESP32-C5 Technical Reference Manual](https://documentation.espressif.com/esp32-c5_technical_reference_manual_en.pdf) | ADSB_Test | yes (2026-10-10) |
| ESP32-C5 | [ESP32-C5 hardware design guidelines](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32c5/esp-hardware-design-guidelines-en-master-esp32c5.pdf) | ADSB_Test | yes (2026-10-10) |
| ESP32-C5-WROOM-1-N16R8 | [ESP32-C5-WROOM-1 / WROOM-1U datasheet](https://documentation.espressif.com/esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf) | ADSB_Test | yes (2026-10-10) |
| ESP32-C6 | [ESP32-C6 datasheet](https://documentation.espressif.com/esp32-c6_datasheet_en.pdf) | Waveshare 7B | yes (2026-10-10) |
| ESP32-C6-MINI-1 | [ESP32-C6-MINI-1 / MINI-1U datasheet](https://documentation.espressif.com/esp32-c6-mini-1_mini-1u_datasheet_en.pdf) | Waveshare 7B | yes (2026-10-10) |
| ESP-IDF | [ESP-IDF programming guide (ESP32-P4)](https://docs.espressif.com/projects/esp-idf/en/latest/esp32p4/) | Waveshare 7B, ADSB_Test | link only |
| esp_hosted | [ESP-Hosted-MCU (Wi-Fi co-processor) repository and docs](https://github.com/espressif/esp-hosted-mcu) | Waveshare 7B, ADSB_Test | link only |

## waveshare

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| ESP32-P4-WIFI6-Touch-LCD-7B | [Waveshare schematic](https://files.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-7B/ESP32-P4-WIFI6-Touch-LCD-7B.pdf) | Waveshare 7B | yes (2026-10-10) |
| ESP32-P4-WIFI6-Touch-LCD-7B | [Waveshare dimension drawing + STEP (ZIP)](https://files.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-7B/ESP32-P4-WIFI6-Touch-LCD-7B-3D.zip) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| ESP32-P4-WIFI6-Touch-LCD-7B | [Waveshare product docs](https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B) | Waveshare 7B | link only |
| ESP32-P4-WIFI6-Touch-LCD-7B | [Waveshare example code](https://github.com/waveshareteam/ESP32-P4-WIFI6-Touch-LCD-7B) | Waveshare 7B | link only |

## display

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| EK79007AD | [EK79007AD LCD driver IC (Espressif mirror)](https://dl.espressif.com/dl/schematics/display_driver_chip_EK79007AD_datasheet.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| GT911 | [GT911 capacitive touch controller](https://www.crystalfontz.com/controllers/GOODIX/GT911/464/) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| AP3012KTR-E1 | [AP3012 boost (panel AVDD)](https://www.diodes.com/assets/Datasheets/AP3012.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| AP3032KTR-G1 | [AP3032 LED backlight boost](https://www.diodes.com/assets/Datasheets/AP3032.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| BAT54S-7-F | [BAT54S Schottky (VGH/VGL charge pumps)](https://www.diodes.com/assets/Datasheets/ds11005.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |

## power

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| RT9193-18 / -33 | [RT9193 300 mA LDO (product page; no direct PDF link)](https://www.richtek.com/Products/Linear%20Regulators/Single%20Output%20Linear%20Regulator/RT9193?sc_lang=en) | Waveshare 7B, ADSB_Test | link only |
| MP1658GTF-Z | [MP1658 3 A buck (product page; MPS has no public PDF link)](https://www.monolithicpower.com/en/mp1658.html) | Waveshare 7B | link only |
| MP1605GTF-Z | [MP1605 2 A buck (product page)](https://www.monolithicpower.com/en/mp1605.html) | Waveshare 7B, ADSB_Test | link only |
| AO3401A | [AO3401A P-MOSFET (SD power, VBUS OR)](https://www.aosmd.com/res/datasheets/AO3401A.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| ETA6098 | [ETA6098 1S Li-ion charger](https://www.lcsc.com/search?q=ETA6098) | Waveshare 7B | link only |
| STUSB4500 | [STUSB4500 USB-PD sink controller](https://www.st.com/resource/en/datasheet/stusb4500.pdf) | ADSB_Test | no: site blocks scripts, save by hand |
| BQ25792 | [BQ25792 charger: TI product/datasheet pages return 404 (2026-10-10), see BQ25798](https://ti.com/document-viewer/lit/html/slusdg1) | ADSB_Test | link only |
| BQ25798 | [BQ25798 1-4S buck-boost charger with MPPT (proposed replacement for BQ25792)](https://www.ti.com/lit/ds/symlink/bq25798.pdf) | ADSB_Test | yes (2026-10-10) |
| PAC1954 | [PAC195x power monitor (Microchip product page; site blocks scripts)](https://www.microchip.com/en-us/product/PAC1954) | ADSB_Test | link only (open in a browser) |
| TPS62933 | [TPS62933 3 A buck (3V3)](https://www.ti.com/lit/ds/symlink/tps62933.pdf) | ADSB_Test | yes (2026-10-10) |
| TPS25200 | [TPS25200 eFuse (USB-A VBUS)](https://www.ti.com/lit/ds/symlink/tps25200.pdf) | ADSB_Test | yes (2026-10-10) |
| AP2112K-3.3 | [AP2112 600 mA LDO (ADSBee carrier)](https://www.diodes.com/assets/Datasheets/AP2112.pdf) | ADSB_Test | yes (2026-10-10) |

## memory

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| GD25Q256EYIGR | [GD25Q256E 32 MB QSPI flash](https://www.gigadevice.com/product/flash/spi-nor-flash/gd25q256e) | Waveshare 7B, ADSB_Test | link only |

## interface

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| IP101GRI | [IP101G family datasheet IP101G-DS-R01 (unofficial distributor mirror; IC Plus has no public link)](https://dfsimg2.hqewimg.com/group1/M00/1E/7E/wKhk72GgdAWACBnTACa6J2TDLkI754.pdf) | ADSB_Test | yes (2026-10-10) |
| USB2514B | [USB2514B 4-port USB 2.0 hub (Microchip product page; site blocks scripts)](https://www.microchip.com/en-us/product/USB2514B) | ADSB_Test | link only (open in a browser) |
| FT2232H | [FT2232H dual USB-UART (FTDI product page; site blocks scripts)](https://ftdichip.com/products/ft2232hq/) | ADSB_Test | link only (open in a browser) |
| CP2102N | [CP2102N USB-UART](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf) | ADSB_Test | no: site blocks scripts, save by hand |
| CH343P | [CH343 USB-UART (reference board)](https://www.wch-ic.com/products/CH343.html) | Waveshare 7B | link only |
| RP2040 | [RP2040 datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf) | ADSB_Test | yes (2026-10-10) |
| RP2040 | [Hardware design with RP2040](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf) | ADSB_Test | yes (2026-10-10) |

## logic

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| TCA6408A | [TCA6408A I2C GPIO expander](https://www.ti.com/lit/ds/symlink/tca6408a.pdf) | ADSB_Test | yes (2026-10-10) |
| 74LVC1G157 (Nexperia) | [2:1 mux (m1421 UART RX); TI has no SN74LVC1G157](https://assets.nexperia.com/documents/data-sheet/74LVC1G157.pdf) | ADSB_Test | yes (2026-10-10) |
| SN74LVC1G32 | [OR gate (m1421 SYNC)](https://www.ti.com/lit/ds/symlink/sn74lvc1g32.pdf) | ADSB_Test | yes (2026-10-10) |
| SN74LVC1G07 | [Open-drain buffer (resets)](https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf) | ADSB_Test | yes (2026-10-10) |
| SN74LVC1G125 | [3-state buffer (Dev isolation)](https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf) | ADSB_Test | yes (2026-10-10) |
| SN74LVC2T45 | [Dual level translator (Dev isolation)](https://www.ti.com/lit/ds/symlink/sn74lvc2t45.pdf) | ADSB_Test | yes (2026-10-10) |

## rf

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| MAX-M10S | [u-blox MAX-M10S GNSS](https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf) | ADSB_Test | yes (2026-10-10) |
| MAX-M10S | [u-blox MAX-M10S integration manual](https://content.u-blox.com/sites/default/files/MAX-M10S_IntegrationManual_UBX-20053088.pdf) | ADSB_Test | yes (2026-10-10) |
| SCN-2-11+ | [Mini-Circuits SCN-2-11+ power splitter/combiner](https://www.minicircuits.com/pdfs/SCN-2-11+.pdf) | ADSB_Test | yes (2026-10-10) |
| ESD7351 | [ESD7351 RF ESD diode](https://www.onsemi.com/download/data-sheet/pdf/esd7351-d.pdf) | ADSB_Test | yes (2026-10-10) |

## adsbee

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| ADSBee m1421 | [ADSBee m1421 datasheet (pinout, AT commands)](https://github.com/PantsForBirds/adsbee/raw/main/word/exports/datasheet_adsbee_m1421.pdf) | ADSB_Test | yes (2026-10-10) |
| ADSBee 1421 Dev Kit | [ADSBee 1421 Developer Kit datasheet](https://github.com/PantsForBirds/adsbee/raw/main/word/exports/datasheet_adsbee_1421_devkit.pdf) | ADSB_Test | yes (2026-10-10) |
| ADSBee 1421 carrier | [ADSBee 1421 carrier KiCad reference design (ZIP, ~300 MB)](https://pantsforbirds.com/wp-content/uploads/2026/06/adsbee_1421-A.zip) | ADSB_Test | link only |
| ADSBee m1421 | [m1421 module docs (pinout, SYNC, bootloader)](https://github.com/PantsForBirds/adsbee/blob/main/docs/adsbee-1421/m1421.md) | ADSB_Test | link only |
| ADSBee m1421 | [m1421 firmware README (SYNC backdoor, UART flashing)](https://github.com/PantsForBirds/adsbee/blob/main/firmware/adsbee_1421/README.md) | ADSB_Test | link only |
| ADSBee m1421 | [PantsForBirds KiCad libraries (MIT)](https://github.com/PantsForBirds/kicad-libs) | ADSB_Test | link only |
| CC1314R10 | [TI CC1314R10 (inside the m1421)](https://www.ti.com/lit/ds/symlink/cc1314r10.pdf) | ADSB_Test | yes (2026-10-10) |
| CC1314R10 | [CC13x4/CC26x4 TRM SWCU194 (ROM serial bootloader)](https://www.ti.com/lit/ug/swcu194/swcu194.pdf) | ADSB_Test | yes (2026-10-10) |
| LR2021 | [Semtech LR2021 (inside the m1421)](https://www.semtech.com/products/wireless-rf/lora-plus/lr2021) | ADSB_Test | link only |

## reference-only

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| ES8311 | [ES8311 audio codec (reference only)](http://www.everest-semi.com/pdf/ES8311%20PB.pdf) | Waveshare 7B | link only |
| ES7210 | [ES7210 4-ch ADC (reference only)](http://www.everest-semi.com/pdf/ES7210%20PB.pdf) | Waveshare 7B | link only |
| TJA1051 | [TJA1051 CAN transceiver (reference only)](https://www.nxp.com/docs/en/data-sheet/TJA1051.pdf) | Waveshare 7B | yes (2026-10-10) |

## tools

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| LA5016 | [Kingst LA5016 logic analyser (product page; header pin-out in architecture.md)](http://www.qdkingst.com/en/products) | ADSB_Test | link only |
