#!/usr/lib/zabbix/externalscripts/env/bin/python
## ---------- INSTALLATION ---------- ##
# apt install python3 python3-venv
# python3 -m venv env
# source env/bin/activate
# pip install selenium
# pip install requests
# change #!env/bin/python to pwd/env/bin/python
# chmod +x ./wt.py
# wt.py https://www.google.com/


## --------- GLOBAL VARIABLES --------- ##

# SELENIUM HOST
# MUST BE ON "http://ip:port". Ex. SELENIUM_HOST = "http://127.0.0.1:4444"
# SELENIUM_HOST = "http://localhost:4444"
SELENIUM_HOST = "http://192.168.50.8:4444"

# SELENIUM TIMEOUT
# MUST BE INT (SECONDS) Ex. SELENIUM_TIMEOUT = 15
SELENIUM_TIMEOUT = 15

# REQUEST TIMEOUT
# MUST BE INT (SECONDS) Ex. REQUEST_TIMEOUT = 15
REQUEST_TIMEOUT = 15

## ------------------------------------ ##

import base64
from PIL import Image

import json

import io

import time
import socket
import requests
import argparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from requests.exceptions import Timeout, ConnectionError


# {"dns_time":"<output>","response_time":"<output>","load_time":"<output>","img":"<base64>"}

class web_transation:
    def __init__(self, url):
        self.url = url

    def result(self):
        result = {}
        get_data = self.get_base64_screenshot()

        dns_time = round(self.measure_dns_time(), 7)
        response_time = round(self.measuere_responce_time(), 7)
        load_time = round(get_data[0], 7)
        status = self.get_status_code(self.url)
        img = get_data[1]
        quot = '"'


        # json_str = ("{" + f"{quot}status{quot}:{quot}{str(status["status"])}{quot},{quot}statusCode{quot}:{quot}{str(status["code"])}{quot},{quot}dns_time{quot}:{quot}{dns_time}{quot},{quot}response_time{quot}:{quot}{response_time}{quot},{quot}load_time{quot}:{quot}{load_time}{quot},{quot}img{quot}:{quot}{img}{quot}" + "}")
        final_data = {
            "status": str(status["status"]),
            "statusCode": str(status["code"]),
            "dns_time": str(dns_time),
            "response_time": str(response_time),
            "load_time": str(load_time),
            "img": img
        }
        return json.dumps(final_data)

    def measure_dns_time(self):
        domain = self.url.replace("http://", "").replace("https://", "").split("/")[0]
        start_time = time.time()
        socket.gethostbyname(domain)
        end_time = time.time()
        return end_time - start_time

    def measuere_responce_time(self):
        start_time = time.time()
        try:
            response = requests.get(self.url, timeout=REQUEST_TIMEOUT)
            response.status_code
        except Exception as e:
            pass
        return time.time() - start_time

    def _take_ss(self, driver):
        # Take screenshot
        screenshot = driver.get_screenshot_as_png()
        # Open image with Pillow
        image = Image.open(io.BytesIO(screenshot))
        # Resize image to reduce dimensions (e.g., 50% reduction)
        width, height = image.size
        new_size = (int(width * 0.4), int(height * 0.4))
        image = image.resize(new_size, Image.LANCZOS)
        # Save to buffer in JPEG format without additional compression
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=50)  # Set quality to 50 for minimal compression
        # Encode image to base64
        compressed_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return compressed_image

    def get_base64_screenshot(self):
        start_time = time.time()
        """
        Takes a URL, captures a full-page screenshot, and returns it as a Base64 encoded string.

        Args:
            url (str): The URL of the page to capture.
            app_config (dict): Configuration settings containing Selenium grid host and timeout.
            selenium_timeout (int): Timeout for Selenium operations.

        Returns:
            str: The Base64 encoded string of the screenshot or None if an error occurs.
        """

        chrome_options = Options()
        chrome_options.add_argument("--disable-extensions")  # Disable extensions
        chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
        chrome_options.add_argument("--disable-infobars")  # Disable infobars
        chrome_options.add_argument("--no-sandbox")  # Disable sandbox mode
        chrome_options.add_argument("--start-maximized")  # Start maximized
        chrome_options.add_argument("--force-device-scale-factor=1")  # forcing to scale 100%
        chrome_options.add_argument("--incognito")  # Start in incognito mode
        chrome_options.add_argument("--window-size=1024,768")

        # Clear cache and cookies
        chrome_options.add_argument("--disable-application-cache")  # Disable application cache
        chrome_options.add_argument("--disable-cache")  # Disable browser cache
        chrome_options.add_argument("--disable-session-crashed-bubble")  # Disable session crashed bubble
        chrome_options.add_argument("--disable-restore-session-state")  # Disable session restore state
        chrome_options.add_argument("--disable-restore-background-contents")  # Disable restoring background contents
        chrome_options.add_argument("--delete-cookies")  # Delete cookies
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging']) # stoping chrome to generate console output
        chrome_options.add_experimental_option("detach", True) # stoping chrome to automatically close


        driver = webdriver.Remote(command_executor=f'{SELENIUM_HOST}/wd/hub', options=chrome_options)
        wait = WebDriverWait(driver, SELENIUM_TIMEOUT)

        try:
            driver.get(self.url)
            wait.until(EC.presence_of_element_located(By.TAG_NAME, "body"))
            time.sleep(4)  # Small delay to ensure page elements are rendered
        except Exception as e:
            # print(f"Error capturing screenshot: {e}")
            pass
        finally:
            # time.sleep(4)
            screenshot_base64 = self._take_ss(driver)
            load_time = time.time() - start_time
            driver.quit()

        return load_time, screenshot_base64

    def get_status_code(self, url, timeout=15):
        # Ensure the URL starts with http:// or https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url  # Default to https

        try:
            response = requests.get(url, timeout=timeout)
            status_code = response.status_code
            status_code = int(status_code)
        except Timeout:
            status_code = 408  # Timeout occurred
        except ConnectionError:
            status_code = 503  # Server connection issue
        except Exception:
            status_code = 500  # Any other issue occurred

        # Managing status code
        status_code = int(status_code)  # Convert to integer
        if status_code < 400 or status_code > 600:
            status_code = 200
        elif status_code in [403]:
            status_code = 200

        if status_code >= 200 and status_code < 400:
            s_id = 1  # Status ID indicating success
        else:
            s_id = 0  # Status ID indicating failure

        return {"code": status_code, "status": s_id}

if __name__ == "__main__":

    # Argument Parsing
    parser = argparse.ArgumentParser(description="Capture a base64 encoded screenshot of a webpage.")
    parser.add_argument("url", help="The URL of the webpage to capture.")
    args = parser.parse_args()

    wt = web_transation(args.url)
    print(wt.result())
