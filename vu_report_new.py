#!/usr/lib/zabbix/externalscripts/env/bin/python3
import argparse
import pymysql
import json
import re
import os

# Read DB credentials from Zabbix config
def load_db_config(conf_path="/etc/zabbix/zabbix_server.conf"):
    config = {
        "host": "localhost",  # default
        "user": None,
        "password": None,
        "database": None,
    }

    if not os.path.exists(conf_path):
        raise FileNotFoundError(f"Config file not found: {conf_path}")

    with open(conf_path, "r") as file:
        for line in file:
            if line.startswith("#") or not line.strip():
                continue
            if match := re.match(r"DBHost=(.+)", line):
                config["host"] = match.group(1).strip()
            elif match := re.match(r"DBName=(.+)", line):
                config["database"] = match.group(1).strip()
            elif match := re.match(r"DBUser=(.+)", line):
                config["user"] = match.group(1).strip()
            elif match := re.match(r"DBPassword=(.+)", line):
                config["password"] = match.group(1).strip()

    if not all(config.values()):
        raise ValueError("Incomplete DB config loaded")

    return config

# Argument parsing
parser = argparse.ArgumentParser(description="Downtime stats for a host")
parser.add_argument("hostname", help="Zabbix host name")
args = parser.parse_args()

# SQL query
sql_query = """
SELECT
  h.name AS Website,
  COUNT(*) AS Downtime_Count,
  SUM(COALESCE(er.clock, UNIX_TIMESTAMP(NOW())) - e.clock) AS Total_Downtime_Seconds
FROM hosts h
JOIN items i ON i.hostid = h.hostid
JOIN functions f ON f.itemid = i.itemid
JOIN triggers t ON t.triggerid = f.triggerid
JOIN events e ON e.objectid = t.triggerid AND e.object = 0 AND e.value = 1
LEFT JOIN event_recovery erc ON erc.eventid = e.eventid
LEFT JOIN events er ON er.eventid = erc.r_eventid
WHERE h.name = %s
  AND t.description = 'Website not available'
  AND e.clock >= UNIX_TIMESTAMP(NOW() - INTERVAL 1 DAY)
  AND h.status = 0
GROUP BY h.hostid, h.name;
"""

# Fetch data
def fetch_data(hostname, db_config):
    conn = None
    try:
        conn = pymysql.connect(**db_config)
        with conn.cursor() as cursor:
            cursor.execute(sql_query, (hostname,))
            result = cursor.fetchone()

            if not result:
                return {
                    "host": hostname,
                    "downtime_count": 0,
                    "downtime_minutes": "00.00",
                }

            name, count, seconds = result
            seconds = int(seconds or 0)
            minutes = seconds // 60
            rem_seconds = seconds % 60

            return {
                "host": name,
                "downtime_count": int(count),
                "downtime_minutes": f"{minutes:02d}.{rem_seconds:02d}",
            }

    except Exception as e:
        return {"error": str(e)}
    finally:
        if conn:
            conn.close()

# Main execution
if __name__ == "__main__":
    db_config = load_db_config()
    data = fetch_data(args.hostname, db_config)
    print(json.dumps(data, indent=2))
