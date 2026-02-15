import sqlite3
from pathlib import Path
from datetime import datetime

class NoteStore:
    """
    Note manager with sqlite DB
    initialize connection with DB
    Args: db_path (path to .db file)
    """
    def __init__(self, db_path:Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """
        Creates a Note table if not already exists
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    slug TEXT UNIQUE NOT NULL,
                    content TEXT,
                    tags TEXT,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                ) 
            """)


    def create_note(self, title, slug, content="", tags=""):
        """
        Creates a new note, Fails if slug already exists
        """
        now = datetime.now().isoformat(timespec='seconds')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            INSERT INTO notes (title, slug, content, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (title, slug, content, tags, now, now))

    def get_content(self, slug):
        """
        gets the content of a note
        :param slug: unique slug
        :return: content of note or empty string if note not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT content FROM notes  WHERE slug = ?", (slug,))
            row = cursor.fetchone()
            return row[0] if row else None


    def update_content(self, slug, new_content):
        """
        Updates the body of an existing note and refreshes its timestamp.
        The method uses the 'slug' as a unique identifier to locate the note.
        Args:
            slug (str): The unique identifier for the note (e.g., 'meeting-notes').
            new_content (str): The new text content to be saved.
        """
        now = datetime.now().isoformat(timespec='seconds')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE notes
                SET content = ?, updated_at = ?
                WHERE slug = ?
            """, (new_content, now, slug))


    def update_tags(self, slug, new_tags):
        """
        Updates tags for a specific note
        """
        now = datetime.now().isoformat(timespec='seconds')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                         UPDATE notes 
                         SET tags = ?, updated_at = ? 
                         WHERE slug = ?
                         """, (new_tags, now, slug))

    def rename_note(self, slug, new_name, new_slug):
        """
        Updates title of a specific note
        """
        now = datetime.now().isoformat(timespec='seconds')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                        UPDATE notes
                        SET title = ?, slug = ?, updated_at = ?
                        WHERE slug = ?
                        """, (new_name, new_slug, now, slug))

    def search(self, query):
        """
        search notes based on title, tags, or content
        :param query: key-word for search
        :return:list of tuples (title, slug)
        """
        search_query = f"%{query.lower()}%"
        with sqlite3.connect(self.db_path) as conn:
           cursor = conn.execute(
               """SELECT title, slug from notes
                   WHERE LOWER(title) LIKE ?
                   OR LOWER(tags) LIKE ?
                   OR LOWER(content) LIKE ?
               """, (search_query, search_query, search_query)
           )
           return cursor.fetchall()


    def list_notes(self):
        """
        returns all notes sorted by date (newest first)
        :return: List of tuples (title, slug, tags, updated_at)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(""" SELECT title, slug, tags, updated_at FROM notes ORDER BY updated_at DESC """)
            return cursor.fetchall()


    def list_notes_by_tag(self, tag):
        """
        Returns notes with a specific tag
        """
        search_tag = f"%{tag.lower()}%"
        with sqlite3.connect(self.db_path) as conn:
            cursor =  conn.execute("""
                SELECT title, slug, tags, updated_at
                FROM notes WHERE LOWER(tags) LIKE ?
                ORDER BY updated_at DESC
            """, (search_tag,))
            return cursor.fetchall()


    def delete_note(self, slug):
        """
        Deletes a note based on slug
        :param slug:
        :return: True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(" DELETE FROM notes WHERE slug = ? ", (slug,))
            return cursor.rowcount > 0


    def export_debug_log(self):
        """
        exports note content into a human-readable .txt file
        """
        log_dir = Path("debug")
        log_dir.mkdir(exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, title, slug, content, tags, updated_at FROM notes")
            rows = cursor.fetchall()

        with open(log_dir/"db_viewer.txt", "w", encoding="utf-8") as file:
            file.write(f"=== LAZY NOTES DEBUG LOG ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===\n\n")
            for row in rows:
                file.write(f"[{row[0]}] {row[1]} (slug: {row[2]})\n")
                file.write(f"Content\n{row[3]}\n")
                file.write(f"Tags: {row[4]} | Last update: {row[5]}\n")
                file.write("-" * 50 + "\n")