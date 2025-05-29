#!/usr/lib/zabbix/externalscripts/env/bin/python
import argparse
import json
import socket
import ssl
import datetime
import time
import pycurl
import io
import requests
from urllib.parse import urlparse
import httpx
import sys
import re

class WebMonitor:
    def __init__(self, url_or_domain, api_key=None):
        self.url = self.validate_and_format_url(url_or_domain)
        self.domain = urlparse(self.url).netloc
        self.response = None
        self.start_time = None
        self.end_time = None
        self.api_key = api_key

    @staticmethod
    def validate_and_format_url(url_or_domain):
        parsed = urlparse(url_or_domain)
        if not parsed.scheme:
            url_or_domain = "https://" + url_or_domain
        parsed = urlparse(url_or_domain)
        if not all([parsed.scheme, parsed.netloc]):
            raise argparse.ArgumentTypeError("Invalid URL or domain name format")
        return parsed.geturl()

    def fetch_url_once(self):
        try:
            with httpx.Client(http2=True, follow_redirects=True, timeout=10) as client:
                self.start_time = time.time()
                self.response = client.get(self.url)
                self.end_time = time.time()
        except Exception as e:
            print(f"[ERROR] fetch_url_once failed: {repr(e)}", file=sys.stderr)
            self.response = None

    def get_http_status(self):
        return self.response.status_code if self.response else -1

    def get_http_version(self):
        version = self.response.extensions.get("http_version") or self.response.http_version
        return version.decode("utf-8").upper() if isinstance(version, bytes) else version.upper()

    def get_download_speed_kbps(self):
        try:
            size_bits = len(self.response.content) * 8
            duration = self.end_time - self.start_time
            return round((size_bits / duration) / 1024, 2)
        except:
            return -1

    def get_curl_metrics(self):
        buffer = io.BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, self.url)
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.NOPROGRESS, True)
        c.setopt(c.FOLLOWLOCATION, True)
        c.setopt(c.CONNECTTIMEOUT, 10)
        c.setopt(c.TIMEOUT, 20)
        c.perform()

        metrics = {
            'dns_time_ms': round(c.getinfo(pycurl.NAMELOOKUP_TIME) * 1000, 2),
            'tcp_connect_time_ms': round(c.getinfo(pycurl.CONNECT_TIME) * 1000, 2),
            'ssl_handshake_time_ms': round(
                (c.getinfo(pycurl.APPCONNECT_TIME) - c.getinfo(pycurl.CONNECT_TIME)) * 1000, 2
            ),
            'ttfb_ms': round(c.getinfo(pycurl.STARTTRANSFER_TIME) * 1000, 2),
            'http_code': c.getinfo(pycurl.RESPONSE_CODE),
            'total_load_time_ms': round(c.getinfo(pycurl.TOTAL_TIME) * 1000, 2),
            'page_size_bytes': len(buffer.getvalue())
        }

        c.close()
        return metrics

    def get_dns_and_geo(self):
        try:
            ip = socket.gethostbyname(self.domain)
        except:
            return {'ip': 'N/A', 'geo': 'N/A'}

        try:
            geo_data = requests.get(f"http://ip-api.com/json/{ip}", timeout=5).json()
            geo_info = {
                'country': geo_data.get('country'),
                'region': geo_data.get('regionName'),
                'city': geo_data.get('city'),
                'isp': geo_data.get('isp'),
            }
        except:
            geo_info = 'N/A'

        return {'ip': ip, 'geo': geo_info}

    def get_ssl_expiry(self):
        try:
            context = ssl.create_default_context()
            with socket.create_connection((self.domain, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=self.domain) as ssock:
                    cert = ssock.getpeercert()
                    expiry_str = cert['notAfter']
                    expiry_date = datetime.datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                    days_left = (expiry_date - datetime.datetime.now()).days
                    return {
                        'ssl_expiry_date': expiry_date.strftime('%Y-%m-%d'),
                        'days_left': days_left
                    }
        except:
            return {'ssl_expiry_date': 'N/A', 'days_left': 'N/A'}

    def get_pagespeed_insights(self):
        if not self.api_key:
            print("[ERROR] API key is required for PageSpeed Insights.")
            return {}
        strategies = ['desktop', 'mobile']
        results = {}

        def clean(value):
            if not isinstance(value, str):
                return value
            value = value.replace('\u00a0', '').strip().lower()
            try:
                if value.endswith('ms'):
                    return float(value.replace('ms', '').strip())
                elif value.endswith('s'):
                    return float(value.replace('s', '').strip()) * 1000
                else:
                    return float(value)
            except:
                # Special handling for TTFB-like values: "root document took 80ms"
                match = re.search(r'(\d+\.?\d*)\s*ms', value)
                return float(match.group(1)) if match else value

        for strategy in strategies:
            try:
                api_url = (
                    f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
                    f"?url={self.url}&category=PERFORMANCE&category=ACCESSIBILITY"
                    f"&category=BEST_PRACTICES&category=SEO&strategy={strategy}&key={self.api_key}"
                )
                response = requests.get(api_url, timeout=60)
                data = response.json()
                lighthouse = data['lighthouseResult']
                audits = lighthouse['audits']

                metrics = {
                    'performance': lighthouse['categories']['performance']['score'] * 100,
                    'accessibility': lighthouse['categories']['accessibility']['score'] * 100,
                    'bestPractices': lighthouse['categories']['best-practices']['score'] * 100,
                    'seo': lighthouse['categories']['seo']['score'] * 100,
                    'FCP': clean(audits['first-contentful-paint']['displayValue']),
                    'LCP': clean(audits['largest-contentful-paint']['displayValue']),
                    'TBT': clean(audits['total-blocking-time']['displayValue']),
                    'CLS': clean(audits['cumulative-layout-shift']['displayValue']),
                    'SpeedIndex': clean(audits['speed-index']['displayValue']),
                    'TTFB': clean(audits['server-response-time']['displayValue']),
                    'MaxFID': clean(audits.get('max-potential-fid', {}).get('displayValue', 'N/A')),
                    'TTI': clean(audits.get('interactive', {}).get('displayValue', 'N/A')),
                    'NetworkServerLatency': clean(audits.get('network-server-latency', {}).get('displayValue', 'N/A'))
                }

                results[strategy] = metrics
            except Exception as e:
                print(f"[ERROR] PageSpeed {strategy} failed: {e}")
                print(f"URL called: {api_url}")
                if 'response' in locals():
                    print(f"Response: {response.text}")
                results[strategy] = {
                    'performance': -1,
                    'accessibility': -1,
                    'bestPractices': -1,
                    'seo': -1
                }
        return results

    def run_httpx_probe(self):
        self.fetch_url_once()
        if not self.response:
            print("Failed to fetch the URL.")
            return

        result = {
            'url': self.url,
            'http_probe_status': self.get_http_status(),
            'http_version': self.get_http_version(),
            'download_speed_kbps': self.get_download_speed_kbps(),
            'dns_and_geo': self.get_dns_and_geo(),
            'ssl_certificate': self.get_ssl_expiry(),
            'network_metrics': self.get_curl_metrics()
        }
        print(json.dumps(result, indent=4))

    def run_curl_probe(self):
        result = {
            'url': self.url,
            'pagespeed_insights': self.get_pagespeed_insights()
        }
        print(json.dumps(result, indent=4))

def main():
    parser = argparse.ArgumentParser(description="Website Monitoring Tool (Split Modes)")
    parser.add_argument("url_or_domain", help="Website URL or domain")
    parser.add_argument("mode", choices=["site_metrix", "site_seo_web"], default="site_metrix", help="Choose probe mode (httpx or curl)")
    parser.add_argument("--api_key", help="PageSpeed Insights API key (only required for 'site_seo_web')", default=None)
    args = parser.parse_args()

    if args.mode == "site_metrix":
        monitor = WebMonitor(args.url_or_domain)
        monitor.run_httpx_probe()
    elif args.mode == "site_seo_web":
        if not args.api_key:
            print("[ERROR] API key is required for PageSpeed Insights in 'site_seo_web' mode.")
            return
        monitor = WebMonitor(args.url_or_domain, api_key=args.api_key)
        monitor.run_curl_probe()

if __name__ == "__main__":
    main()
