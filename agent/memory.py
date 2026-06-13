import sqlite3
import chromadb
from datetime import datetime
from uuid import uuid4


class HermesMemory:
    def __init__(self):
         self.chroma = chromadb.PersistentClient(path="data/chroma")
         self.collection = self.chroma.get_or_create_collection(
              name="hermes_skills"
         )
         self.conn = sqlite3.connect("data/memory.db", check_same_thread=False)
         self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                anomaly TEXT,
                reasoning TEXT,
                action TEXT
            )
        """)
        self.conn.commit()

    def store(self, anomaly: str, reasoning: str, action: str) -> str:
        decision_id = str(uuid4())
        timestamp = datetime.utcnow().isoformat()

        self.conn.execute(
            "INSERT INTO decisions VALUES (?, ?, ?, ?, ?)",
            (decision_id, timestamp, anomaly, reasoning, action)
        )
        self.conn.commit()

        self.collection.add(
            documents=[f"{anomaly} | action: {action}"],
            metadatas=[{"timestamp": timestamp, "action": action}],
            ids=[decision_id]
        )
        return decision_id

    def recall(self, situation: str, n: int = 3) -> list:
        if self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_texts=[situation],
            n_results=min(n, self.collection.count())
        )
        return results["documents"][0]

    def get_all(self, limit: int = 50) -> list:
        cursor = self.conn.execute(
            "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


memory = HermesMemory()