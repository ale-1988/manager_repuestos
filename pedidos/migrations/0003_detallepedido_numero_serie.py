from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('pedidos', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='detallepedido',
            name='numero_serie',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
