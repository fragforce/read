import secrets

from django.db import migrations, models

QR_CODE_ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"


def backfill_short_codes(apps, schema_editor):
    QRCode = apps.get_model("books", "QRCode")
    existing = set(QRCode.objects.values_list("short_code", flat=True))
    for qr in QRCode.objects.filter(short_code__isnull=True):
        for _ in range(100):
            candidate = "".join(secrets.choice(QR_CODE_ALPHABET) for _ in range(8))
            if candidate not in existing:
                qr.short_code = candidate
                qr.save(update_fields=["short_code"])
                existing.add(candidate)
                break


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0006_recording_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="qrcode",
            name="short_code",
            field=models.CharField(max_length=8, null=True),
        ),
        migrations.RunPython(backfill_short_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="qrcode",
            name="short_code",
            field=models.CharField(default=None, max_length=8, unique=True),
            preserve_default=False,
        ),
    ]
