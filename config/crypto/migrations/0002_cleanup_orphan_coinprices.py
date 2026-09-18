from django.db import migrations

def delete_orphan_coinprices(apps, schema_editor):
    CoinPrice = apps.get_model('crypto', 'CoinPrice')
    CoinPrice.objects.filter(snapshot__isnull=True).delete()

class Migration(migrations.Migration):
    dependencies = [('crypto', '0001_initial'),]
    operations = [migrations.RunPython(delete_orphan_coinprices, migrations.RunPython.noop),]