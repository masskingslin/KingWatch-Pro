"""
KingWatch Pro v17 - android_service.py
Foreground service - monitoring loop ONLY.
CRITICAL: Must NEVER import kivy, Builder, or any UI code.
The double-render bug was caused by this file triggering Kivy
window initialization in the service process.
"""
import time
import os

# Guard: only run service logic if we ARE the service process
# p4a sets PYTHON_SERVICE_ARGUMENT when running as a service
_is_service = (
    os.environ.get("PYTHON_SERVICE_ARGUMENT") is not None
    or os.environ.get("P4A_IS_SERVICE") is not None
)

if _is_service:
    try:
        from android import AndroidService  # type: ignore
        service = AndroidService("KingWatch Pro", "Monitoring system stats...")
        service.start("service started")
    except Exception:
        pass

    # Keep service alive - no UI, no Kivy, no imports of main
    while True:
        time.sleep(10)
