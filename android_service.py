"""
KingWatch Pro - android_service.py
Background foreground service.
Keeps monitoring alive when screen is off.
"""
import time

try:
    from android import AndroidService  # type: ignore
    service = AndroidService("KingWatch Pro", "Monitoring system stats...")
    service.start("service started")
except Exception:
    pass

while True:
    time.sleep(10)