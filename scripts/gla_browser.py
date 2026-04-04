#!/usr/bin/env python3
"""
GLA Browser — Selenium Chrome for Google Flow (bypasses bot detection).

Opens Chrome, navigates to Google Flow, keeps the page alive.
User loads the GLA extension manually (persists in profile).

Usage:
    python scripts/gla_browser.py [--refresh-interval 120]
"""

import argparse
import json
import os
import signal
import sys
import time
import urllib.request

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME_PROFILE = os.path.join(PROJECT_ROOT, ".chrome-profile")
FLOW_URL = "https://labs.google/fx/tools/flow"
HEALTH_URL = "http://127.0.0.1:8100/health"
FLOW_STATUS_URL = "http://127.0.0.1:8100/api/flow/status"


def check_status():
    try:
        h = json.loads(urllib.request.urlopen(HEALTH_URL, timeout=2).read())
        f = json.loads(urllib.request.urlopen(FLOW_STATUS_URL, timeout=2).read())
        return {"server": True, "ext": h.get("extension_connected", False), "auth": f.get("flow_key_present", False)}
    except Exception:
        return {"server": False, "ext": False, "auth": False}


def create_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"--user-data-dir={CHROME_PROFILE}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.set_page_load_timeout(300)
    return driver


def run(refresh_interval=120, login_wait=180):
    print("=" * 50)
    print("  GLA Browser — Chrome for Google Flow")
    print("=" * 50)
    print()

    s = check_status()
    print(f"  Server: {'OK' if s['server'] else 'DOWN'}")
    print(f"  Profile: {CHROME_PROFILE}")
    print()

    print("  Launching Chrome...")
    driver = create_driver()

    print(f"  Opening {FLOW_URL}")
    driver.get(FLOW_URL)

    # Wait for login if needed
    time.sleep(5)
    if "accounts.google" in driver.current_url:
        print(f"\n  Google login required — log in now ({login_wait}s timeout)")
        deadline = time.time() + login_wait
        while time.time() < deadline:
            if "labs.google" in driver.current_url:
                print("  Logged in!")
                break
            time.sleep(3)
        else:
            print("  Login timeout — continuing")
    else:
        print("  Already logged in")

    print()
    print("  Load GLA extension manually if not loaded:")
    print("    chrome://extensions → Developer mode → Load unpacked → extension/")
    print()

    # Graceful shutdown
    def stop(sig, frame):
        print("\n  Closing Chrome...")
        try: driver.quit()
        except: pass
        sys.exit(0)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    print(f"  Refreshing every {refresh_interval}s. Ctrl+C to stop.\n")

    cycle = 0
    while True:
        try:
            time.sleep(refresh_interval)
            cycle += 1
            driver.refresh()
            time.sleep(3)
            s = check_status()
            ext = "OK" if s["ext"] else "✗"
            auth = "OK" if s["auth"] else "✗"
            print(f"  [{time.strftime('%H:%M:%S')}] #{cycle} refreshed | ext:{ext} auth:{auth}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"  [ERR] {e}")
            time.sleep(10)

    print("\n  Done.")
    driver.quit()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="GLA Browser")
    p.add_argument("--refresh-interval", type=int, default=120)
    p.add_argument("--login-wait", type=int, default=180)
    a = p.parse_args()
    run(refresh_interval=a.refresh_interval, login_wait=a.login_wait)
