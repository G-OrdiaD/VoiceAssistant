import sqlite3
import logging
import os
from typing import List

from ..security import SecurityManager
from .models import Task

class DatabaseManager:
    """
    SQLite-based storage for tasks with encryption.
    """
    def __init__(self, security_manager, db_path: str = None, test_mode: bool = False):
        self.security = security_manager
        self.test_mode = test_mode
        
        if test_mode:
            self.db_path = ":memory:"
        elif db_path:
            self.db_path = db_path
        else:
            self.db_path = self.security.get_secure_db_path()
            
        self._init_db()

    def _init_db(self):
        """Create the 'tasks' table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title_encrypted TEXT NOT NULL,
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
                
                # Set secure file permissions for production DB
                if not self.test_mode and os.path.exists(self.db_path):
                    os.chmod(self.db_path, 0x180)  # 0o600 in octal - owner read/write only
                    
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            raise

    def add_task(self, title: str, due_time: str) -> bool:
        """Add a new task with encrypted title."""
        try:
            encrypted_title = self.security.encrypt_data(title)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO tasks (title_encrypted, due_time, created_at, is_completed)
                    VALUES (?, ?, datetime('now'), 0);
                """, (encrypted_title, due_time))
                conn.commit()
                return True
        except sqlite3.Error as e:
            logging.error(f"Error adding task: {e}")
            return False

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks with decrypted titles."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("""
                    SELECT id, title_encrypted, due_time, created_at, is_completed
                    FROM tasks
                    ORDER BY due_time ASC;
                """)
                rows = cur.fetchall()
                tasks = []
                for row in rows:
                    try:
                        decrypted_title = self.security.decrypt_data(row["title_encrypted"])
                        task = Task(
                            id=row["id"],
                            title=decrypted_title,
                            due_time=row["due_time"],
                            created_at=row["created_at"],
                            is_completed=bool(row["is_completed"])
                        )
                        tasks.append(task)
                    except Exception as e:
                        logging.error(f"Error decrypting task {row['id']}: {e}")
                        # Fallback to placeholder if decryption fails
                        task = Task(
                            id=row["id"],
                            title="[Encrypted Task]",
                            due_time=row["due_time"],
                            created_at=row["created_at"],
                            is_completed=bool(row["is_completed"])
                        )
                        tasks.append(task)
                return tasks
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
    
    def clear_old_tasks(self) -> bool:
        """Remove tasks from previous calendar days."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    DELETE FROM tasks
                    WHERE DATE(created_at) < DATE('now')
                """)
                conn.commit()
            return True
        except sqlite3.Error as e:
            logging.error(f"Error clearing old tasks: {e}")
            return False