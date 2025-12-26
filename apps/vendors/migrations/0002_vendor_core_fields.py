# Generated manually to align Vendor schema with current model definition.
from django.db import migrations, models
from django.db.models import Q
from django.utils.text import slugify


def populate_slug_and_flags(apps, schema_editor):
    Vendor = apps.get_model("vendors", "Vendor")
    db_alias = schema_editor.connection.alias

    # Copy legacy allow_out_of_area_snap flag into the new field if it still exists on the table.
    if "allow_out_of_area_snap" in [f.attname for f in Vendor._meta.fields]:
        for vendor in Vendor.objects.using(db_alias).all():
            vendor.supports_out_of_zone_snapp_cod = getattr(vendor, "allow_out_of_area_snap", False)
            vendor.save(update_fields=["supports_out_of_zone_snapp_cod"])

    # Populate slug from name if missing.
    for vendor in Vendor.objects.using(db_alias).filter(Q(slug__isnull=True) | Q(slug="")):
        base_slug = slugify(vendor.name) or f"vendor-{vendor.pk}"
        slug = base_slug
        suffix = 1
        while Vendor.objects.using(db_alias).filter(slug=slug).exclude(pk=vendor.pk).exists():
            suffix += 1
            slug = f"{base_slug}-{suffix}"
        vendor.slug = slug
        vendor.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("vendors", "0001_initial"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="vendor",
            name="vendors_ven_is_acti_4a0adb_idx",
        ),
        migrations.RemoveIndex(
            model_name="vendor",
            name="vendors_ven_city_f6e221_idx",
        ),
        migrations.AddField(
            model_name="vendor",
            name="admin_notes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="vendor",
            name="address_text",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="vendor",
            name="is_accepting_orders",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="vendor",
            name="is_visible",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="vendor",
            name="logo_url",
            field=models.URLField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="vendor",
            name="max_active_orders",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="vendor",
            name="min_order_amount",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="vendor",
            name="prep_time_minutes_default",
            field=models.PositiveSmallIntegerField(default=20),
        ),
        migrations.AddField(
            model_name="vendor",
            name="slug",
            field=models.SlugField(blank=True, max_length=220, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="vendor",
            name="supports_in_zone_delivery",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="vendor",
            name="supports_out_of_zone_snapp_cod",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vendor",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="vendor",
            name="area",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AlterField(
            model_name="vendor",
            name="city",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AlterField(
            model_name="vendor",
            name="lat",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="vendor",
            name="lng",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="vendor",
            name="name",
            field=models.CharField(max_length=200),
        ),
        migrations.RenameField(
            model_name="vendor",
            old_name="sms_phone",
            new_name="primary_phone_number",
        ),
        migrations.RunPython(populate_slug_and_flags, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="vendor",
            name="slug",
            field=models.SlugField(max_length=220, unique=True),
        ),
        migrations.AlterField(
            model_name="vendor",
            name="primary_phone_number",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="accepts_preorder",
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="allow_out_of_area_snap",
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="closes_at",
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="max_orders_per_hour",
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="opens_at",
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="out_of_area_note",
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="service_radius_km",
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="updated_at",
        ),
        migrations.RemoveField(
            model_name="vendor",
            name="vendor_type",
        ),
        migrations.AddIndex(
            model_name="vendor",
            index=models.Index(fields=["is_active", "is_visible", "is_accepting_orders"], name="vendors_ven_is_acti_eeb134_idx"),
        ),
        migrations.AddIndex(
            model_name="vendor",
            index=models.Index(fields=["slug"], name="vendors_ven_slug_7b01ce_idx"),
        ),
    ]
