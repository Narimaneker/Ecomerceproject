# Generated by Django 5.0.6 on 2025-03-04 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_item_category_item_description_item_label_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='status',
            field=models.CharField(default='new', max_length=200),
            preserve_default=False,
        ),
    ]
