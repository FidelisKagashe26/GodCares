from django.core.management.base import BaseCommand
from discipleship.models import Level, Lesson

class Command(BaseCommand):
    help = "Seed sample Levels & Lessons for quick testing."

    def handle(self, *args, **opts):
        data = [
            {
                "name": "Discovery (Level 1)",
                "slug": "level-1",
                "order": 1,
                "desc": "Kuanza safari ya kumjua Mungu.",
                "lessons": [
                    ("Mungu ni Nani?", "mungu-ni-nani"),
                    ("Tatizo la Dhambi", "tatizo-la-dhambi"),
                    ("Suluhisho la Kristo", "suluhisho-la-kristo"),
                ],
            },
            {
                "name": "Growth (Level 2)",
                "slug": "level-2",
                "order": 2,
                "desc": "Kukua kiroho baada ya ubatizo.",
                "lessons": [
                    ("Sala na Neno", "sala-na-neno"),
                    ("Ushirika", "ushirika"),
                ],
            },
        ]
        created_levels = 0
        created_lessons = 0
        for lv in data:
            level, lvc = Level.objects.get_or_create(
                slug=lv["slug"], defaults={"name": lv["name"], "order": lv["order"], "description": lv["desc"], "is_active": True}
            )
            if lvc:
                created_levels += 1
            for i, (title, slug) in enumerate(lv["lessons"], start=1):
                _, lc = Lesson.objects.get_or_create(
                    level=level, slug=slug,
                    defaults={"title": title, "order": i, "is_published": True, "body": f"<p>{title} — content...</p>"}
                )
                if lc:
                    created_lessons += 1
        self.stdout.write(self.style.SUCCESS(f"Done. Levels+Lessons: {created_levels}/{created_lessons} created."))
