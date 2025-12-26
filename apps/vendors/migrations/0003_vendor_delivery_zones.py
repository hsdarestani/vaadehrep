# Generated manually to add vendor delivery zone relations.
import django.db.models.deletion
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("addresses", "0001_initial"),
        ("vendors", "0002_vendor_core_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="VendorDeliveryZone",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "vendor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vendor_zones",
                        to="vendors.vendor",
                    ),
                ),
                (
                    "zone",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vendor_zones",
                        to="addresses.deliveryzone",
                    ),
                ),
            ],
            options={
                "unique_together": {("vendor", "zone")},
                "indexes": [models.Index(fields=["vendor", "zone", "is_active"], name="vendors_ven_vendor_i_7163d5_idx")],
            },
        ),
        migrations.AddField(
            model_name="vendor",
            name="delivery_zones",
            field=models.ManyToManyField(
                blank=True,
                related_name="vendors",
                through="vendors.VendorDeliveryZone",
                to="addresses.deliveryzone",
            ),
        ),
    ]
