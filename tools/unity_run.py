#!/usr/bin/env python3
"""Run Unity test-app tests over a serial port and capture the output.

Resets the board via DTR/RTS (CH343 / USB-UART auto-reset wiring), waits for the
Unity menu, sends each test selector (a tag such as "[i2c]", a test number, or a
quoted test name) and prints everything until Unity's summary line.

Usage (from the ESP-IDF Python environment, which has pyserial):
    python tools/unity_run.py -p COM4 "[bsp]" "[i2c]"
    python tools/unity_run.py -p COM4 --timeout 60 "[usb]"
    python tools/unity_run.py -p COM4 --log out.txt "*"
"""
import argparse
import re
import sys
import time

import serial

SUMMARY = re.compile(rb"(\d+) Tests (\d+) Failures (\d+) Ignored")
MENU = b"Press ENTER to see the list of tests"
PROMPT = b"Enter test for running."


def reset(port):
    """EN low via RTS, IO0 high via DTR, then release: normal boot."""
    port.dtr = False
    port.rts = True
    time.sleep(0.2)
    port.rts = False
    time.sleep(0.05)


def read_until(port, patterns, timeout, out):
    buf = b""
    end = time.time() + timeout
    while time.time() < end:
        chunk = port.read(port.in_waiting or 1)
        if chunk:
            out.write(chunk.decode(errors="replace"))
            out.flush()
            buf += chunk
            for pat in patterns:
                m = pat.search(buf) if hasattr(pat, "search") else (pat if pat in buf else None)
                if m:
                    return buf, m
    return buf, None


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, s):
        for st in self.streams:
            st.write(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", required=True)
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("--timeout", type=float, default=90, help="seconds per test selector")
    ap.add_argument("--no-reset", action="store_true")
    ap.add_argument("--log", help="also write output to this file")
    ap.add_argument("tests", nargs="+")
    args = ap.parse_args()

    log = open(args.log, "w", encoding="utf-8") if args.log else None
    out = Tee(sys.stdout, log) if log else sys.stdout

    port = serial.Serial(args.port, args.baud, timeout=0.1)
    if not args.no_reset:
        reset(port)
    _, m = read_until(port, [MENU, PROMPT], 20, out)
    if not m:
        port.write(b"\n")
        _, m = read_until(port, [PROMPT], 10, out)
    if not m:
        print("\n!! Unity menu not seen", file=sys.stderr)
        return 2

    failures = 0
    for t in args.tests:
        out.write(f"\n===== running {t} =====\n")
        port.write(t.encode() + b"\n")
        _, m = read_until(port, [SUMMARY], args.timeout, out)
        if not m:
            out.write(f"\n!! timeout waiting for summary of {t}\n")
            failures += 1
            port.write(b"\n")
            continue
        failures += int(m.group(2))
        read_until(port, [PROMPT], 5, out)
    port.close()
    out.write(f"\n===== done: {'OK' if failures == 0 else f'{failures} failure(s)/timeout(s)'} =====\n")
    if log:
        log.close()
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
