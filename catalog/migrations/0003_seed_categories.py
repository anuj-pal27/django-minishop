from django.db import migrations

CATEGORIES = [                        # data we want to insert
    ("Shoes", "shoes"),
    ("Clothing", "clothing"),
    ("Electronics", "electronics"),
]


def add_categories(apps, schema_editor):
    # Get the model as it was AT THIS migration, not today's version from models.py
    Category = apps.get_model("catalog", "Category")
    for name, slug in CATEGORIES:
        # get_or_create: only inserts if it's missing, so running it twice is safe
        Category.objects.get_or_create(slug=slug, defaults={"name": name})


def remove_categories(apps, schema_editor):
    # Runs when you roll back (undo) this migration
    Category = apps.get_model("catalog", "Category")
    Category.objects.filter(
        slug__in=[slug for _, slug in CATEGORIES],  # only our seeded categories
        products__isnull=True,                       # and only if no product uses them
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_category_description"),  # run after 0002
    ]

    operations = [
        migrations.RunPython(add_categories, remove_categories),  # (forward, backward)
    ]