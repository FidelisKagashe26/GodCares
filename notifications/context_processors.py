def unread_notifications(request):
    count = 0
    if request.user.is_authenticated:
        try:
            count = request.user.notifications.filter(is_read=False).count()
        except Exception:
            count = 0
    return {"notif_unread_count": count}

def notif_counts(request):
    count = 0
    u = getattr(request, "user", None)
    if getattr(u, "is_authenticated", False):
        try:
            count = u.notifications.filter(is_read=False).count()
        except Exception:
            pass
    return {"notif_unread_count": count}
