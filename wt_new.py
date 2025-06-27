#!/usr/lib/zabbix/externalscripts/env/bin/python

# ---------- REQUIREMENTS ----------
# pip install selenium requests pillow
# Make executable: chmod +x wt_new.py
# Place in /usr/lib/zabbix/externalscripts/
# Zabbix key: wt_new.py["https://google.com", "{$SELENIUM_HOSTS}"]

import base64
from PIL import Image
import json
import io
import time
import socket
import requests
import argparse
import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from requests.exceptions import Timeout, ConnectionError

SELENIUM_TIMEOUT = 15
REQUEST_TIMEOUT = 10

class WebTransaction:
    def __init__(self, url, selenium_host):
        self.url = url
        self.selenium_host = selenium_host

    def measure_dns_time(self):
        domain = self.url.replace("http://", "").replace("https://", "").split("/")[0]
        start = time.time()
        socket.gethostbyname(domain)
        return time.time() - start

    def measure_response_time(self):
        start = time.time()
        try:
            requests.get(self.url, timeout=REQUEST_TIMEOUT)
        except Exception:
            pass
        return time.time() - start

    def get_status_code(self):
        try:
            response = requests.get(self.url, timeout=REQUEST_TIMEOUT)
            status_code = int(response.status_code)
        except Timeout:
            status_code = 408
        except ConnectionError:
            status_code = 503
        except Exception:
            status_code = 500

        if status_code < 100 or status_code > 599:
            status_code = 200
        elif status_code == 403:
            status_code = 200

        status = 1 if 200 <= status_code < 400 else 0
        return {"code": status_code, "status": status}

    def _take_screenshot_base64(self, driver):
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        width, height = image.size
        new_size = (int(width * 0.4), int(height * 0.4))
        image = image.resize(new_size, Image.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=50)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def get_screenshot_and_load_time(self):
        start = time.time()

        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1024,768")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        chrome_options.page_load_strategy = 'eager'

        driver = webdriver.Remote(command_executor=f"{self.selenium_host}/wd/hub", options=chrome_options)
        wait = WebDriverWait(driver, SELENIUM_TIMEOUT)

        try:
            driver.get(self.url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)  # let it settle
        except Exception:
            pass
        finally:
            img = self._take_screenshot_base64(driver)
            load_time = time.time() - start
            driver.quit()

        return load_time, img

    def result(self):
        dns_time = round(self.measure_dns_time(), 6)
        response_time = round(self.measure_response_time(), 6)
        status_info = self.get_status_code()
        load_time, image = self.get_screenshot_and_load_time()

        result = {
            "status": str(status_info["status"]),
            "statusCode": str(status_info["code"]),
            "dns_time": str(dns_time),
            "response_time": str(response_time),
            "load_time": str(round(load_time, 6)),
            "img": image
        }
        return json.dumps(result)

def get_working_selenium_host(host_list):
    for host in host_list:
        try:
            resp = requests.get(f"{host}/status", timeout=2)
            if resp.status_code == 200 and resp.json().get("value", {}).get("ready", False):
                return host
        except Exception:
            continue
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web transaction monitor")
    parser.add_argument("url", help="Website URL to monitor")
    parser.add_argument("selenium_hosts", help="Comma-separated list of Selenium hosts")
    args = parser.parse_args()

    host_list = [x.strip() for x in args.selenium_hosts.split(",")]
    working_host = get_working_selenium_host(host_list)

    if not working_host:
        print(json.dumps({"error": "No working Selenium host found"}))
        sys.exit(1)

    wt = WebTransaction(args.url, working_host)
    print(wt.result())
