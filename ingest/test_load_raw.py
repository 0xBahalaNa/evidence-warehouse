"""Landing-file stem must match each finding row's source field."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
LOADER = ROOT / "ingest" / "load_raw.py"
FIXTURES = ROOT / "fixtures"


def _run(raw_dir: Path, db_path: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["EVIDENCE_DB_PATH"] = str(db_path)
    return subprocess.run(
        [sys.executable, str(LOADER), "--raw-dir", str(raw_dir)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


def _copy_fixtures(dest: Path) -> None:
    dest.mkdir()
    for path in FIXTURES.glob("*.json"):
        shutil.copy(path, dest / path.name)


class LoadManifestSourceTests(unittest.TestCase):
    def test_renamed_fixture_exits_naming_stem_and_row_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = root / "good"
            renamed = root / "renamed"
            db = root / "warehouse.duckdb"
            _copy_fixtures(good)
            seeded = _run(good, db)
            self.assertEqual(seeded.returncode, 0, seeded.stderr)

            _copy_fixtures(renamed)
            landed = renamed / "s3audit.json"
            (renamed / "s3_audit.json").rename(landed)

            result = _run(renamed, db)

            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                result.stderr.strip(),
                f"{landed}: row source 's3_audit' does not match "
                f"file stem 's3audit' at index 0",
            )
            self.assertEqual(result.stdout, "")

            con = duckdb.connect(str(db), read_only=True)
            try:
                tables = con.execute(
                    "select table_name from information_schema.tables "
                    "where table_schema = 'raw' order by 1"
                ).fetchall()
                manifest = con.execute(
                    "select source, row_count from raw.load_manifest order by source"
                ).fetchall()
                row_source = con.execute(
                    'select distinct "source" from raw.s3_audit'
                ).fetchall()
            finally:
                con.close()

            self.assertEqual(
                tables,
                [
                    ("cloudtrail_audit",),
                    ("evidence_logger",),
                    ("load_manifest",),
                    ("s3_audit",),
                    ("sg_audit",),
                ],
            )
            self.assertEqual(
                manifest,
                [
                    ("cloudtrail_audit", 6),
                    ("evidence_logger", 3),
                    ("s3_audit", 3),
                    ("sg_audit", 4),
                ],
            )
            self.assertEqual(row_source, [("s3_audit",)])

    def test_later_row_disagreement_names_that_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            landing = root / "raw"
            landing.mkdir()
            landed = landing / "s3_audit.json"
            landed.write_text(
                json.dumps(
                    [
                        {"source": "s3_audit", "check_id": "first"},
                        {"source": "other", "check_id": "second"},
                    ]
                ),
                encoding="utf-8",
            )
            result = _run(landing, root / "warehouse.duckdb")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                result.stderr.strip(),
                f"{landed}: row source 'other' does not match "
                f"file stem 's3_audit' at index 1",
            )

    def test_missing_source_names_both(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            landing = root / "raw"
            landing.mkdir()
            landed = landing / "s3_audit.json"
            landed.write_text(json.dumps([{"check_id": "x"}]), encoding="utf-8")
            result = _run(landing, root / "warehouse.duckdb")
            self.assertEqual(result.returncode, 1)
            self.assertEqual(
                result.stderr.strip(),
                f"{landed}: row source None does not match "
                f"file stem 's3_audit' at index 0",
            )

    def test_empty_array_keeps_stem_as_manifest_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            landing = root / "raw"
            landing.mkdir()
            (landing / "s3_audit.json").write_text("[]", encoding="utf-8")
            db = root / "warehouse.duckdb"
            result = _run(landing, db)
            self.assertEqual(result.returncode, 0, result.stderr)
            con = duckdb.connect(str(db), read_only=True)
            try:
                manifest = con.execute(
                    "select source, row_count from raw.load_manifest"
                ).fetchall()
                tables = con.execute(
                    "select table_name from information_schema.tables "
                    "where table_schema = 'raw' order by 1"
                ).fetchall()
            finally:
                con.close()
            self.assertEqual(manifest, [("s3_audit", 0)])
            self.assertEqual(tables, [("load_manifest",)])

    def test_matching_fixtures_record_stem_as_manifest_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            landing = root / "raw"
            db = root / "warehouse.duckdb"
            _copy_fixtures(landing)
            result = _run(landing, db)
            self.assertEqual(result.returncode, 0, result.stderr)
            con = duckdb.connect(str(db), read_only=True)
            try:
                manifest = con.execute(
                    "select source, row_count from raw.load_manifest order by source"
                ).fetchall()
            finally:
                con.close()
            self.assertEqual(
                manifest,
                [
                    ("cloudtrail_audit", 6),
                    ("evidence_logger", 3),
                    ("s3_audit", 3),
                    ("sg_audit", 4),
                ],
            )


if __name__ == "__main__":
    unittest.main()
