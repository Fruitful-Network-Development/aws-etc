# !/usr/bin/env python3

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


# Column indices (0-based) for THIS export (based on your header probes)
IDX_STREET_NUMBER = 6   # ADRADD (street number)
IDX_STREET_DIR    = 7   # often direction like N/S/E/W (verify if needed)
IDX_STREET_NAME   = 8   # ADRSTR (street name)
IDX_STREET_SUFFIX = 9   # ADRSUF (ST/AVE/RD/BLVD)
IDX_UNIT          = 15  # LVU    (living unit)
IDX_CITY          = 50  # UDATE1 contains BARBERTON etc. per your probe


def norm_city(x: str) -> str:
    return (x or "").strip().upper()


def norm_token(x: str) -> str:
    return (x or "").strip().upper()


def slug(x: str) -> str:
    """lowercase underscore slug for keys"""
    x = (x or "").strip().lower()
    x = x.replace("&", " and ")
    x = re.sub(r"[\s\-]+", "_", x)
    x = re.sub(r"[^a-z0-9_]", "", x)
    x = re.sub(r"_+", "_", x).strip("_")
    return x


def make_street_key(dir_: str, name: str, suf: str) -> str:
    """
    Street key used as JSON key. Includes suffix to avoid collisions.
    Example: "summit_st", "31st_st"
    """
    parts = [slug(dir_), slug(name), slug(suf)]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    # If direction missing, still okay.
    return "_".join(parts)


def make_address_key(number: str, dir_: str, name: str, suf: str, unit: str) -> str:
    """
    Address key used as JSON key.
    Example: "860_n_summit_st", "168_sw_31st_st", optionally "..._unit_12"
    """
    parts = [slug(number), slug(dir_), slug(name), slug(suf)]
    parts = [p for p in parts if p]
    if unit.strip():
        parts.append("unit_" + slug(unit))
    return "_".join(parts)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Split Summit County parcel addresses into one JSON per canonical community with sequential IDs."
    )
    ap.add_argument("--in", dest="infile", default="SC705_PARDAT.CSV", help="Input CSV")
    ap.add_argument("--outdir", default="out", help="Output directory for community JSON files")
    ap.add_argument("--limit", type=int, default=0, help="Optional row limit for testing")
    ap.add_argument("--skip-header", action="store_true", default=True, help="Skip first CSV row (headers)")

    # Allow overriding indices if needed
    ap.add_argument("--idx-city", type=int, default=IDX_CITY)
    ap.add_argument("--idx-number", type=int, default=IDX_STREET_NUMBER)
    ap.add_argument("--idx-dir", type=int, default=IDX_STREET_DIR)
    ap.add_argument("--idx-street", type=int, default=IDX_STREET_NAME)
    ap.add_argument("--idx-suffix", type=int, default=IDX_STREET_SUFFIX)
    ap.add_argument("--idx-unit", type=int, default=IDX_UNIT)

    args = ap.parse_args()

    in_path = Path(args.infile)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        raise FileNotFoundError(f"Missing input CSV: {in_path.resolve()}")

    # Exclusions you listed
    EXCLUDE = {
        "MONTVILLE", "MARSHALLVIL", "DELLROY", "CANAL FULTO", "BEDFORD", "BRECKSVILLE",
        "MENTOR", "DOYLESTOWN", "MEDINA", "WADSWORTH", "KENT", "AURORA", "MORGANTOWN",
        "COLUMBUS", "WAYNESBURG",
    }

    # Raw city token -> canonical community
    RAW_TO_CANON = {
        "AKRON": "akron",
        "AKRON OHIO": "akron",
        "BARBERTON": "barberton",
        "E BARBERTON": "barberton",
        "CUYAHOGA FA": "cuyahoga_falls",
        "FAIRLAWN": "fairlawn",
        "GREEN": "green",
        "UNIONTOWN": "green",
        "HUDSON": "hudson",
        "MACEDONIA": "macedonia",
        "MUNROE FALL": "munroe_falls",
        "NEW FRANKLI": "new_franklin",
        "NORTON": "norton",
        "STOW": "stow",
        "TALLMADGE": "tallmadge",
        "TWINSBURG": "twinsburg",
        "BOSTON HEIG": "boston_heights",
        "CLINTON": "clinton",
        "LAKEMORE": "lakemore",
        "MOGADORE": "mogadore",
        "NORTHFIELD": "northfield",
        "PENINSULA": "peninsula",
        "RICHFIELD": "richfield",
        "SILVER LAKE": "silver_lake",
        "COVENTRY TO": "coventry",
        "NORTH CANTO": "sagamore_hills",
        "BATH": "bath",
        "HINCKLEY": "bath",
        "COPLEY": "copley",
    }

    # Canonical community -> REQUIRED numeric ID (your provided mapping)
    CANON_TO_NUM = {
        "akron": 1,
        "barberton": 2,
        "cuyahoga_falls": 3,
        "fairlawn": 4,
        "green": 5,
        "hudson": 6,
        "macedonia": 7,
        "munroe_falls": 8,
        "new_franklin": 9,
        "norton": 10,
        "stow": 11,
        "tallmadge": 12,
        "twinsburg": 13,
        "boston_heights": 14,
        "clinton": 15,
        "lakemore": 16,
        "mogadore": 17,
        "northfield": 18,
        "peninsula": 19,
        "richfield": 21,
        "silver_lake": 22,
        "coventry": 23,
        "sagamore_hills": 26,
        "bath": 29,
        "copley": 31,
    }

    # Gather: canon -> street_key -> set(address_keys)
    store: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

    # Diagnostics
    unmapped_raw: Dict[str, int] = defaultdict(int)
    excluded_raw: Dict[str, int] = defaultdict(int)

    with in_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        if args.skip_header:
            next(reader, None)

        for row_i, row in enumerate(reader, start=1):
            if args.limit and row_i > args.limit:
                break

            # guard
            needed = max(args.idx_city, args.idx_number, args.idx_dir, args.idx_street, args.idx_suffix, args.idx_unit)
            if len(row) <= needed:
                continue

            raw_city = norm_city(row[args.idx_city])
            if not raw_city:
                continue

            if raw_city in EXCLUDE:
                excluded_raw[raw_city] += 1
                continue

            canon = RAW_TO_CANON.get(raw_city)
            if not canon:
                unmapped_raw[raw_city] += 1
                continue

            # Address parts
            number = norm_token(row[args.idx_number])
            dir_ = norm_token(row[args.idx_dir])
            name = norm_token(row[args.idx_street])
            suf = norm_token(row[args.idx_suffix])
            unit = norm_token(row[args.idx_unit])

            if not number or not name:
                continue

            street_key = make_street_key(dir_, name, suf)
            if not street_key:
                continue

            addr_key = make_address_key(number, dir_, name, suf, unit)
            if not addr_key:
                continue

            store[canon][street_key].add(addr_key)

    # Write one JSON per canonical community
    for canon, streets in store.items():
        if canon not in CANON_TO_NUM:
            # Canon exists but no configured numeric ID
            # Skip writing to avoid inconsistent IDs.
            continue

        comm_num = CANON_TO_NUM[canon]
        # Stable sort streets and addresses
        street_keys_sorted = sorted(streets.keys())

        out_list: List[Dict] = []
        for s_idx, street_key in enumerate(street_keys_sorted, start=1):
            street_id = f"{comm_num}_{s_idx}"
            addr_keys_sorted = sorted(streets[street_key])

            addresses_out = []
            for a_idx, addr_key in enumerate(addr_keys_sorted, start=1):
                addr_id = f"{comm_num}_{s_idx}_{a_idx}"
                addresses_out.append({addr_key: addr_id})

            out_list.append({
                street_key: street_id,
                "addresses": addresses_out
            })

        out_obj = {canon: out_list}
        out_path = outdir / f"{canon}.json"
        out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Print summary
    print(f"Wrote {len(store)} community files into: {outdir}")
    if unmapped_raw:
        print("\nUnmapped raw city tokens (top 25):")
        for k, v in sorted(unmapped_raw.items(), key=lambda kv: kv[1], reverse=True)[:25]:
            print(f"  {k}: {v} rows")
    if excluded_raw:
        print("\nExcluded raw city tokens (top 25):")
        for k, v in sorted(excluded_raw.items(), key=lambda kv: kv[1], reverse=True)[:25]:
            print(f"  {k}: {v} rows")


if __name__ == "__main__":
    main()
