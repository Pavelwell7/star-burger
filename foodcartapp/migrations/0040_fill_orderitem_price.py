from django.db import migrations


def fill_prices(apps, schema_editor):
    OrderItem = apps.get_model('foodcartapp', 'OrderItem')

    for item in OrderItem.objects.filter(price=0):
        item.price = item.product.price
        item.save()

class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0039_orderitem_price'),
    ]

    operations = [
        migrations.RunPython(fill_prices, migrations.RunPython.noop),
    ]
