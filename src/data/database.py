import sqlite3
import logging
from typing import List
from .models import Task


class DatabaseManager:
    """
    SQLite-based storage for tasks.

    Security notes:
    - Uses parameterised queries (no string formatting).
    - DB path is provided by the app and not user-controlled.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create the 'tasks' table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        due_time TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        is_completed INTEGER DEFAULT 0
                    );
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tasks_due_time
                    ON tasks (due_time);
                """)
                conn.commit()
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            raise

    def add_task(self, title: str, due_time: str) -> bool:
        """Add a new task."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO tasks (title, due_time, created_at, is_completed)
                    VALUES (?, ?, datetime('now'), 0);
                """, (title, due_time))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error adding task: {e}")
            return False

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks ordered by due_time."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("""
                    SELECT id, title, due_time, created_at, is_completed
                    FROM tasks
                    ORDER BY due_time ASC;
                """)
                rows = cur.fetchall()
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