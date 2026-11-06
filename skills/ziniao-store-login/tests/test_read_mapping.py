"""Offline checks: catch wrong-recipient matches and incomplete mappings."""
import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "read_mapping.py"


def load_module():
    if not SCRIPT.exists():
        return None
    spec = importlib.util.spec_from_file_location("read_mapping", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.mapping = load_module()
        self.assertIsNotNone(self.mapping, "read-only mapping helper is not implemented")
        self.headers = ["机器名称", "员工UserID", "姓名"]

    def parse(self, rows):
        return self.mapping.parse_rows("Sheet1", [self.headers, *rows])

    def test_exact_shop_name_keeps_new_vc_and_po_distinct(self):
        rows = self.parse([
            ["0号机欧洲-新", "ou_person1", "甲"],
            ["VC账户7号机", "ou_person2", "乙"],
            ["VC账户7号机-PO", "ou_person3", "丙"],
        ])
        self.assertEqual(self.mapping.resolve_mapping(rows, "VC账户7号机-PO")["open_id"], "ou_person3")
        with self.assertRaises(ValueError):
            self.mapping.resolve_mapping(rows, "0号机欧洲")
        with self.assertRaises(ValueError):
            self.mapping.resolve_mapping(rows, "7号机")

    def test_duplicate_shop_cannot_pick_first_person(self):
        rows = self.parse([["1号机美国", "ou_a", "甲"], ["1号机美国", "ou_b", "乙"]])
        with self.assertRaises(ValueError):
            self.mapping.resolve_mapping(rows, "1号机美国")

    def test_blank_required_cell_and_wrong_id_stop_lookup(self):
        for row in (["1号机美国", "", "甲"], ["1号机美国", "user_123", "甲"], ["1号机美国", "ou_a", ""]):
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.parse([row])

    def test_headers_are_required_and_unambiguous(self):
        for header in (["店铺", "员工UserID", "姓名"], ["机器名称", "员工UserID", "姓名", "员工UserID"]):
            with self.subTest(header=header), self.assertRaises(ValueError):
                self.mapping.parse_rows("Sheet1", [header, ["1号机美国", "ou_a", "甲"]])

    def test_trims_edges_skips_empty_rows_and_keeps_source_row(self):
        rows = self.parse([["", "", ""], [" 1号机美国 ", " ou_a ", " 甲 "]])
        result = self.mapping.resolve_mapping(rows, "1号机美国")
        self.assertEqual(result, {"store": "1号机美国", "open_id": "ou_a", "name": "甲", "sheet": "Sheet1", "row": 3})

    def test_conflicting_name_for_same_open_id_is_rejected(self):
        rows = self.parse([["1号机美国", "ou_a", "甲"], ["2号机美国", "ou_a", "乙"]])
        with self.assertRaises(ValueError):
            self.mapping.resolve_mapping(rows, "1号机美国")

    def test_workbook_can_be_read_without_changes(self):
        path = pathlib.Path(r"D:\共享\验证码请求飞书.xls")
        if not path.exists():
            self.skipTest("User workbook is not present on this machine")
        before = path.read_bytes()
        rows, digest = self.mapping.read_workbook(path)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(len(digest), 64)
        self.assertGreater(len(rows), 0)
        # The workbook stays authoritative when the user changes assignments.
        # Do not snapshot today's people or record count into a permanent test.
        for row in rows:
            self.assertEqual(self.mapping.resolve_mapping(rows, row["store"]), row)


if __name__ == "__main__":
    unittest.main()
