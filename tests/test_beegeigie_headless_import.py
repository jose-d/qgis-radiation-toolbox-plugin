import glob
import math
import os
import unittest
from datetime import datetime


LOG_GLOB = os.environ.get(
    "BEEGEIGIE_LOG_GLOB",
    "/run/media/jose/ADATA2T/beegeigie/*.LOG",
)


def _haversine_distance(p1, p2):
    """Return approximate WGS84 distance in meters without importing QGIS."""
    lon1, lat1 = map(math.radians, p1)
    lon2, lat2 = map(math.radians, p2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 6371008.8 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class BeeGeigieHeadlessImportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from radiation_toolbox_reader import ComputedAttributes
            from radiation_toolbox_reader.exceptions import ReaderError
            from radiation_toolbox_reader.safecast import SafecastReader
        except ModuleNotFoundError as e:
            try:
                from reader import ComputedAttributes
                from reader.exceptions import ReaderError
                from reader.safecast import SafecastReader
            except ModuleNotFoundError:
                raise unittest.SkipTest(
                    "radiation_toolbox_reader is not installed"
                ) from e

        SafecastReader._distance = staticmethod(_haversine_distance)
        cls.ComputedAttributes = ComputedAttributes
        cls.ReaderError = ReaderError
        cls.SafecastReader = SafecastReader

    def test_imports_all_mounted_beegeigie_logs_without_qgis(self):
        paths = sorted(glob.glob(LOG_GLOB))
        if not paths:
            raise unittest.SkipTest(f"No LOG files matched {LOG_GLOB}")

        failures = []
        summaries = []
        for path in paths:
            try:
                summary = self._import_summary(path)
            except self.ReaderError as e:
                if self._has_data_records(path):
                    failures.append(f"{path}: {type(e).__name__}: {e}")
                else:
                    summaries.append({
                        "path": path,
                        "records": 0,
                        "imported": 0,
                        "skipped": 0,
                        "rejected": True,
                    })
            except Exception as e:
                failures.append(f"{path}: {type(e).__name__}: {e}")
            else:
                summaries.append(summary)

        if failures:
            self.fail(
                "Headless BeeGeigie import failed for "
                f"{len(failures)} of {len(paths)} files:\n" + "\n".join(failures)
            )

        empty = [
            item["path"] for item in summaries
            if item["imported"] == 0 and not item.get("rejected")
        ]
        self.assertFalse(empty, "No importable records found in: " + ", ".join(empty))

    def _import_summary(self, path):
        reader = self.SafecastReader(
            path,
            computed_attributes=self.ComputedAttributes.All,
        )
        try:
            metadata = reader.metadata
            self.assertIn("format_version", metadata)
            self.assertIn("deadtime", metadata)
            self.assertNotIn("columns", metadata)

            imported = 0
            skipped = 0
            for record in reader:
                if self._record_is_importable(record):
                    imported += 1
                else:
                    skipped += 1

                for name in (
                    "ader_microsvh",
                    "time_local",
                    "speed_kmph",
                    "dose_increment",
                    "time_cumulative",
                    "dose_cumulative",
                    "dist_cumulative",
                ):
                    self.assertIn(name, record)

            stats = reader.stats()
            self.assertEqual(stats["count"], imported + skipped)
            return {
                "path": path,
                "records": stats["count"],
                "imported": imported,
                "skipped": skipped,
            }
        finally:
            reader.release()

    @staticmethod
    def _record_is_importable(record):
        if int(record["hdop"]) == 9999:
            return False
        if int(record["sat"]) < 3:
            return False
        try:
            datetime.strptime(record["date_time"].split("T", 1)[1], "%H:%M:%SZ")
        except ValueError:
            return False

        x, y = record.point
        return abs(x) >= sys_float_epsilon() and abs(y) >= sys_float_epsilon()

    @staticmethod
    def _has_data_records(path):
        with open(path, encoding="utf-8") as fd:
            return any(line.startswith("$") for line in fd)


def sys_float_epsilon():
    return float.fromhex("0x1.0000000000000p-52")
