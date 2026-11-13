#!/usr/bin/env python3
"""Parse fixed-record headers and rows from Tây Du Chiến Ký .dat resources."""
import argparse, json, struct
from pathlib import Path
WIDTHS={1:1,2:2,4:4}
FORMATS={1:">b",2:">h",4:">i"}
def parse_dat(path):
    data=path.read_bytes()
    if len(data)<5: raise ValueError(f"{path}: short header")
    marker,count=struct.unpack_from(">HH",data,0)
    field_count=data[4]; start=5+field_count
    types=list(data[5:start])
    unknown=sorted(set(types)-WIDTHS.keys())
    if unknown: raise ValueError(f"{path}: unknown field types {unknown}")
    row_size=sum(WIDTHS[t] for t in types); end=start+count*row_size
    if end>len(data): raise ValueError(f"{path}: records exceed file")
    rows=[]; pos=start
    for _ in range(count):
        row=[]
        for t in types:
            row.append(struct.unpack_from(FORMATS[t],data,pos)[0]); pos+=WIDTHS[t]
        rows.append(row)
    trailer=data[end:]
    text=trailer[2:].decode("utf-8","replace") if len(trailer)>=2 else ""
    return {"file":path.name,"sizeBytes":len(data),"tableMarker":marker,
      "recordCount":count,"fieldCount":field_count,"fieldTypes":types,
      "recordSizeBytes":row_size,"headerBytes":start,"recordsEndOffset":end,
      "records":rows,"trailerBytes":len(trailer),"trailerPrefixHex":trailer[:2].hex(),
      "trailerTextUtf8View":text,"trailerSemicolonEntries":[s for s in text.split(";") if s],
      "fullyConsumed":end==len(data)}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("data_dir",type=Path); ap.add_argument("-o","--output",type=Path); args=ap.parse_args()
    tables=[parse_dat(p) for p in sorted(args.data_dir.glob("*.dat"))]
    result={"format":"TDCK-DAT-inspection-v1","fileCount":len(tables),
      "typeCodeNotes":{"1":"signed byte","2":"signed big-endian short","4":"signed big-endian int; checked against exp.dat"},
      "trailerNote":"Preserved; UTF-8/semicolon view is exploratory; string-table semantics are not decoded.","tables":tables}
    payload=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output: args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(payload,encoding="utf-8")
    else: print(payload)
    print(f"Parsed {len(tables)} DAT files; {sum(t['fullyConsumed'] for t in tables)} without trailer.")
if __name__=="__main__": main()
