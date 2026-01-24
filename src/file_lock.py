"""
Cross-platform file locking utility.
Uses filelock library to prevent concurrent access to shared files.
"""
import logging
from pathlib import Path
from contextlib import contextmanager
from typing import Union, Generator

# Try to import filelock, or define a dummy fallback if not installed
# (though it should be installed via requirements.txt)
try:
    from filelock import FileLock, Timeout
    FILELOCK_AVAILABLE = True
except ImportError:
    FILELOCK_AVAILABLE = False
    
logger = logging.getLogger(__name__)

class DummyLock:
    """Fallback lock that does nothing (for when filelock is missing)."""
    def __init__(self, lock_file, timeout=-1):
        pass
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
        
    def acquire(self, timeout=-1):
        pass
        
    def release(self):
        pass

@contextmanager
def safe_lock(file_path: Union[str, Path], timeout: int = 10) -> Generator[None, None, None]:
    """
    Acquires a lock for the given file.
    The lock file will be created as {file_path}.lock
    """
    path = Path(file_path)
    lock_path = path.parent / f"{path.name}.lock"
    
    if FILELOCK_AVAILABLE:
        lock = FileLock(str(lock_path), timeout=timeout)
        try:
            with lock:
                yield
        except Timeout:
            logger.warning(f"Could not acquire lock for {file_path} after {timeout}s")
            # Proceed anyway? Or raise? Better to raise to prevent corruption.
            raise TimeoutError(f"Could not acquire lock for {file_path}")
    else:
        logger.warning(f"filelock not installed. Proceeding without lock for {file_path}")
        yield
