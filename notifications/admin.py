# notifications/admin.py
from django.contrib import admin, messages
from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Notification
from .utils import broadcast_notification

User = get_user_model()

class NotificationComposerForm(forms.Form):
    send_to_all = forms.BooleanField(
        required=False, label="Tuma kwa watumiaji wote (waliowasha arifa)"
    )
    recipients = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("username"),
        required=False, label="Wapokeaji maalum"
    )
    level = forms.ChoiceField(choices=Notification.LEVELS, initial="info", label="Aina")
    title = forms.CharField(max_length=200, label="Kichwa cha ujumbe")
    body = forms.CharField(widget=forms.Textarea, required=False, label="Ujumbe")
    url = forms.URLField(required=False, label="Kiungo (hiari)")
    email_also = forms.BooleanField(required=False, initial=True,
                                    label="Tuma pia kupitia barua pepe (kwa waliowasha)")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    # Hatutaki form ya model ya kawaida wakati wa “Add”
    list_display = ("title", "level", "recipient", "is_read", "created_at")
    list_filter = ("level", "is_read", "created_at")
    search_fields = ("title", "body", "recipient__username", "recipient__email")
    readonly_fields = ("recipient", "sender", "is_read", "read_at", "created_at")

    def has_add_permission(self, request):
        # Tunaruhusu “Add” lakini tutatumia composer yetu
        return True

    def add_view(self, request, form_url="", extra_context=None):
        # Onyesha fomu yetu ya composer badala ya ModelForm
        return self._render_composer(request)

    def _render_composer(self, request):
        if request.method == "POST":
            form = NotificationComposerForm(request.POST)
            if form.is_valid():
                send_to_all = form.cleaned_data["send_to_all"]
                recipients = list(form.cleaned_data["recipients"]) if not send_to_all else None
                title = form.cleaned_data["title"]
                body = form.cleaned_data["body"]
                url = form.cleaned_data["url"]
                level = form.cleaned_data["level"]
                email_also = form.cleaned_data["email_also"]

                if not send_to_all and not recipients:
                    form.add_error("recipients", "Chagua wapokeaji au tiki 'Tuma kwa wote'.")
                else:
                    with transaction.atomic():
                        created_count = broadcast_notification(
                            title=title,
                            body=body,
                            url=url,
                            level=level,
                            recipients=recipients,      # None => all opted-in users
                            send_email=email_also,
                            sender=request.user,        # Hatuwaonyeshi users; tunahifadhi tu
                        )
                    self.message_user(
                        request,
                        f"✅ Ujumbe umetumwa kwa {created_count} wapokeaji.",
                        level=messages.SUCCESS,
                    )
                    # Rudi kwenye list view ya Notification
                    from django.urls import reverse
                    from django.shortcuts import redirect
                    return redirect(reverse("admin:notifications_notification_changelist"))
        else:
            form = NotificationComposerForm()

        from django.template.response import TemplateResponse
        context = {
            **self.admin_site.each_context(request),
            "title": "Tuma Ujumbe Mpya",
            "form": form,
            "opts": Notification._meta,
            "add": True,
            "change": False,
            "is_popup": False,
            "save_as": False,
            "show_save": True,
        }
        # Tumia template ya admin generic form
        return TemplateResponse(request, "admin/notifications/composer.html", context)

    def get_urls(self):
        # Kuwezesha /add/ itumie composer yetu (tayari tumeshai-handle kwenye add_view)
        return super().get_urls()

    def get_form(self, request, obj=None, **kwargs):
        # Zuia ModelForm ya edit kubadilisha fields nyeti
        form = super().get_form(request, obj, **kwargs)
        if obj:
            # editing existing notification -> everything read-only
            for f in form.base_fields.values():
                f.disabled = True
        return form
