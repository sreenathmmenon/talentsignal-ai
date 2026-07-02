#!/usr/bin/env python3
"""Generate the submission XLSX from the validated submission CSV — stdlib only.

The portal asks for the ranked output in XLSX format. This writes a real .xlsx
(a minimal OOXML zip) with the SAME four columns and rows as the CSV, so the two
are identical in content and the XLSX is reproducible (never hand-edited).

  python3 scripts/make_xlsx.py                       # csv -> xlsx (defaults below)
  python3 scripts/make_xlsx.py --csv X.csv --out Y.xlsx
"""
from __future__ import annotations

import argparse
import csv
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]


def _col(n: int) -> str:
    s = ""
    n += 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def build_xlsx(rows: list[list[str]], out: Path) -> None:
    # sheet: every cell inline-string typed (t="inlineStr") — no shared-strings table,
    # so the file is self-contained and trivially correct.
    sheet_rows = []
    for r_i, row in enumerate(rows, 1):
        cells = []
        for c_i, val in enumerate(row):
            ref = f"{_col(c_i)}{r_i}"
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(str(val))}</t></is></c>')
        sheet_rows.append(f'<row r="{r_i}">{"".join(cells)}</row>')
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>"
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="submission" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=str(ROOT / "outputs" / "final_submission.csv"))
    ap.add_argument("--out", default=str(ROOT / "outputs" / "final_submission.xlsx"))
    args = ap.parse_args()
    rows = list(csv.reader(open(args.csv, encoding="utf-8")))
    if not rows or rows[0] != ["candidate_id", "rank", "score", "reasoning"]:
        raise SystemExit(f"CSV header must be candidate_id,rank,score,reasoning — got {rows[0] if rows else 'empty'}")
    build_xlsx(rows, Path(args.out))
    print(f"Wrote {args.out} — {len(rows) - 1} candidates, 4 columns, from {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
