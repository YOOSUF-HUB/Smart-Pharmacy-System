# In the new migration file
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('Non_Medicine_inventory', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nonmedicalproduct',
            name='is_active',
        ),
    ]