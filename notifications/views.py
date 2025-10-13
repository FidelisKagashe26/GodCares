# notifications/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Notification
from .services import broadcast_notification, mark_as_read
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()

@login_required
def inbox(request):
    qs = Notification.objects.filter(recipient=request.user).order_by("-created_at")
    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    # Mark-as-read on visit? Hapana—mteja atabonyeza kila moja; au ongeza "mark all read" kitufe
    return render(request, "notifications/inbox.html", {"page_obj": page_obj})

@login_required
def open_and_redirect(request, pk):
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    mark_as_read(notif)
    if notif.url:
        return redirect(notif.url)
    return redirect("notifications_inbox")

@login_required
def unread_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({"count": count})

@login_required
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True, read_at=timezone.now())
    return redirect("notifications_inbox")

@login_required
def api_unread_count(request):
    if request.method != "GET":
        return HttpResponseBadRequest("GET only")
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({"count": count})

@login_required
def api_mark_read(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    n = get_object_or_404(Notification, pk=pk, recipient=request.user)
    if not n.is_read:
        n.is_read = True
        n.read_at = timezone.now()
        n.save(update_fields=["is_read", "read_at"])
    return JsonResponse({"ok": True})

@login_required
def api_mark_all_read(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    qs = Notification.objects.filter(recipient=request.user, is_read=False)
    now = timezone.now()
    qs.update(is_read=True, read_at=now)
    return JsonResponse({"ok": True, "updated": qs.count()})

# ---------- Admin broadcast ----------
class BroadcastForm(forms.Form):
    title = forms.CharField(max_length=200)
    body = forms.CharField(widget=forms.Textarea, required=False)
    url = forms.URLField(required=False)
    level = forms.ChoiceField(choices=Notification.LEVELS, initial="info")
    audience = forms.ChoiceField(choices=[
        ("all", "Watumiaji Wote"),
        ("one", "Mtumiaji Mmoja"),
    ], initial="all")
    user = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True), required=False)

@user_passes_test(lambda u: u.is_staff)
def broadcast(request):
    if request.method == "POST":
        form = BroadcastForm(request.POST)
        if form.is_valid():
            audience = form.cleaned_data["audience"]
            recipients = None
            if audience == "one":
                recipients = [form.cleaned_data["user"]] if form.cleaned_data["user"] else []

            n = broadcast_notification(
                title=form.cleaned_data["title"],
                body=form.cleaned_data.get("body", ""),
                url=form.cleaned_data.get("url", ""),
                level=form.cleaned_data.get("level", "info"),
                recipients=recipients,
                sender=request.user,  # hatutaonyesha jina lake kwenye UI
            )
            return redirect("notifications_inbox")
    else:
        form = BroadcastForm()
    return render(request, "notifications/broadcast.html", {"form": form})
