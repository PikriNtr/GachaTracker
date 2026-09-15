"""API process state (import lock)."""
import threading

# One import at a time across the process; shared by the import endpoint.
import_lock = threading.Lock()
