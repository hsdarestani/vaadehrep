# Generated to align catalog menu with vendor-scoped hierarchy and variants.
import django.db.models.deletion
from django.db import migrations, models
from django.utils import timezone
from django.utils.text import slugify


def populate_product_names_and_slugs(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    db_alias = schema_editor.connection.alias

    for product in Product.objects.using(db_alias).all():
        # Backfill name_fa from legacy name field if missing.
        if not getattr(product, "name_fa", None):
            product.name_fa = getattr(product, "name", "") or ""

        # Ensure slug exists per vendor for uniqueness.
        base_slug = product.slug or slugify(product.name_fa) or f"product-{product.pk}"
        slug = base_slug
        suffix = 1
        while Product.objects.using(db_alias).filter(vendor_id=product.vendor_id, slug=slug).exclude(pk=product.pk).exists():
            suffix += 1
            slug = f"{base_slug}-{suffix}"
        product.slug = slug
        product.save(update_fields=["name_fa", "slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="product",
            old_name="price_amount",
            new_name="base_price",
        ),
        migrations.AddField(
            model_name="product",
            name="is_available_today",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="product",
            name="name_en",
            field=models.CharField(blank=True, default="", max_length=180),
        ),
        migrations.AddField(
            model_name="product",
            name="name_fa",
            field=models.CharField(default="", max_length=180),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="product",
            name="slug",
            field=models.SlugField(blank=True, default=None, max_length=200, null=True),
        ),
        migrations.RunPython(populate_product_names_and_slugs, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="product",
            name="name",
        ),
        migrations.AlterUniqueTogether(
            name="product",
            unique_together={("vendor", "name_fa"), ("vendor", "slug")},
        ),
        migrations.AlterIndexTogether(
            name="product",
            index_together={("vendor", "is_active", "sort_order"), ("vendor", "category", "is_active"), ("vendor", "name_fa")},
        ),
        migrations.CreateModel(
            name="ProductVariant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=64)),
                ("name", models.CharField(max_length=120)),
                ("price_amount", models.BigIntegerField(default=0)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(default=timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("product", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="variants", to="catalog.product")),
            ],
            options={
                "unique_together": {("product", "code")},
                "indexes": [models.Index(fields=["product", "is_active", "sort_order"], name="catalog_pro_product__9d4290_idx")],
            },
        ),
    ]
