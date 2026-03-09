"""
Android Foreground Service — KingWatch Pro v15
Keeps the monitoring alive when the app is backgrounded.
Google Play compliant — uses DATA_SYNC foreground service type on API 34+.
"""

CHANNEL_ID      = "kingwatch_v15_channel"
NOTIFICATION_ID = 2001


def start_foreground_service():
    """Call from main thread within app startup."""
    from jnius import autoclass

    PythonActivity      = autoclass("org.kivy.android.PythonActivity")
    Build               = autoclass("android.os.Build")
    NotificationManager = autoclass("android.app.NotificationManager")
    Context             = autoclass("android.content.Context")

    activity = PythonActivity.mActivity

    # ── Create notification channel (Android 8+ / API 26+) ────────────────
    if Build.VERSION.SDK_INT >= 26:
        NotificationChannel = autoclass("android.app.NotificationChannel")
        nm = activity.getSystemService(Context.NOTIFICATION_SERVICE)
        if nm.getNotificationChannel(CHANNEL_ID) is None:
            channel = NotificationChannel(
                CHANNEL_ID,
                "KingWatch Monitor",
                NotificationManager.IMPORTANCE_LOW,   # silent, no vibration
            )
            channel.setDescription("Real-time system stats monitoring")
            channel.setShowBadge(False)
            channel.enableVibration(False)
            nm.createNotificationChannel(channel)

    # ── Build notification ─────────────────────────────────────────────────
    Notification = autoclass("android.app.Notification")
    if Build.VERSION.SDK_INT >= 26:
        Builder = autoclass("android.app.Notification$Builder")
        builder = Builder(activity, CHANNEL_ID)
    else:
        Builder = autoclass("android.support.v4.app.NotificationCompat$Builder")
        builder = Builder(activity, CHANNEL_ID)

    builder.setContentTitle("KingWatch Pro")
    builder.setContentText("Monitoring CPU · RAM · Battery · Network")
    builder.setSmallIcon(activity.getApplicationInfo().icon)
    builder.setOngoing(True)
    builder.setPriority(-2)   # PRIORITY_MIN

    if Build.VERSION.SDK_INT >= 31:
        builder.setForegroundServiceBehavior(
            Notification.FOREGROUND_SERVICE_IMMEDIATE
        )

    notification = builder.build()

    # ── Start foreground ───────────────────────────────────────────────────
    if Build.VERSION.SDK_INT >= 34:
        ServiceInfo = autoclass("android.content.pm.ServiceInfo")
        activity.startForeground(
            NOTIFICATION_ID,
            notification,
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC,
        )
    else:
        activity.startForeground(NOTIFICATION_ID, notification)
