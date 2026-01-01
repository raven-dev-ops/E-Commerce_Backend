from django.db import migrations, models
from django.db.models import Count
from django.db.models.functions import Lower


def normalize_emails(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User.objects.exclude(email="").iterator():
        normalized = user.email.strip().lower()
        if user.email != normalized:
            User.objects.filter(pk=user.pk).update(email=normalized)


def check_duplicates(apps, schema_editor):
    User = apps.get_model("users", "User")
    duplicates = (
        User.objects.exclude(email="")
        .annotate(email_norm=Lower("email"))
        .values("email_norm")
        .annotate(cnt=Count("id"))
        .filter(cnt__gt=1)
    )
    if duplicates.exists():
        sample = ", ".join(row["email_norm"] for row in duplicates[:5])
        raise RuntimeError(
            "Duplicate emails detected. Resolve duplicates before applying "
            f"unique constraint. Sample: {sample}"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_user_is_paused"),
    ]

    operations = [
        migrations.RunPython(normalize_emails, migrations.RunPython.noop),
        migrations.RunPython(check_duplicates, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower("email"),
                name="unique_user_email_ci",
                condition=~models.Q(email=""),
            ),
        ),
    ]
