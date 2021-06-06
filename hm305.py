#!/usr/bin/python3

import sys
import serial
import logging

from hm305 import HM305

logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    serial_parser = parser.add_mutually_exclusive_group(required=True)
    serial_parser.add_argument("--port", type=str, help="serial port")

    volt_parser = parser.add_mutually_exclusive_group()
    volt_parser.add_argument("--voltage", type=float, help="set voltage")
    volt_parser.add_argument(
        "--adj-voltage", metavar="X", type=float, help="adjust voltage by X"
    )
    current_parser = parser.add_mutually_exclusive_group()
    current_parser.add_argument("--current", type=float, help="set current")

    output_parser = parser.add_mutually_exclusive_group()
    output_parser.add_argument("--on", action="store_true", help="switch output on")
    output_parser.add_argument("--off", action="store_true", help="switch output off")
    beep_parser = parser.add_mutually_exclusive_group()
    beep_parser.add_argument("--beep", action="store_true", help="enable beeping")
    beep_parser.add_argument("--nobeep", action="store_true", help="disable beeping")

    parser.add_argument("--debug", action="store_true", help="enable verbose logging")
    parser.add_argument("--get", action="store_true", help="report output measurements")
    parser.add_argument(
        "--get-power", action="store_true", help="report output power in W"
    )
    parser.add_argument(
        "--get-voltage-max", action="store_true", help="report possible max voltage"
    )
    parser.add_argument(
        "--get-memory", action="store_true", help="get MEMORY key settings"
    )
    parser.add_argument("--info", action="store_true", help="get PSU info")

    def auto_int(x):
        return int(x, 0)

    parser.add_argument("--raw", type=auto_int, help="get a raw address")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        # display help message when no args are passed.
        parser.print_help()
        sys.exit(1)

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    with serial.Serial(args.port, baudrate=9600, timeout=0.1) as ser:
        hm = HM305(ser)
        if args.voltage is not None:
            logging.info("Setting voltage:")
            hm.voltage.instrument_setpoint = args.voltage
        elif args.adj_voltage is not None:
            logging.info("Adjusting voltage:")
            hm.voltage.instrument_setpoint += args.adj_voltage
        if args.current is not None:
            logging.info("Setting current:")
            hm.current.value = args.current
        if args.beep:
            logging.info("Setting beep: ON")
            hm.beep = 1
        elif args.nobeep:
            logging.info("Setting beep: OFF")
            hm.beep = 0
        if args.off:
            logging.info("Setting output: OFF")
            hm.off()
        elif args.on:
            logging.info("Setting output: ON")
            hm.on()
        if args.get:
            logging.info(f"{hm.voltage.value} Volts")
            logging.info(f"{hm.current.value} Amps")
            logging.info(f"{hm.w} Watts")
        if args.get_power:
            logging.info(f"{hm.w} Watts")
        if args.get_voltage_max:
            logging.info(f"{hm.vmax} Volts")
        if args.get_memory:
            memory_values = hm.memory
            logging.info("Memory Key Presets:")
            for key in memory_values:
                logging.info(f"{key} : {memory_values[key]['Volts']} Volts")
                logging.info(f"{key} : {memory_values[key]['Amps']} Amps")
                logging.info(f"{key} : {memory_values[key]['Time_span']} Time Span")
                logging.info(f"{key} : {memory_values[key]['Enabled']} Enabled")
        if args.info:
            logging.info(
                f"Info:\n"
                f"Model: {hm.model}\n"
                f"protect_state {hm.protect_state}\n"
                f"decimals: {hex(hm.decimals)}\n"
                f"class_details: {hex(hm.classdetail)}\n"
                f"Device: {hm.device}"
            )
        if args.raw:
            val = hm.modbus.get_by_addr(args.raw)
            logging.info(f"{args.raw: x}: {val} / {val: x}")
    logging.debug("Done")
