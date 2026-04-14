from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dv_dathoa', '0008_shopgalleryimage_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='phienchat',
            name='last_read_kh',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='phienchat',
            name='last_read_tiem',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
