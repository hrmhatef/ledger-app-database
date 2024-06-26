#!/usr/bin/env python3

import json
import difflib
from argparse import ArgumentParser
from pathlib import Path
from app_load_params_utils import format_database
from app_load_params_check import PARAMS_VALUE_CHECK


def check_database_lint(database_path: Path):
    ret = 0
    with open(database_path, 'r') as f:
        database_str = f.read()
        database = json.loads(database_str)

    for variant, params in database.items():
        for param, value in params.items():
            if param not in PARAMS_VALUE_CHECK.keys():
                print(f"[ERROR] Not allowed '{param}' in variant '{variant}'")
                ret = -1

            # Special case for appFlags which value is unique per device
            if param == "appFlags":
                if not isinstance(value, dict):
                    print(f"[ERROR] Wrong type for '{param}' in variant '{variant}'")
                    ret = -1
                else:
                    for device, device_flags in value.items():
                        if device not in ["flex", "nanos", "nanox", "nanos2", "stax"]:
                            print(f"[ERROR] Unknown device type '{device}' in variant '{variant}'")
                            ret = -1
                        elif not isinstance(device_flags, str):
                            print(f"[ERROR] Wrong type for '{param}' in variant '{variant}'")
                        elif not device_flags.startswith("0x"):
                            print(f"[ERROR] Device appFlags should start with '0x' in variant '{variant}'")

            elif not isinstance(value, PARAMS_VALUE_CHECK[param]):
                print(f"[ERROR] Wrong type for '{param}' in variant '{variant}'")
                ret = -1

        for param in ["appName", "appFlags", "path"]:
            if param not in params:
                print(f"[ERROR] Missing '{param}' in variant '{variant}'")
                ret = -1

    # Splitlines put keep line ends and escape it to make them visible.
    a = [repr(x)[1:-1] for x in database_str.splitlines(keepends=True)]
    b = [repr(x)[1:-1] for x in format_database(database).splitlines(keepends=True)]
    res = list(difflib.unified_diff(a, b))
    if res:
        ret = -1
        print("[ERROR] Database is not properly linted, see diff below:")
        for line in res:
            print(line)

    if ret != 0:
        exit(ret)


def check_database_appnames(database_path: Path):
    ret = 0
    with open(database_path, 'r') as f:
        database_str = f.read()
        database = json.loads(database_str)

    db_rev = {v["appName"].lower().replace(" ","").replace("_", "").replace("-", ""): k for k,
              v in database.items()}

    for variant, params in database.items():
        app_name = params["appName"]
        db_rev_variant = db_rev[app_name.lower().replace(" ","").replace("_", "").replace("-", "")]
        if db_rev_variant != variant:
            print(f"[ERROR] Conflict on appName between '{db_rev_variant}' and '{variant}'. AppName shall be unique ('-',' ' and '_' are stripped)")
            ret = -1

    if ret != 0:
        exit(ret)


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("--database_path", required=True, type=Path)
    parser.add_argument("--check_lint", action="store_true")
    parser.add_argument("--check_appnames", action="store_true")

    args = parser.parse_args()

    if args.check_lint:
        check_database_lint(args.database_path)
    elif args.check_appnames:
        check_database_appnames(args.database_path)
    else:
        parser.print_help()
