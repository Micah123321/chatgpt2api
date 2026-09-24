"""Browser check using static build + mocked APIs; no real accounts or server calls.
Run after web build: uv run --no-sync --with playwright python test/browser_sub2api_auto_sync.py
Requires installed Google Chrome. Screenshots are saved in a temporary directory.
"""
from __future__ import annotations

import json
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    servers = []
    writes = []
    screenshot_dir = Path(tempfile.mkdtemp(prefix="sub2api-ui-"))
    http = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(ROOT / "web" / "out")))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{http.server_port}"

    def route_api(route):
        path = urlparse(route.request.url).path.rstrip("/")
        payload = None
        if path == "/auth/login":
            payload = {"role": "admin", "subject_id": "test-admin", "name": "test-admin"}
        elif path == "/api/sub2api/servers" or path == "/api/sub2api/servers/test-server":
            if route.request.method == "POST":
                submitted = route.request.post_data_json
                writes.append(dict(submitted))
                defaults = {"id": "test-server", "name": "", "base_url": "", "email": "", "has_api_key": False, "group_id": "", "auto_sync_enabled": False, "auto_sync_time": "03:00", "auto_sync_last_run_at": "", "auto_sync_last_error": "", "import_job": None}
                server = {**(servers[0] if servers else defaults), **submitted}
                server.pop("password", None)
                server.pop("api_key", None)
                servers[:] = [server]
                payload = {"server": server, "servers": servers}
            else:
                payload = {"servers": servers}
        elif path == "/api/settings":
            payload = {"config": {"image_models": ["gpt-image-2.5", "gpt-image-2.5-flare"], "default_image_model": "gpt-image-2.5", "log_levels": [], "sensitive_words": []}}
        elif path == "/api/cpa/pools":
            payload = {"pools": []}
        elif path == "/api/accounts":
            payload = {"items": [], "stats": {"total": 0, "active": 0, "total_quota": 0, "limited": 0, "abnormal": 0, "by_type": {}}}
        elif path == "/api/third-party-apps":
            payload = {"infinite_canvas": {"enabled": False, "url": ""}}
        elif path == "/version":
            payload = {"version": "test"}
        if payload is None:
            route.continue_()
        else:
            route.fulfill(status=200, content_type="application/json", body=json.dumps(payload))

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome", headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 960})
            page = context.new_page()
            page.route("**/*", route_api)
            page.goto(origin + "/login/")
            page.get_by_label("密钥", exact=True).fill("browser-test-only")
            page.get_by_role("button", name="登录", exact=True).click()
            page.wait_for_url("**/accounts/**")
            page.goto(origin + "/settings/")
            page.get_by_role("tab", name="Sub2API", exact=True).click()
            page.clock.install()
            page.get_by_role("button", name="添加连接", exact=True).click()
            dialog = page.get_by_role("dialog")
            time_field = dialog.get_by_label("每日时间（北京时间 UTC+8）", exact=True)
            toggle = dialog.get_by_role("checkbox", name="每日自动导入", exact=True)
            expect(toggle).not_to_be_checked()
            expect(time_field).to_have_value("03:00")
            time_field.fill("")
            expect(dialog.get_by_role("button", name="保存连接", exact=True)).to_be_disabled()
            dialog.get_by_placeholder("例如：自建 sub2api").fill("每日同步测试")
            dialog.get_by_placeholder("http://your-sub2api-host:8080").fill("https://sub2api.invalid")
            dialog.get_by_placeholder("admin@example.com").fill("admin@example.test")
            dialog.get_by_placeholder("管理员密码", exact=True).fill("test-only")
            dialog.get_by_placeholder("留空则同步所有分组；或填写分组 ID / ungrouped").fill("group-7")
            toggle.check()
            time_field.fill("22:15")
            assert not writes, "Draft settings must not be saved automatically"
            dialog.get_by_role("button", name="保存连接", exact=True).click()
            expect(dialog).not_to_be_visible()
            expect(page.get_by_text("自动导入已开启", exact=True)).to_be_visible()
            expect(page.get_by_text("每天 22:15（北京时间 UTC+8）", exact=True)).to_be_visible()
            assert writes[-1]["auto_sync_enabled"] is True
            assert writes[-1]["auto_sync_time"] == "22:15"
            assert writes[-1]["group_id"] == "group-7"
            servers[0]["auto_sync_last_run_at"] = "2026-09-24T15:15:00+00:00"
            servers[0]["auto_sync_last_error"] = "测试连接故障"
            page.clock.fast_forward(16_000)
            expect(page.get_by_text("最近自动执行错误：测试连接故障", exact=True)).to_be_visible()
            expect(page.get_by_text("最近自动执行：2026/09/24 23:15:00（北京时间）", exact=True)).to_be_visible()
            page.screenshot(path=str(screenshot_dir / "desktop.png"), full_page=True)
            page.get_by_title("编辑", exact=True).click()
            expect(dialog.get_by_role("checkbox", name="每日自动导入", exact=True)).to_be_checked()
            expect(dialog.get_by_label("每日时间（北京时间 UTC+8）", exact=True)).to_have_value("22:15")
            page.set_viewport_size({"width": 390, "height": 844})
            dialog.get_by_role("checkbox", name="每日自动导入", exact=True).uncheck()
            dialog.get_by_label("每日时间（北京时间 UTC+8）", exact=True).fill("04:30")
            save = dialog.get_by_role("button", name="保存修改", exact=True)
            save.scroll_into_view_if_needed()
            expect(save).to_be_visible()
            page.screenshot(path=str(screenshot_dir / "mobile-edit.png"), full_page=True)
            save.click()
            expect(dialog).not_to_be_visible()
            assert writes[-1]["auto_sync_enabled"] is False
            assert writes[-1]["auto_sync_time"] == "04:30"
            assert "password" not in writes[-1], "Schedule editing must preserve existing credentials"
            page.reload()
            page.get_by_role("tab", name="Sub2API", exact=True).click()
            expect(page.get_by_text("自动导入已关闭", exact=True)).to_be_visible()
            expect(page.get_by_text("每天 04:30（北京时间 UTC+8）", exact=True)).to_be_visible()
            browser.close()
        print("PASS: defaults, empty-time validation, explicit save, group payload, polling, Beijing time, edit, disable, reload, mobile dialog")
        print(f"Screenshots: {screenshot_dir}")
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    main()
