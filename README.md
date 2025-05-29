# Website Performance Monitoring with Zabbix & Grafana

This project provides website performance and availability monitoring using Zabbix external scripts, Google PageSpeed Insights, and a custom Grafana dashboard.

---

## Step 1: Download Required Files

Copy the following Python scripts to the Zabbix `externalscripts` directory:

```bash
sudo cp vu_report_new.py /usr/lib/zabbix/externalscripts/
sudo cp website.py /usr/lib/zabbix/externalscripts/
sudo cp wt.py /usr/lib/zabbix/externalscripts/
```

Make them executable:

```bash
sudo chmod +x /usr/lib/zabbix/externalscripts/*.py
```

---

## Step 2: Install Python Dependencies

Use `requirements.txt` to install required packages:

```bash
pip install -r requirements.txt
```

### `requirements.txt` should contain:

```
selenium
requests
pillow
pycurl
httpx
```

---

## Step 3: Import Zabbix Template

1. Log in to your Zabbix frontend.
2. Navigate to **Configuration > Templates**.
3. Click **Import**.
4. Upload the file:  
   `zbx_export_templates (3).json`
5. Attach the imported template to your Zabbix host.

---

## Step 4: Add Required Macros to Host

Go to your host configuration and add the following macros:

| Macro | Value | Description |
|-------|-------|-------------|
| {$API_KEY} | AlzaSyDxf_9V_-ITsUIQ4-s5uIEPjxQ-SOl2Xt4 | API key for Google PageSpeed Insights |
| {$CERT.EXPIRY.WARN} | 30 | SSL certificate expiry threshold in days |
| {$DNS.QUERY.WARN} | 100 | DNS lookup threshold in ms |
| {$DOWNLOAD.SPEED.WARN} | 100 | Download speed threshold in kbps |
| {$PAGE.LOAD.WARN} | 1000 | Page load time threshold in ms |
| {$SSL.HANDSHAKE.WARN} | 150 | SSL handshake threshold in ms |
| {$TCP.WARN} | 100 | TCP connect threshold in ms |
| {$TTFB.WARN} | 200 | Time To First Byte threshold in ms |
| {$WEB.URL} | App.pssadvantage.com | Domain or site to monitor |
| {$WT.DATA} | `{ "data": [ { "page_name": "login", "url": "https://App.pssadvantage.com" } ] }` | Page list in JSON format |

---

## Step 5: Grafana Setup

### A. Add Zabbix as a Data Source

1. Open Grafana.
2. Go to **Connections > Data Sources**.
3. Click **Add data source**.
4. Select **Zabbix**.
5. Configure:
   - URL: Your Zabbix frontend URL
   - Username/Password: Zabbix credentials
   - Zabbix API: Enabled
6. Click **Save & Test**.

### B. Import Grafana Dashboard

1. Go to **Dashboards > Import**.
2. Upload the file:  
   `Web Monitoring-1748526175925.json`
3. Select the previously added Zabbix data source when prompted.
4. Click **Import**.

---

## Done!

You should now see live website monitoring metrics in both Zabbix and Grafana. You can customize alert thresholds by editing the macros on the host.
