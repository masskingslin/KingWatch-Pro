"""
KingWatch Pro â€” Background Foreground Service
Keeps system monitoring active when screen is off.
Runs as android.service in buildozer.spec.
"""
import time
from android import AndroidService  # type: ignore

service = AndroidService("KingWatch Pro", "Monitoring system stats...")
service.start("service started")

# Keep the service alive
while True:
    time.sleep(10)