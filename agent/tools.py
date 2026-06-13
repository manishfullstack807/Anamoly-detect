import os
import csv
import json
import smtplib
import httpx
from email.mime.text import MIMEText
from datetime import datetime
from agent.config import settings
import pandas as pd

def load_csv_files() -> str:
    data_folder = "data"
    all_data = []

    for filename in os.listdir(data_folder):
        if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
            continue

        filepath = os.path.join(data_folder, filename)

        try:
            if filename.endswith(".xlsx"):
                df = pd.read_excel(filepath)
            else:
                try:
                    df = pd.read_csv(filepath, encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(filepath, encoding="latin-1")

            summary = f"--- File: {filename} ---\n"
            summary += f"Total rows: {len(df)}\n"
            summary += f"Columns: {list(df.columns)}\n\n"
            summary += f"Sample (first 20 rows):\n{df.head(20).to_string(index=False)}\n"

            all_data.append(summary)

        except Exception as e:
            all_data.append(f"--- File: {filename} --- ERROR: {str(e)}")

    if not all_data:
        return "No data files found."

    return "\n\n".join(all_data)


def log_decision(anomaly: str, reasoning: str, action: str) -> None:
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "anomaly": anomaly,
        "reasoning": reasoning,
        "action": action
    }
    with open("data/decisions.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"[LOG] Decision saved.")
