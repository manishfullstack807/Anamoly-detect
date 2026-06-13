import os
import pandas as pd


def load_dataframe() -> pd.DataFrame:
    data_folder = "data"
    for filename in os.listdir(data_folder):
        if filename.endswith(".xlsx") or filename.endswith(".csv"):
            filepath = os.path.join(data_folder, filename)
            if filename.endswith(".xlsx"):
                return pd.read_excel(filepath)
            else:
                return pd.read_csv(filepath)
    return pd.DataFrame()


def verify(agent_anomalies: str) -> dict:
    df = load_dataframe()
    if df.empty:
        return {"error": "No data file found"}

    report = {}

    if "Sales" in df.columns:
        neg_sales = int((df["Sales"] < 0).sum())
        report["negative_sales"] = {
            "agent_claimed": "negative sales" in agent_anomalies.lower(),
            "data_confirms": neg_sales > 0,
            "count": neg_sales
        }

    if "Order ID" in df.columns:
        dupes = int(df["Order ID"].duplicated().sum())
        report["duplicate_order_ids"] = {
            "agent_claimed": "duplicate order" in agent_anomalies.lower(),
            "data_confirms": dupes > 0,
            "count": dupes
        }

    if "Ship Date" in df.columns and "Order Date" in df.columns:
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
        invalid_dates = int((df["Ship Date"] < df["Order Date"]).sum())
        report["invalid_ship_dates"] = {
            "agent_claimed": "ship date" in agent_anomalies.lower(),
            "data_confirms": invalid_dates > 0,
            "count": invalid_dates
        }

    missing = df.isnull().sum()
    missing_cols = {k: int(v) for k, v in missing[missing > 0].items()}
    report["missing_values"] = {
        "agent_claimed": "missing" in agent_anomalies.lower(),
        "data_confirms": len(missing_cols) > 0,
        "columns": missing_cols
    }

    if "Profit" in df.columns:
        q1 = df["Profit"].quantile(0.25)
        q3 = df["Profit"].quantile(0.75)
        iqr = q3 - q1
        outliers = int(((df["Profit"] < q1 - 1.5 * iqr) | (df["Profit"] > q3 + 1.5 * iqr)).sum())
        report["profit_outliers"] = {
            "agent_claimed": "profit" in agent_anomalies.lower(),
            "data_confirms": outliers > 0,
            "count": outliers
        }

    confirmed = sum(
        1 for v in report.values()
        if isinstance(v, dict) and v.get("agent_claimed") and v.get("data_confirms")
    )
    claimed = sum(
        1 for v in report.values()
        if isinstance(v, dict) and v.get("agent_claimed")
    )

    report["accuracy_score"] = f"{confirmed}/{claimed} agent claims verified by data"
    report["accuracy_percent"] = round((confirmed / claimed * 100) if claimed > 0 else 0, 1)

    return report
