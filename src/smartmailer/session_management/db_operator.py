import threading
from typing import List, Optional, Dict, Any
from smartmailer.session_management.db import Database
from smartmailer.utils.new_logger import Logger


class DBOperator:
    """Buffered singleton wrapper for Database operations."""

    _instance: Optional["DBOperator"] = None
    _init_lock = threading.Lock()

    def __new__(cls, dbfile_path: str) -> "DBOperator":
        with cls._init_lock:
            if cls._instance is None:
                instance = object.__new__(cls)
                instance._initialized = False
                cls._instance = instance
        return cls._instance

    def __init__(self, dbfile_path: str) -> None:
        # Avoid re-initialization
        if self._initialized:
            return

        self.logger = Logger()
        self._db = Database(dbfile_path)

        # Initialize buffer and lock
        self._buffer: List[str] = []
        self._buffer_lock = threading.Lock()

        # Background flush thread
        self._stop_event = threading.Event()
        self._flush_thread = threading.Thread(
            target=self._flush_loop, name="DBOperator-flush", daemon=True
        )
        self._flush_thread.start()
        self.logger.info("DBOperator started (flush interval = 1 s).")

        self._initialized = True

    def add_to_db(self, recipient_hash: str) -> None:
        """Append *recipient_hash* to the pending buffer."""
        with self._buffer_lock:
            self._buffer.append(recipient_hash)
        self.logger.info(f"Buffered recipient {recipient_hash}.")

    def shutdown(self) -> None:
        # Final flush and cleanup
        self.logger.info("DBOperator shutting down – performing final flush.")
        self._stop_event.set()
        self._flush_thread.join()
        self._flush()          # one last flush for anything added between the last tick and stop
        self._db.close()
        DBOperator._instance = None
        self.logger.info("DBOperator shut down cleanly.")

    def _flush_loop(self) -> None:
        """Background loop: flush once per second until stopped."""
        while not self._stop_event.wait(timeout=1.0):
            self._flush()

    def _flush(self) -> None:
        """Drain the buffer and persist every entry to the database."""
        with self._buffer_lock:
            if not self._buffer:
                return
            batch, self._buffer = self._buffer, []

        self.logger.info(f"Flushing {len(batch)} record(s) to database.")
        try:
            self._db.batch_insert_recipients(batch)
        except Exception as exc:  # pragma: no cover
            self.logger.error(
                f"Failed to flush batch of {len(batch)}: {exc}. Re-buffering."
            )
            with self._buffer_lock:
                # Prepend the failed batch back to the buffer to preserve order as much as possible
                self._buffer = batch + self._buffer

    def check_recipient_sent(self, recipient_hash: str) -> bool:
        """Check if *recipient_hash* is in the pending buffer or the database."""
        with self._buffer_lock:
            if recipient_hash in self._buffer:
                return True
        return self._db.check_recipient_sent(recipient_hash)

    def get_sent_recipients(self) -> List[Dict[str, Any]]:
        return self._db.get_sent_recipients()

    def delete_recipient(self, recipient_hash: str) -> None:
        self._db.delete_recipient(recipient_hash)

    def clear_database(self) -> None:
        with self._buffer_lock:
            self._buffer.clear()
        self._db.clear_database()

    def __enter__(self) -> "DBOperator":
        return self

    def __exit__(self, *_) -> None:
        self.shutdown()