from django.db import migrations, models

def set_initial_order_numbers(apps, schema_editor):
    Order = apps.get_model('clothingstore', 'Order')
    # Get all users who have orders
    users = Order.objects.values_list('user', flat=True).distinct()
    
    for user_id in users:
        # Get all orders for this user, ordered by creation date
        orders = Order.objects.filter(user_id=user_id).order_by('created_at')
        # Update order numbers starting from 1
        for index, order in enumerate(orders, 1):
            order.user_order_number = index
            order.save()

class Migration(migrations.Migration):

    dependencies = [
        ('clothingstore', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='user_order_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.RunPython(set_initial_order_numbers),
    ] 