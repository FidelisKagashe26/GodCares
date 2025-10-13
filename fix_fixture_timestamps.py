# fix_fixture_timestamps.py
import json
from pathlib import Path

IN_FILE  = Path("content/fixtures/content_seed.json")            # badilisha kama uko na path tofauti
OUT_FILE = Path("content_seed_fixed.json")

with IN_FILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

# modeli zenye auto_now_add / auto_now zisizo na null=True
NEED_CREATED_AT = {
    "content.category",
    "content.post",
    "content.season",
    "content.series",
    "content.lesson",
    "content.event",
    "content.mediaitem",
    "content.prayerrequest",
    "content.profile",
    "content.lessonlike",
    "content.lessoncomment",
    "content.announcement",
}

NEED_UPDATED_AT = {
    "content.post",
    "content.lesson",
}

DEFAULT_CREATED = "2025-09-01T09:00:00"
DEFAULT_UPDATED = "2025-09-01T09:00:00"

for obj in data:
    model = obj.get("model")
    fields = obj.get("fields", {})

    if model in NEED_CREATED_AT and not fields.get("created_at"):
        fields["created_at"] = DEFAULT_CREATED

    if model in NEED_UPDATED_AT and not fields.get("updated_at"):
        # kama created_at ipo, tumia hiyo, vinginevyo DEFAULT_UPDATED
        fields["updated_at"] = fields.get("created_at", DEFAULT_UPDATED)

    # weka tena
    obj["fields"] = fields

with OUT_FILE.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Done. Wrote {OUT_FILE}")
