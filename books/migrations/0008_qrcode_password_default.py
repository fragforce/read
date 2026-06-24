import secrets

from django.db import migrations, models

QR_CODE_ALPHABET = "23456789abcdefghjkmnpqrstuvwxyz"


def backfill_passwords(apps, schema_editor):
    from registration.wordlist import WORDS

    QRCode = apps.get_model("books", "QRCode")
    for qr in QRCode.objects.filter(password=""):
        pin = "".join(secrets.choice(QR_CODE_ALPHABET) for _ in range(4))
        word1 = secrets.choice(WORDS).lower()
        word2 = secrets.choice(WORDS).lower()
        qr.password = f"{pin}-{word1}-{word2}"
        qr.save(update_fields=["password"])


def clear_passwords(apps, schema_editor):
    QRCode = apps.get_model("books", "QRCode")
    QRCode.objects.update(password="")


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0007_qrcode_short_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="qrcode",
            name="password",
            field=models.CharField(max_length=30),
        ),
        migrations.RunPython(backfill_passwords, clear_passwords),
    ]
