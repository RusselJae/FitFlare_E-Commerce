from .models import Product

def global_categories(request):
    return {
        'categories': [('all', 'All Categories')] + list(Product.CATEGORY_CHOICES),
        'clothing_types': [('all', 'All Types')] + list(Product.CLOTHING_TYPE_CHOICES),
    }