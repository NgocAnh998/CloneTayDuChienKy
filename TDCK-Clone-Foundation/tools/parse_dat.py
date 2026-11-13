#!/usr/bin/env python3
"""Inspect the fixed-record header and payload of Tây Du Chiến Ký .dat tables.

Confirmed from the supplied JAR and lx.game bytecode:
- big-endian header: u16 table marker, u16 record count, u8 field count;
- field descriptors: 1 = signed byte, 2 = signed short, 4 = signed int;
- records are stored consecutively in descriptor order;
- exp.dat is fully explained by this layout (200 records x 6 bytes).

For the other tables, bytes after the fixed records are retained as an opaque
trailer. A UTF-8/semicolon view is emitted only as an inspection aid; it is not
yet claimed to be the complete semantic string-table format.
"""
from __future__ import annotations
import argparse, json, struct
from pathlib import Path

WIDTHS = {1: 1, 2: 2, 4: 4}
FORMATS = {1: '>b', 2: '>h', 4: '>i'}


def parse_dat(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 5:
        raise ValueError(f'{path}: shorter than common 5-byte header')
    table_marker, record_count = struct.unpack_from('>HH', data, 0)
    field_count = data[4]
    header_end = 5 + field_count
    if header_end > len(data):
        raise ValueError(f'{path}: field descriptors exceed file size')
    types = list(data[5:header_end])
    unknown = sorted(set(types) - WIDTHS.keys())
    if unknown:
        raise ValueError(f'{path}: unknown field type codes {unknown}')
    row_size = sum(WIDTHS[t] for t in types)
    records_end = header_end + record_count * row_size
    if records_end > len(data):
        raise ValueError(f'{path}: fixed records exceed file size')
    records = []
    pos = header_end
    for _ in range(record_count):
        row = []
        for t in types:
            row.append(struct.unpack_from(FORMATS[t], data, pos)[0])
            pos += WIDTHS[t]
        records.append(row)
    trailer = data[records_end:]
    trailer_prefix = trailer[:2].hex() if len(trailer) >= 2 else trailer.hex()
    text_bytes = trailer[2:] if len(trailer) >= 2 else b''
    text_view = text_bytes.decode('utf-8', errors='replace')
    text_entries = [s for s in text_view.split(';') if s]
    return {
        'file': path.name,
        'sizeBytes': len(data),
        'tableMarker': table_marker,
        'recordCount': record_count,
        'fieldCount': field_count,
        'fieldTypes': types,
        'fieldTypeNames': [{'1': 'signed_byte', '2': 'signed_short', '4': 'signed_int'}[str(t)] for t in types],
        'recordSizeBytes': row_size,
        'headerBytes': header_end,
        'recordsEndOffset': records_end,
        'records': records,
        'trailerBytes': len(trailer),
        'trailerPrefixHex': trailer_prefix,
        'trailerTextUtf8View': text_view,
        'trailerSemicolonEntries': text_entries,
        'fullyConsumed': records_end == len(data),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data_dir', type=Path, help='directory containing .dat files')
    ap.add_argument('-o', '--output', type=Path, default=None)
    args = ap.parse_args()
    results = [parse_dat(p) for p in sorted(args.data_dir.glob('*.dat'))]
    out = {'format': 'TDCK-DAT-inspection-v1', 'fileCount': len(results), 'typeCodeNotes': {
        '1': 'signed byte (inferred from fixed-width record layout)',
        '2': 'signed big-endian short (inferred from fixed-width record layout)',
        '4': 'signed big-endian int; independently confirmed by exp.dat values',
    }, 'trailerNote': 'Trailer is preserved and its UTF-8 semicolon view is exploratory; string indexing/meaning is not yet decoded.', 'tables': results}
    payload = json.dumps(out, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding='utf-8')
    else:
        print(payload)
    print(f'Parsed {len(results)} DAT files; {sum(t["fullyConsumed"] for t in results)} have no trailer.', flush=True)

if __name__ == '__main__':
    main()
