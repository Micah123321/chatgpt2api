from __future__ import annotations

import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.accounts as accounts_api
from services import sub2api_service as sub2api
from services.account_service import AccountService
from services.storage.json_storage import JSONStorageBackend


class Sub2APIAutoSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "sub2api.json"
        self.store = sub2api.Sub2APIConfig(self.path)
        self.server = self.store.add_server(
            name="test", base_url="https://sub2api.invalid", email="", password="",
            api_key="test-key", group_id="group-7", auto_sync_enabled=True,
            auto_sync_time="03:00",
        )
        self.server_id = self.server["id"]
        self.service = sub2api.Sub2APIImportService(self.store)
        self.due = datetime(2026, 9, 24, 3, 0, tzinfo=sub2api.SYNC_TIMEZONE)

    def test_legacy_configuration_defaults_to_disabled(self):
        self.path.write_text(json.dumps([{"id": "old", "base_url": "https://example.invalid"}]))
        server = sub2api.Sub2APIConfig(self.path).get_server("old")
        self.assertFalse(server["auto_sync_enabled"])
        self.assertEqual(server["auto_sync_time"], "03:00")
        self.assertEqual(server["auto_sync_last_run_at"], "")

    def test_time_boundary_and_restart_do_not_repeat_same_day(self):
        with mock.patch.object(self.service, "_launch_import") as launch:
            self.service.run_due_imports(self.due.replace(hour=2, minute=59))
            launch.assert_not_called()
            self.service.run_due_imports(self.due)
            launch.assert_called_once()
            saved, ids = launch.call_args.args
            self.assertEqual(saved["group_id"], "group-7")
            self.assertIsNone(ids)
            self.service.run_due_imports(self.due.replace(hour=5))
            self.assertEqual(launch.call_count, 1)
        restarted = sub2api.Sub2APIImportService(sub2api.Sub2APIConfig(self.path))
        with mock.patch.object(restarted, "_launch_import") as launch:
            restarted.run_due_imports(self.due.replace(hour=6))
            launch.assert_not_called()
            restarted.run_due_imports(self.due.replace(day=25))
            launch.assert_called_once()

    def test_utc_clock_is_converted_to_beijing(self):
        with mock.patch.object(self.service, "_launch_import") as launch:
            self.service.run_due_imports(datetime(2026, 9, 23, 18, 59, tzinfo=timezone.utc))
            launch.assert_not_called()
            self.service.run_due_imports(datetime(2026, 9, 23, 19, 0, tzinfo=timezone.utc))
            launch.assert_called_once()

    def test_disabled_and_invalid_times_are_not_scheduled(self):
        for updates in ({"auto_sync_enabled": False}, {"auto_sync_enabled": True, "auto_sync_time": "24:00"}):
            self.store.update_server(self.server_id, updates)
            with mock.patch.object(self.service, "_launch_import") as launch:
                self.service.run_due_imports(self.due.replace(hour=23))
                launch.assert_not_called()

    def test_running_manual_import_blocks_schedule_without_consuming_date(self):
        with mock.patch.object(self.service, "_launch_import") as launch:
            self.service.start_import(self.server, ["1"])
            self.service.run_due_imports(self.due)
            self.assertEqual(launch.call_count, 1)
            self.assertEqual(self.store.get_server(self.server_id)["auto_sync_last_run_at"], "")
            with self.assertRaises(ValueError):
                self.service.start_import(self.server, ["2"])
            self.service._update_job(self.server_id, status="completed")
            self.service.run_due_imports(self.due)
            self.assertEqual(launch.call_count, 2)

    def test_editing_connection_preserves_running_job(self):
        self.store.begin_import(self.server_id, self.service._new_job(1))
        self.service._update_job(self.server_id, status="running")
        self.store.update_server(self.server_id, {"auto_sync_time": "04:00"})
        self.assertEqual(self.store.get_import_job(self.server_id)["status"], "running")
        reloaded = sub2api.Sub2APIConfig(self.path)
        self.assertEqual(reloaded.get_server(self.server_id)["auto_sync_time"], "04:00")
        self.assertEqual(reloaded.get_import_job(self.server_id)["status"], "failed")

    def test_concurrent_scheduler_checks_claim_only_once(self):
        with mock.patch.object(self.service, "_launch_import") as launch:
            with ThreadPoolExecutor(max_workers=4) as executor:
                list(executor.map(lambda _: self.service.run_due_imports(self.due), range(8)))
            launch.assert_called_once()

    def run_inline(self, now=None):
        with mock.patch.object(self.service, "_launch_import", side_effect=self.service._execute_import):
            self.service.run_due_imports(now or self.due)

    def test_daily_import_reuses_group_and_skips_existing_tokens(self):
        account_store = AccountService(JSONStorageBackend(Path(self.temp.name) / "accounts.json"))
        with (
            mock.patch.object(sub2api, "list_remote_accounts", return_value=[{"id": "1"}, {"id": "1"}, {"id": "2"}]) as listing,
            mock.patch.object(sub2api, "_fetch_access_tokens_for_accounts", return_value=(["fake-token-1", "fake-token-2"], [])) as fetch,
            mock.patch.object(sub2api, "account_service", account_store),
            mock.patch.object(account_store, "refresh_accounts", return_value={"refreshed": 2, "errors": []}),
        ):
            self.run_inline()
            self.assertEqual(listing.call_args.args[0]["group_id"], "group-7")
            self.assertEqual(fetch.call_args.args[1], ["1", "2"])
            self.assertEqual(self.store.get_import_job(self.server_id)["added"], 2)
            self.run_inline(self.due.replace(day=25))
            job = self.store.get_import_job(self.server_id)
            self.assertEqual(job["added"], 0)
            self.assertEqual(job["skipped"], 2)
            self.assertEqual(job["status"], "completed")
            self.assertEqual(len(account_store.list_accounts()), 2)

    def test_empty_remote_list_completes_without_export(self):
        with (
            mock.patch.object(sub2api, "list_remote_accounts", return_value=[]),
            mock.patch.object(sub2api, "_fetch_access_tokens_for_accounts") as fetch,
        ):
            self.run_inline()
            fetch.assert_not_called()
            self.assertEqual(self.store.get_import_job(self.server_id)["status"], "completed")
            self.assertEqual(self.store.get_import_job(self.server_id)["total"], 0)

    def test_remote_failure_is_saved_without_exposing_response_or_retrying(self):
        with mock.patch.object(sub2api, "list_remote_accounts", side_effect=RuntimeError("secret-response")) as listing:
            self.run_inline()
            self.run_inline(self.due.replace(hour=6))
            listing.assert_called_once()
        server = sub2api.Sub2APIConfig(self.path).get_server(self.server_id)
        self.assertEqual(server["import_job"]["status"], "failed")
        self.assertIn("RuntimeError", server["auto_sync_last_error"])
        self.assertNotIn("secret-response", json.dumps(server))

    def test_export_and_refresh_failures_finish_job(self):
        for target in ("export", "refresh"):
            with self.subTest(target=target):
                self.store.update_server(self.server_id, {"auto_sync_last_run_at": ""})
                with (
                    mock.patch.object(sub2api, "list_remote_accounts", return_value=[{"id": "1"}]),
                    mock.patch.object(sub2api, "_fetch_access_tokens_for_accounts", return_value=(["fake-token"], []), side_effect=RuntimeError("private") if target == "export" else None),
                    mock.patch.object(sub2api.account_service, "add_accounts", return_value={"added": 1}),
                    mock.patch.object(sub2api.account_service, "refresh_accounts", side_effect=RuntimeError("private")),
                ):
                    self.run_inline()
                server = self.store.get_server(self.server_id)
                self.assertEqual(server["import_job"]["status"], "failed")
                self.assertTrue(server["auto_sync_last_error"])

    def test_large_selection_is_exported_in_bounded_batches(self):
        with (
            mock.patch.object(sub2api, "list_remote_accounts", return_value=[{"id": str(i)} for i in range(205)]),
            mock.patch.object(sub2api, "_fetch_access_tokens_for_accounts", return_value=(["fake-token"], [])) as fetch,
            mock.patch.object(sub2api.account_service, "add_accounts", return_value={"added": 1}) as add,
            mock.patch.object(sub2api.account_service, "refresh_accounts", return_value={"refreshed": 1}),
        ):
            self.run_inline()
            self.assertEqual([len(call.args[1]) for call in fetch.call_args_list], [100, 100, 5])
            add.assert_called_once_with(["fake-token"], source_type="codex")

    def test_failed_claim_save_does_not_leave_pending_job(self):
        with (
            mock.patch.object(self.store, "_save", side_effect=OSError("disk unavailable")),
            mock.patch.object(self.service, "_launch_import") as launch,
        ):
            self.service.run_due_imports(self.due)
            launch.assert_not_called()
            self.assertIsNone(self.store.get_import_job(self.server_id))
            self.assertEqual(self.store.get_server(self.server_id)["auto_sync_last_run_at"], "")
        with mock.patch.object(self.service, "_launch_import") as launch:
            self.service.run_due_imports(self.due)
            launch.assert_called_once()

    def test_storage_failure_during_worker_does_not_leave_running_job(self):
        saved = self.store.begin_import(self.server_id, self.service._new_job(), scheduled_at=self.due)
        with mock.patch.object(self.store, "_save", side_effect=OSError("disk unavailable")):
            self.service._execute_import(saved, None)
        self.assertEqual(self.store.get_import_job(self.server_id)["status"], "failed")

    def test_scheduler_stops_with_application_event(self):
        stop = threading.Event()
        with mock.patch.object(self.service, "run_due_imports", side_effect=stop.set) as run:
            thread = self.service.start_scheduler(stop)
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            run.assert_called_once()

    def test_api_saves_schedule_and_rejects_invalid_time(self):
        app = FastAPI()
        app.include_router(accounts_api.create_router())
        with (
            mock.patch.object(accounts_api, "sub2api_config", self.store),
            mock.patch.object(accounts_api, "require_admin", return_value={"role": "admin"}),
            TestClient(app) as client,
        ):
            payload = {"base_url": "https://example.invalid", "api_key": "dummy-key", "auto_sync_enabled": True, "auto_sync_time": "22:15"}
            response = client.post("/api/sub2api/servers", json=payload)
            self.assertEqual(response.status_code, 200)
            server = response.json()["server"]
            self.assertEqual(server["auto_sync_time"], "22:15")
            self.assertTrue(server["auto_sync_enabled"])
            self.assertNotIn("api_key", server)
            self.assertNotIn("password", server)
            url = f"/api/sub2api/servers/{server['id']}"
            for invalid in ("25:00", "3:00", "03:60", "", "03:00:00"):
                self.assertEqual(client.post(url, json={"auto_sync_time": invalid}).status_code, 422)
            self.assertEqual(client.post(url, json={"auto_sync_enabled": False}).status_code, 200)
            saved = sub2api.Sub2APIConfig(self.path).get_server(server["id"])
            self.assertFalse(saved["auto_sync_enabled"])
            self.assertEqual(saved["auto_sync_time"], "22:15")

    def test_schedule_endpoints_require_admin(self):
        app = FastAPI()
        app.include_router(accounts_api.create_router())
        with TestClient(app) as client:
            response = client.post(f"/api/sub2api/servers/{self.server_id}", json={"auto_sync_enabled": True})
            self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
