from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from clothingstore.models import Order

class Command(BaseCommand):
    help = 'Removes cancelled and delivered orders that are older than 1 hour'

    def handle(self, *args, **options):
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        # Get orders to delete
        orders_to_delete = Order.objects.filter(
            status__in=['cancelled', 'delivered'],
            created_at__lt=one_hour_ago
        )
        
        # Count orders before deletion
        count = orders_to_delete.count()
        
        # Delete the orders
        orders_to_delete.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} old orders')
        ) 