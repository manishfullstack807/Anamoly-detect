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
        if filename.endswith(".csv") or filename.endswith(".xlsx"):
            filepath = os.path.join(data_folder, filename)

            if filename.endswith(".xlsx"):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)

            summary = f"--- File: {filename} ---\n"
            summary += f"Total rows: {len(df)}\n"
            summary += f"Columns: {list(df.columns)}\n\n"
            summary += f"Sample (first 50 rows):\n{df.head(50).to_string(index=False)}\n\n"
            summary += f"Basic stats:\n{df.describe(include='all').to_string()}\n"

            all_data.append(summary)

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
