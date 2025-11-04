import sqlite3
import logging
from typing import List, Optional
from dataclasses import dataclass

# ---- Data model ----
@dataclass
class Task:
    id: int
    title: str
    due_time: str
    created_at: str
    is_completed: bool

# ---- Database manager ----
class DatabaseManager:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._init_db()

    def _table_exists(self, conn: sqlite3.Connection, name: str) -> bool:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
            (name,)
        )
        return cur.fetchone() is not None

    def _init_db(self):
        """Initialize DB; migrate from legacy 'reminders' if present."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Create new 'tasks' table if not exists
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        due_time TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        is_completed INTEGER DEFAULT 0
                    );
                """)

                # If legacy 'reminders' exists and 'tasks' is empty, migrate data
                legacy_exists = self._table_exists(conn, "reminders")
                tasks_empty = conn.execute("SELECT COUNT(*) FROM tasks;").fetchone()[0] == 0

                if legacy_exists and tasks_empty:
                    logging.info("Migrating data from legacy 'reminders' to 'tasks'...")
                    # Create a view of legacy schema and copy across
                    # legacy cols: (id, task, reminder_time, created_at, is_completed)
                    conn.execute("""
                        INSERT INTO tasks (id, title, due_time, created_at, is_completed)
                        SELECT id, task, reminder_time, created_at,
                               CASE WHEN is_completed IS NULL THEN 0 ELSE is_completed END
                        FROM reminders;
                    """)
                    conn.commit()
                    logging.info("Migration complete.")

        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            raise

    # ---- CRUD ----
    def add_task(self, title: str, due_time: str) -> bool:
        """Add a new task."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO tasks (title, due_time, created_at)
                    VALUES (?, ?, datetime('now'));
                """, (title, due_time))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error adding task: {e}")
            return False

    def get_all_tasks(self) -> List[Task]:
        """Retrieve all pending tasks ordered by due_time."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute("""
                    SELECT * FROM tasks
                    WHERE is_completed = 0
                    ORDER BY due_time;
                """).fetchall()
                return [
                    Task(
                        id=row["id"],
                        title=row["title"],
                        due_time=row["due_time"],
                        created_at=row["created_at"],
                        is_completed=bool(row["is_completed"])
                    )
                    for row in rows
                ]
        except sqlite3.Error as e:
            logging.error(f"Error fetching tasks: {e}")
            return []

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute("DELETE FROM tasks WHERE id = ?;", (task_id,))
                conn.commit()
                return cur.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error deleting task: {e}")
            return False

    def mark_done(self, task_id: int) -> bool:
        """Mark a task as completed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.execute(
                    "UPDATE tasks SET is_completed = 1 WHERE id = ?;",
                    (task_id,)
                )
                conn.commit()
                return cur.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error completing task: {e}")
            return False