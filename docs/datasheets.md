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
| ESP32-C5-WROOM-1-N16R8 | [ESP32-C5-WROOM-1 / WROOM-1U datasheet](https://documentation.espressif.com/esp32-c5-wroom-1_wroom-1u_datasheet_en.pdf) | no longer used | yes (2026-10-10) |
| ESP32-C6 | [ESP32-C6 datasheet](https://documentation.espressif.com/esp32-c6_datasheet_en.pdf) | Waveshare 7B | yes (2026-10-10) |
| ESP32-C6-MINI-1 | [ESP32-C6-MINI-1 / MINI-1U datasheet](https://documentation.espressif.com/esp32-c6-mini-1_mini-1u_datasheet_en.pdf) | Waveshare 7B | yes (2026-10-10) |
| ESP-IDF | [ESP-IDF programming guide (ESP32-P4)](https://docs.espressif.com/projects/esp-idf/en/latest/esp32p4/) | Waveshare 7B, ADSB_Test | link only |
| esp_hosted | [ESP-Hosted-MCU (Wi-Fi co-processor) repository and docs](https://github.com/espressif/esp-hosted-mcu) | Waveshare 7B, ADSB_Test | link only |
| WT01P4C5-S1 | [Wireless-Tag WT01P4C5-S1 (ESP32-P4 + ESP32-C5 module) datasheet v1.3](https://img03.71360.com/w3/77q677/20260127/9a1f9a9cd53575eaf50a76b38847ef97.pdf?dl=1&dlf=WT01P4C5-S1_datasheet_V1.3.pdf) | ADSB_Test | yes (2026-10-12) |
| WT01P4C5-S1 | [Wireless-Tag WT01P4C5-S1 product page](http://en.wireless-tag.com/product-item-73.html) | ADSB_Test | link only |

## waveshare

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| ESP32-P4-WIFI6-Touch-LCD-7B | [Waveshare schematic](https://files.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-7B/ESP32-P4-WIFI6-Touch-LCD-7B.pdf) | Waveshare 7B | yes (2026-10-10) |
| ESP32-P4-WIFI6-Touch-LCD-7B | [Waveshare dimension drawing + STEP (ZIP)](https://files.waveshare.com/wiki/ESP32-P4-WIFI6-Touch-LCD-7B/ESP32-P4-WIFI6-Touch-LCD-7B-3D.zip) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| ESP32-P4-WIFI6-Touch-LCD-7B | [Waveshare product docs](https://docs.waveshare.com/ESP32-P4-WIFI6-Touch-LCD-7B) | Waveshare 7B | link only |
| ESP32-P4-WIFI6-Touch-LCD-7B | [Waveshare example code](https://github.com/waveshareteam/ESP32-P4-WIFI6-Touch-LCD-7B) | Waveshare 7B | link only |
| Waveshare ESP32-P4-Module | [Waveshare ESP32-P4-Module schematic (fallback to WT01P4C5-S1)](https://files.waveshare.com/wiki/ESP32-P4-Module/ESP32-P4-Module-datasheet.pdf) | ADSB_Test | yes (2026-10-12) |
| Waveshare ESP32-P4-Module | [Waveshare ESP32-P4-Module wiki (pinout, land pattern, STEP)](https://www.waveshare.com/wiki/ESP32-P4-Module) | ADSB_Test | link only |

## display

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| EK79007AD | [EK79007AD LCD driver IC (Espressif mirror)](https://dl.espressif.com/dl/schematics/display_driver_chip_EK79007AD_datasheet.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| GT911 | [GT911 capacitive touch controller](https://www.crystalfontz.com/controllers/GOODIX/GT911/464/) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| AP3012KTR-E1 | [AP3012 boost (panel AVDD)](https://www.diodes.com/assets/Datasheets/AP3012.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| AP3032KTR-G1 | [AP3032 LED backlight boost](https://www.diodes.com/assets/Datasheets/AP3032.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| BAT54S-7-F | [BAT54S Schottky (VGH/VGL charge pumps)](https://www.diodes.com/assets/Datasheets/ds11005.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| BZT52C7V5S / BZT52C18S | [Diodes BZT52C-S zener (VGL/VGH clamps)](https://www.diodes.com/part/view/BZT52C18S) | ADSB_Test | link only |
| 1N5819HW | [Diodes 1N5819HW 1 A Schottky, SOD-123 (panel boosts)](https://www.diodes.com/part/view/1N5819HW) | ADSB_Test | link only |

## power

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| RT9193-18 / -33 | [RT9193 300 mA LDO (product page; no direct PDF link)](https://www.richtek.com/Products/Linear%20Regulators/Single%20Output%20Linear%20Regulator/RT9193?sc_lang=en) | Waveshare 7B | link only |
| MP1658GTF-Z | [MP1658 3 A buck (product page; MPS has no public PDF link)](https://www.monolithicpower.com/en/mp1658.html) | Waveshare 7B | link only |
| MP1605GTF-Z | [MP1605 2 A buck (product page)](https://www.monolithicpower.com/en/mp1605.html) | Waveshare 7B | link only |
| AO3401A | [AO3401A P-MOSFET (SD power, VBUS OR)](https://www.aosmd.com/res/datasheets/AO3401A.pdf) | Waveshare 7B, ADSB_Test | yes (2026-10-10) |
| ETA6098 | [ETA6098 1S Li-ion charger](https://www.lcsc.com/search?q=ETA6098) | Waveshare 7B | link only |
| STUSB4500 | [STUSB4500 USB-PD sink controller](https://www.st.com/resource/en/datasheet/stusb4500.pdf) | ADSB_Test | yes (manual) |
| BQ25792 | [BQ25792 charger datasheet (saved by hand; TI pages 404 from scripts). BQ25798 is the part used](https://www.ti.com/lit/ds/symlink/bq25792.pdf) | ADSB_Test | yes (manual) |
| BQ25798 | [BQ25798 1-4S buck-boost charger with MPPT (proposed replacement for BQ25792)](https://www.ti.com/lit/ds/symlink/bq25798.pdf) | ADSB_Test | yes (2026-10-10) |
| PAC1954 | [PAC195x family datasheet DS20006539 (power monitor; saved by hand, Microchip blocks scripts)](https://ww1.microchip.com/downloads/aemDocuments/documents/MSLD/ProductDocuments/DataSheets/PAC1951-2-3-4-Single-Multi-Channel-Power-Monitor-with-Accumulator-32V-Full-Scale-Range-DS20006539.pdf) | ADSB_Test | yes (manual) |
| TPS62933 | [TPS62933 3 A buck (3V3)](https://www.ti.com/lit/ds/symlink/tps62933.pdf) | ADSB_Test | yes (2026-10-10) |
| TPS25200 | [TPS25200 eFuse (USB-A VBUS)](https://www.ti.com/lit/ds/symlink/tps25200.pdf) | no longer used | yes (2026-10-10) |
| TPS2596 | [TPS2596 2.7-19 V eFuse (USB-A VBUS; replaces TPS25200, no KiCad symbol)](https://www.ti.com/lit/ds/symlink/tps2596.pdf) | ADSB_Test | yes (2026-10-12) |
| TPS22917 | [TPS22917 load switch (switched rails)](https://www.ti.com/lit/ds/symlink/tps22917.pdf) | ADSB_Test | yes (2026-10-12) |
| DMP3013SFV | [DMP3013SFV -30 V P-MOSFET (USB-PD sink power path)](https://www.diodes.com/assets/Datasheets/DMP3013SFV.pdf) | no longer used | yes (2026-10-12) |
| AP2112K-3.3 | [AP2112 600 mA LDO (ADSBee carrier)](https://www.diodes.com/assets/Datasheets/AP2112.pdf) | ADSB_Test | yes (2026-10-10) |
| FDS9435A | [onsemi FDS9435A P-channel MOSFET, SO-8 (input reverse/ideal switch)](https://www.onsemi.com/pdf/datasheet/fds9435a-d.pdf) | ADSB_Test | yes (2026-10-12) |
| MCP1703 | [Microchip MCP1703 250 mA LDO, 2 uA Iq (VBACKUP)](https://www.microchip.com/en-us/product/MCP1703) | ADSB_Test | yes (manual) |

## interface

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| USBLC6-2SC6 | [USBLC6-2 USB ESD protection](https://www.st.com/resource/en/datasheet/usblc6-2.pdf) | ADSB_Test | yes (manual) |
| IP101GRI | [IP101G family datasheet IP101G-DS-R01 (unofficial distributor mirror; IC Plus has no public link)](https://dfsimg2.hqewimg.com/group1/M00/1E/7E/wKhk72GgdAWACBnTACa6J2TDLkI754.pdf) | no longer used | yes (2026-10-10) |
| USB2514B | [USB2514B 4-port USB 2.0 hub (Microchip product page; site blocks scripts)](https://www.microchip.com/en-us/product/USB2514B) | ADSB_Test | link only (open in a browser) |
| FT2232H | [FT2232H dual USB-UART (FTDI product page; site blocks scripts)](https://ftdichip.com/products/ft2232hq/) | ADSB_Test | link only (open in a browser) |
| CP2102N | [CP2102N USB-UART](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf) | ADSB_Test | yes (manual) |
| CH343P | [CH343 USB-UART (reference board)](https://www.wch-ic.com/products/CH343.html) | Waveshare 7B | link only |
| RP2040 | [RP2040 datasheet](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf) | ADSB_Test | yes (2026-10-10) |
| RP2040 | [Hardware design with RP2040](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf) | ADSB_Test | yes (2026-10-10) |
| DS3231M | [Analog Devices (Maxim) DS3231M +/-5ppm I2C RTC](https://www.analog.com/media/en/technical-documentation/data-sheets/DS3231M.pdf) | ADSB_Test | yes (manual) |
| LAN8720A | [Microchip LAN8720A/LAN8720Ai RMII 10/100 Ethernet PHY](https://www.microchip.com/en-us/product/LAN8720A) | ADSB_Test | yes (manual) |
| MMBT3904 | [onsemi MMBT3904 NPN (Dev auto-reset)](https://www.onsemi.com/pdf/datasheet/mmbt3904lt1-d.pdf) | ADSB_Test | yes (2026-10-12) |
| WS2812B | [Worldsemi WS2812B addressable LED (programmer status)](https://www.world-semi.com/) | ADSB_Test | link only |
| 1N4148W | [Diodes 1N4148W small-signal diode, SOD-123](https://www.diodes.com/part/view/1N4148W) | ADSB_Test | link only |

## memory

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| GD25Q256EYIGR | [GD25Q256E 32 MB QSPI flash](https://www.gigadevice.com/product/flash/spi-nor-flash/gd25q256e) | Waveshare 7B | link only |
| 93LC56B | [Microchip 93LC56B Microwire EEPROM (FT2232H config)](https://www.microchip.com/en-us/product/93LC56B) | ADSB_Test | yes (manual) |
| W25Q16JVSS | [Winbond W25Q16JV 16 Mbit QSPI flash (RP2040)](https://www.winbond.com/hq/product/code-storage-flash-memory/serial-nor-flash/?__locale=en&partNo=W25Q16JV) | ADSB_Test | link only |

## logic

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| TCA6408A | [TCA6408A I2C GPIO expander](https://www.ti.com/lit/ds/symlink/tca6408a.pdf) | ADSB_Test | yes (2026-10-10) |
| 74LVC1G157 (Nexperia) | [2:1 mux alternative (not used: no KiCad symbol; 74LVC1G97 used instead)](https://assets.nexperia.com/documents/data-sheet/74LVC1G157.pdf) | no longer used | yes (2026-10-10) |
| 74LVC1G97 (Nexperia) | [Configurable gate used as 2:1 mux (m1421 UART RX); KiCad has no 74LVC1G157 symbol](https://assets.nexperia.com/documents/data-sheet/74LVC1G97.pdf) | ADSB_Test | yes (2026-10-12) |
| SN74LVC1G32 | [OR gate (m1421 SYNC)](https://www.ti.com/lit/ds/symlink/sn74lvc1g32.pdf) | ADSB_Test | yes (2026-10-10) |
| SN74LVC1G07 | [Open-drain buffer (resets)](https://www.ti.com/lit/ds/symlink/sn74lvc1g07.pdf) | ADSB_Test | yes (2026-10-10) |
| SN74LVC1G125 | [3-state buffer (Dev isolation)](https://www.ti.com/lit/ds/symlink/sn74lvc1g125.pdf) | ADSB_Test | yes (2026-10-10) |
| SN74LVC2T45 | [Dual level translator (Dev isolation)](https://www.ti.com/lit/ds/symlink/sn74lvc2t45.pdf) | no longer used | yes (2026-10-10) |

## rf

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| MAX-M10S | [u-blox MAX-M10S GNSS](https://content.u-blox.com/sites/default/files/MAX-M10S_DataSheet_UBX-20035208.pdf) | ADSB_Test | yes (2026-10-10) |
| MAX-M10S | [u-blox MAX-M10S integration manual](https://content.u-blox.com/sites/default/files/MAX-M10S_IntegrationManual_UBX-20053088.pdf) | ADSB_Test | yes (2026-10-10) |
| SCN-2-11+ | [Mini-Circuits SCN-2-11+ power splitter/combiner](https://www.minicircuits.com/pdfs/SCN-2-11+.pdf) | ADSB_Test | yes (2026-10-10) |
| ESD7351 | [ESD7351 RF ESD diode](https://www.onsemi.com/download/data-sheet/pdf/esd7351-d.pdf) | ADSB_Test | yes (2026-10-10) |
| Laird BMI-S-203-F / -C | [Laird BMI-S-203-F shield frame (26.21 mm) - DigiKey page with datasheet](https://www.digikey.com/en/products/detail/laird-technologies-emi/BMI-S-203-F/2175890) | ADSB_Test | link only |
| Laird BMI-S-202-F / -C | [Laird BMI-S-202-F shield frame 16.5 mm (GNSS can)](https://www.digikey.com/en/products/result?keywords=BMI-S-202-F) | ADSB_Test | link only |

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

## connectors

| Part | Document | Boards | Local |
|------|----------|--------|-------|
| HR911105A | [Hanrun HR911105A RJ45 MagJack (magnetics + LEDs)](https://www.hanrun.com/) | ADSB_Test | link only |
| Molex 104031-0811 | [Molex 104031-0811 microSD push-push with detect](https://www.molex.com/en-us/products/part-detail/1040310811) | ADSB_Test | yes (manual) |
| Hirose FH12 | [Hirose FH12 0.5 mm FPC connectors (LCD 30p, touch 6p)](https://www.hirose.com/en/product/series/FH12) | ADSB_Test | link only |
| GCT USB4105 | [GCT USB4105 USB-C 2.0 16-pin receptacle (User, Dev)](https://gct.co/connector/usb4105) | ADSB_Test | link only |
| Molex 67643 | [Molex 67643 USB-A receptacle, through-hole (SDR host)](https://www.molex.com/en-us/products/part-detail/676432910) | ADSB_Test | yes (manual) |
| SMA-J-P-H-ST-EM1 | [Samtec SMA-J-P-H-ST-EM1 edge-mount SMA (ADS-B, GNSS)](https://www.samtec.com/products/sma-j-p-h-st-em1) | ADSB_Test | link only |
| OS102011MA1Q | [C&K OS series slide switch (POWER)](https://www.ckswitches.com/media/1428/os.pdf) | ADSB_Test | yes (manual) |
