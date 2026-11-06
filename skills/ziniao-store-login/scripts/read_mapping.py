"""Read the user's XLS contact map; never write to the workbook or send messages."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

DEFAULT_WORKBOOK = Path(__file__).resolve().parents[1] / "assets" / "验证码请求飞书.xls"
REQUIRED_HEADERS = ("机器名称", "员工UserID", "姓名")
VENDOR = Path(__file__).resolve().parents[1] / "vendor"


def parse_rows(sheet, matrix):
    if not matrix:
        raise ValueError(f"{sheet}: 工作表为空")
    headers = [str(value).strip() for value in matrix[0]]
    if any(headers.count(name) != 1 for name in REQUIRED_HEADERS):
        raise ValueError(f"{sheet}: 必须有且仅有一个表头：机器名称、员工UserID、姓名")
    indices = [headers.index(name) for name in REQUIRED_HEADERS]
    result = []
    for row_number, cells in enumerate(matrix[1:], start=2):
        if not any(str(value).strip() for value in cells):
            continue
        values = [str(cells[i]).strip() if i < len(cells) else "" for i in indices]
        if not all(values):
            raise ValueError(f"{sheet} 第 {row_number} 行：机器名称、员工UserID、姓名均不得为空")
        store, open_id, name = values
        if not re.fullmatch(r"ou_[A-Za-z0-9]+", open_id):
            raise ValueError(f"{sheet} 第 {row_number} 行：员工UserID 必须是飞书 open_id（ou_ 开头）")
        result.append({"store": store, "open_id": open_id, "name": name, "sheet": sheet, "row": row_number})
    return result


def resolve_mapping(rows, store):
    matches = [row for row in rows if row["store"] == store.strip()]
    if len(matches) != 1:
        raise ValueError(f"店铺 {store!r} 精确匹配到 {len(matches)} 行；必须恰好一行，禁止模糊匹配或取第一行")
    selected = matches[0]
    names = {row["name"] for row in rows if row["open_id"] == selected["open_id"]}
    if len(names) != 1:
        raise ValueError("同一飞书 open_id 对应不同姓名，请核对源表")
    return selected


def read_workbook(path):
    # Only the trusted, locally installed reader is added to the import path.
    # Neither the workbook directory nor the current directory is imported.
    if VENDOR.is_dir():
        sys.path.insert(0, str(VENDOR))
    try:
        import xlrd
    except ImportError as exc:
        raise RuntimeError(f"缺少 xlrd：python -I -m pip install --target \"{VENDOR}\" xlrd==2.0.2") from exc
    path = Path(path)
    raw = path.read_bytes()
    if raw[:8] != bytes.fromhex("d0cf11e0a1b11ae1"):
        raise ValueError("文件不是预期的 XLS/OLE 格式；请核对实际文件类型，不修改后缀碰运气")
    workbook = xlrd.open_workbook(file_contents=raw, on_demand=True)
    try:
        rows = []
        for sheet in workbook.sheets():
            if sheet.nrows == 0:
                continue
            headers = [str(value).strip() for value in sheet.row_values(0)]
            if not any(name in headers for name in REQUIRED_HEADERS):
                continue
            rows.extend(parse_rows(sheet.name, [sheet.row_values(r) for r in range(sheet.nrows)]))
        if not rows:
            raise ValueError("未找到具有完整表头的有效店铺映射")
        if path.read_bytes() != raw:
            raise ValueError("读取期间源表发生变化，请重新读取后再匹配")
        return rows, hashlib.sha256(raw).hexdigest()
    finally:
        workbook.release_resources()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--store", help="紫鸟完整店铺名；只移除两端空白")
    mode.add_argument("--list", action="store_true", help="只读列出全部映射并校验唯一性")
    args = parser.parse_args()
    try:
        rows, digest = read_workbook(args.workbook)
        if args.list:
            for row in rows:
                resolve_mapping(rows, row["store"])
            data = {"count": len(rows), "rows": rows}
        else:
            data = resolve_mapping(rows, args.store)
        print(json.dumps({"ok": True, "workbook": str(args.workbook.resolve()), "sha256": digest, "data": data}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
