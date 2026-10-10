import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))

from refresh import last_ok_run_is_recent

NOW = datetime.datetime.fromisoformat("2026-10-09T20:00:00+01:00")


def test_no_previous_run_is_not_recent() -> None:
    assert last_ok_run_is_recent(None, NOW) is False


def test_ok_run_one_hour_ago_is_recent() -> None:
    status = {"ok": True, "finished_at": "2026-10-09T19:00:00+01:00"}
    assert last_ok_run_is_recent(status, NOW) is True


def test_ok_run_three_hours_ago_is_not_recent() -> None:
    status = {"ok": True, "finished_at": "2026-10-09T17:00:00+01:00"}
    assert last_ok_run_is_recent(status, NOW) is False


def test_failed_run_never_counts_as_recent() -> None:
    status = {"ok": False, "finished_at": "2026-10-09T19:59:00+01:00"}
    assert last_ok_run_is_recent(status, NOW) is False


def test_recent_across_clock_change() -> None:
    # Finished 01:30 BST, now 01:15 GMT: 45 real minutes later, still recent.
    status = {"ok": True, "finished_at": "2026-10-25T01:30:00+01:00"}
    now = datetime.datetime.fromisoformat("2026-10-25T01:15:00+00:00")
    assert last_ok_run_is_recent(status, now) is True
