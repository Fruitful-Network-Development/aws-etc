#!/usr/bin/env python3
import argparse
import csv
import json
import re
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ORDINAL_RE = re.compile(r"^\d+(st|nd|rd|th)$", re.IGNORECASE)
DATE_RE = re.compile(r"^\d{1,2}-[A-Z]{3}-\d{2,4}$")  # e.g. 02-JAN-2026, 07-OCT-19


def slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace("&", " and ")
    s = re.sub(r"[-\s]+", "_", s)
    s = re.sub(r"[^a-z0-9_]", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def clean(s: str) -> str:
    return (s or "").strip()


def looks_like_city(token: str) -> bool:
    t = clean(token)
    if not t:
        return False
    # ignore date-like fields
    if DATE_RE.match(t):
        return False
    # must contain at least one letter
    if not re.search(r"[A-Za-z]", t):
        return False
    # reject obvious single-letter codes
    if len(t) == 1:
        return False
    return True


def pick_city(row: dict) -> Optional[str]:
    """
    Your file's data rows are not aligned with the header in the CITY area:
    BARBERTON shows up under UDATE1, while CITY is spaces.
    So we try a sequence of candidates.
    """
    candidates = [
        row.get("CITY", ""),
        row.get("UDATE1", ""),   # this is where BARBERTON appears in your file
        row.get("USER9", ""),
        row.get("UDATE2", ""),
        row.get("UDATE3", ""),
    ]
    for c in candidates:
        if looks_like_city(c):
            return clean(c)
    return None


def is_ordinal_street(name: str, suffix: str) -> bool:
    n = clean(name)
    suf = clean(suffix)
    if not n or not suf:
        return False
    if slug(suf) != "st":
        return False
    return bool(ORDINAL_RE.match(n.lower()))


def build_street_key(street_name: str, street_suffix: str) -> Tuple[str, bool]:
    name = slug(street_name)
    suf = slug(street_suffix)
    if not name:
        return "", False

    if is_ordinal_street(street_name, street_suffix):
        return name, True

    if suf:
        if name.endswith(f"_{suf}") or name == suf:
            return name, False
        return f"{name}_{suf}", False

    return name, False


def parse_additional_numbers(adradd: str) -> List[str]:
    s = clean(adradd)
    if not s:
        return []
    return re.findall(r"\d+", s)


def build_address_key(
    number: str,
    direction: str,
    street_key: str,
    ordinal_flag: bool,
    unit: Optional[str]
) -> str:
    num = slug(number)
    if not num:
        return ""

    dir_slug = slug(direction)
    unit_slug = slug(unit) if unit else ""

    if ordinal_flag:
        base = num
    else:
        parts = [num]
        if dir_slug:
            parts.append(dir_slug)
        parts.append(street_key)
        base = "_".join([p for p in parts if p])

    if unit_slug:
        base = f"{base}_unit_{unit_slug}"

    return base


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Build Summit County hierarchy JSON (comunities->streets->addresses) with sequential IDs."
    )
    ap.add_argument("--in", dest="infile", default="SC705_PARDAT.CSV")
    ap.add_argument("--out", dest="outfile", default="summit_county_addresses.json")
    ap.add_argument("--prefix", default="3_2_35_77")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--debug", action="store_true", help="Print diagnostics about skipped rows.")
    args = ap.parse_args()

    in_path = Path(args.infile)
    out_path = Path(args.outfile)

    if not in_path.exists():
        raise FileNotFoundError(f"Missing input: {in_path.resolve()}")

    communities: "OrderedDict[str, Dict]" = OrderedDict()

    with in_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("Could not read CSV header row; DictReader fieldnames are empty.")

        required = {"ADRNO", "ADRSTR", "ADRSUF"}  # CITY is unreliable in this file
        missing = sorted(required - set(reader.fieldnames))
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}. Found: {reader.fieldnames}")

        rows_used = 0
        rows_skipped = 0
        skipped_reasons = {"no_city": 0, "no_adrno": 0, "no_street": 0}

        for row_i, row in enumerate(reader, start=1):
            if args.limit and row_i > args.limit:
                break

            city_raw = pick_city(row)
            if not city_raw:
                rows_skipped += 1
                skipped_reasons["no_city"] += 1
                continue
            city_key = slug(city_raw)
            if not city_key:
                rows_skipped += 1
                skipped_reasons["no_city"] += 1
                continue

            adrno = clean(row.get("ADRNO", ""))
            adradd = clean(row.get("ADRADD", ""))
            adrir = clean(row.get("ADRDIR", ""))
            adrstr = clean(row.get("ADRSTR", ""))
            adrsuf = clean(row.get("ADRSUF", ""))
            unit = clean(row.get("LVU", "")) or None

            if not adrno:
                rows_skipped += 1
                skipped_reasons["no_adrno"] += 1
                continue

            if not adrstr:
                rows_skipped += 1
                skipped_reasons["no_street"] += 1
                continue

            street_key, ordinal_flag = build_street_key(adrstr, adrsuf)
            if not street_key:
                rows_skipped += 1
                skipped_reasons["no_street"] += 1
                continue

            numbers = [adrno] + parse_additional_numbers(adradd)

            if city_key not in communities:
                comm_index = len(communities) + 1
                communities[city_key] = {
                    "id": f"{args.prefix}_{comm_index}",
                    "streets": OrderedDict(),
                }

            comm = communities[city_key]
            streets: "OrderedDict[str, Dict]" = comm["streets"]

            if street_key not in streets:
                street_index = len(streets) + 1
                streets[street_key] = {
                    "id": f"{comm['id']}_{street_index}",
                    "addresses": OrderedDict(),
                }

            street_obj = streets[street_key]
            addresses: "OrderedDict[str, str]" = street_obj["addresses"]

            for num in numbers:
                addr_key = build_address_key(num, adrir, street_key, ordinal_flag, unit)
                if not addr_key:
                    continue
                if addr_key in addresses:
                    continue
                addr_index = len(addresses) + 1
                addresses[addr_key] = f"{street_obj['id']}_{addr_index}"

            rows_used += 1

    comunities_out: List[Dict] = []
    for city_key, comm in communities.items():
        city_entry: Dict[str, object] = {city_key: comm["id"]}

        streets_out: List[Dict] = []
        for street_key, s_obj in comm["streets"].items():
            street_entry: Dict[str, object] = {street_key: s_obj["id"]}

            addr_out: List[Dict[str, str]] = []
            for addr_key, addr_id in s_obj["addresses"].items():
                addr_out.append({addr_key: addr_id})

            street_entry["addresses"] = addr_out
            streets_out.append(street_entry)

        if streets_out:
            city_entry["streets"] = streets_out

        comunities_out.append(city_entry)

    out_obj = {"comunities": comunities_out}
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {out_path} (communities={len(comunities_out)})")
    if args.debug:
        print(f"Rows used={rows_used}, rows skipped={rows_skipped}, skipped reasons={skipped_reasons}")


if __name__ == "__main__":
    main()

