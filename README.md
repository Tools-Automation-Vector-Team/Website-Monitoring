# Website-Monitoring
Repository for Website Monitoring 
Zabbix Web Monitoring with PageSpeed, Load Metrics & Visual Dashboard
This project includes 3 external scripts integrated with Zabbix for enhanced web monitoring and alerting. It also provides macros, template import, and a Grafana dashboard for visualization.

Project Files
Place the following Python scripts into the Zabbix externalscripts directory:

bash
Copy
Edit
sudo cp vu_report_new.py website.py wt.py /usr/lib/zabbix/externalscripts/
sudo chmod +x /usr/lib/zabbix/externalscripts/*.py
Install Python Dependencies
Install all dependencies using requirements.txt:

bash
Copy
Edit
pip install -r requirements.txt
Content of requirements.txt:

text
Copy
Edit
selenium>=4.0.0
requests>=2.25.0
pillow>=8.0.0
pycurl>=7.45.0
httpx>=0.21.0
Import Zabbix Template
Login to Zabbix frontend.

Navigate to: Configuration → Templates → Import

Import file: zbx_export_templates (3).json

Link Template to Host
Go to: Configuration → Hosts

Choose your target host.

Under Templates, click Link new templates

Select the imported template and save.

Configure Zabbix Macros
Set the following macros for your host:

Macro	Value
{$API_KEY}	AIzaSyDXf_9V_-ITsUIQ4-s5uIEPjxQ-SOl2Xt4
{$CERT.EXPIRY.WARN}	30
{$DNS.QUERY.WARN}	100
{$DOWNLOAD.SPEED.WARN}	100
{$PAGE.LOAD.WARN}	1000
{$SSL.HANDSHAKE.WARN}	150
{$TCP.WARN}	100
{$TTFB.WARN}	200
{$WEB.URL}	App.pssadvantage.com
{$WT.DATA}	```json
{	
"data": [	

json
Copy
Edit
{
  "page_name": "login",
  "url": "https://App.pssadvantage.com"
}
]
}

|
Copy
Edit

---

## 📊 Setup Grafana Visualization

1. Open Grafana.
2. Go to **Connections → Data Sources**.
3. Add a **Zabbix** data source:
   - URL: your Zabbix frontend URL (e.g., `http://localhost/zabbix`)
   - Zabbix API details as required.
4. Import Dashboard:
   - Go to **Dashboards → Import**
   - Upload or paste JSON from `Web Monitoring-1748526175925.json`
   - Assign your Zabbix data source.

---

## ✅ Final Checks

- Ensure Zabbix server and agent have permission to run Python scripts.
- Confirm external checks are enabled in `zabbix_server.conf`:
  ```bash
  ExternalScripts=/usr/lib/zabbix/externalscripts
Restart Zabbix server after configuration:

bash
Copy
Edit
sudo systemctl restart zabbix-server
📁 Repository Structure
pgsql
Copy
Edit
/your-repo/
├── vu_report_new.py
├── website.py
├── wt.py
├── requirements.txt
├── zbx_export_templates (3).json
├── Web Monitoring-1748526175925.json
└── README.md
