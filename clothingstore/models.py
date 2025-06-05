from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('men', "Men's Wear"),
        ('women', "Women's Wear"),
        ('kid_boy', "Kid's Boy"),
        ('kid_girl', "Kid's Girl"),
        ('teen_boy', "Teen Boy"),
        ('teen_girl', "Teen Girl"),
        ('toddler_boy', "Toddler Boy"),
        ('toddler_girl', "Toddler Girl"),
    ]

    CLOTHING_TYPE_CHOICES = [
        ('tops', 'Tops'),
        ('bottoms', 'Bottoms'),
        ('dress', 'Dress'),
        ('terno', 'Terno'),
        ('suits', 'Suits'),
        ('romper', 'Romper'),
        ('jumpsuit', 'Jumpsuit'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    clothing_type = models.CharField(max_length=100, choices=CLOTHING_TYPE_CHOICES)
    image = models.ImageField(upload_to='products/')
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    def get_total(self):
        return self.product.price * self.quantity
    
    
class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=20, default='pending')
    payment_method = models.CharField(max_length=20, default='paypal')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total(self):
        return self.price * self.quantity