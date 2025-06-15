import json
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout 
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Product, CartItem
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Order, OrderItem
from django.db import transaction
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg, F
from django.db.models import Sum, Count, F, DecimalField
from django.db.models.functions import Cast
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.paginator import Paginator
from .forms import CustomUserCreationForm
from django.db import models

#user authentication views

def home(request):
    # Get 6 featured products (you can modify the query based on your needs)
    featured_products = Product.objects.filter(stock__gt=0).order_by('-id')[:6]
    return render(request, 'home.html', {
        'featured_products': featured_products
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def product_list(request):
    # Get filter parameters from request
    category = request.GET.get('category', '')
    clothing_type = request.GET.get('clothing_type', '')
    price_range = request.GET.get('price_range', '')
    
    # Start with all products
    products = Product.objects.all()
    
    # Filter by category if selected
    if category and category != 'all':
        products = products.filter(category=category)
        
    # Filter by clothing type if selected    
    if clothing_type and clothing_type != 'all':
        products = products.filter(clothing_type=clothing_type)
    
    # Filter by price range if selected
    if price_range:
        if price_range == 'under_500':
            products = products.filter(price__lt=500)
        elif price_range == '500_1000':
            products = products.filter(price__gte=500, price__lte=1000)
        elif price_range == 'over_1000':
            products = products.filter(price__gt=1000)
    
    # Add pagination
    paginator = Paginator(products, 9)  # Show 9 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'selected_category': category,
        'selected_clothing_type': clothing_type,
        'selected_price_range': price_range,
        'categories': [('all', 'All Categories')] + list(Product.CATEGORY_CHOICES),
        'clothing_types': [('all', 'All Types')] + list(Product.CLOTHING_TYPE_CHOICES),
        'price_ranges': [
            ('all', 'All Prices'),
            ('under_500', 'Under ₱500'), 
            ('500_1000', '₱500 - ₱1000'),
            ('over_1000', 'Over ₱1000')
        ]
    }
    return render(request, 'product_list.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_superuser:
                return redirect('admin_dashboard')
            return redirect('home')
        else:
            return render(request, 'login.html', {
                'form': {
                    'non_field_errors': ['Invalid username or password.']
                }
            })
    return render(request, 'login.html')



def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')



@login_required
def cart_view(request):
    cart_items = CartItem.objects.filter(user=request.user)
    subtotal = sum(item.get_total() for item in cart_items)
    total = subtotal  # Add shipping/tax calculation if needed
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'total': total,
    }
    return render(request, 'cart.html', context)

@login_required
def update_cart(request, item_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
            
            cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
            
            # Validate quantity against stock
            if quantity > cart_item.product.stock:
                return JsonResponse({
                    'success': False,
                    'message': 'Not enough stock available'
                })
            
            cart_item.quantity = quantity
            cart_item.save()
            
            return JsonResponse({
                'success': True,
                'item_total': str(cart_item.get_total())
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })

    return JsonResponse({'success': False})

@login_required
def store_cart_selection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            selected_items = data.get('selected_items', [])
            request.session['selected_cart_items'] = selected_items
            return JsonResponse({'success': True})
        except:
            return JsonResponse({'success': False})
    return JsonResponse({'success': False})

from django.conf import settings
from decimal import Decimal

@login_required
def checkout_view(request):
    if request.method == 'POST':
        try:
            # Validate form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            address = request.POST.get('address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            zip_code = request.POST.get('zip_code')
            payment_id = request.POST.get('paymentId')

            if not all([first_name, last_name, address, city, state, zip_code, payment_id]):
                messages.error(request, 'Please fill in all required fields')
                return redirect('checkout')

            # Get selected cart items
            selected_items = request.POST.getlist('selected_items')
            if not selected_items:
                messages.error(request, 'No items selected for checkout')
                return redirect('cart')

            cart_items = CartItem.objects.filter(
                user=request.user,
                id__in=selected_items
            )

            if not cart_items:
                messages.error(request, 'Selected items not found in cart')
                return redirect('cart')

            with transaction.atomic():
                # Calculate total
                total_amount = sum(item.get_total() for item in cart_items)
                # Format amount to 2 decimal places for comparison
                formatted_total = '{:.2f}'.format(total_amount)

                if formatted_total != request.POST.get('amount'):
                    messages.error(request, 'Payment amount mismatch')
                    return redirect('checkout')

                # Create order
                order = Order.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    address=address,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    total_amount=total_amount,
                    payment_method='paypal',
                    payment_status='completed',
                    payment_id=payment_id
                )

                for cart_item in cart_items:
                    # Check stock availability
                    if cart_item.quantity > cart_item.product.stock:
                        raise ValueError(f'Not enough stock for {cart_item.product.name}')
                        
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=cart_item.product.price
                    )

                    # Update product stock
                    cart_item.product.stock -= cart_item.quantity
                    cart_item.product.save()
                    cart_item.delete()

                if 'selected_cart_items' in request.session:
                    del request.session['selected_cart_items']

                return redirect('order_receipt', order_id=order.id)

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('checkout')
        except Exception as e:
            messages.error(request, 'An error occurred while processing your order. Please try again.')
            return redirect('checkout')

    # Handle GET request
    try:
        selected_items = request.session.get('selected_cart_items', [])
        cart_items = CartItem.objects.filter(
            user=request.user,
            id__in=selected_items
        )

        if not cart_items:
            messages.error(request, 'No items selected for checkout')
            return redirect('cart')

        total_amount = sum(item.get_total() for item in cart_items)

        context = {
            'selected_items': cart_items,
            'total_amount': total_amount,
            'paypal_client_id': settings.PAYPAL_CLIENT_ID
        }
        return render(request, 'checkout.html', context)
    except Exception as e:
        messages.error(request, 'Error loading checkout page')
        return redirect('cart')
    

@login_required
def order_receipt(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        return render(request, 'order_receipt.html', {'order': order})
    except Order.DoesNotExist:
        messages.error(request, 'Order not found')
        return redirect('order_history')


@login_required
def account_settings(request):
    if request.method == 'POST':
        # Handle form submission
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()
        return redirect('account_settings')
    
    return render(request, 'account_settings.html')

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

@login_required
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        if order.status != 'pending':
            return JsonResponse({
                'success': False,
                'message': 'Only pending orders can be cancelled'
            })
            
        order.status = 'cancelled'
        order.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Order cancelled successfully'
        })
    except Order.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Order not found'
        })

# In views.py
def order_history(request):
    orders = Order.objects.filter(user=request.user)
    
    # Handle status filter
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    
    # Handle search
    search = request.GET.get('search')
    if search:
        orders = orders.filter(
            models.Q(id__icontains=search) |
            models.Q(total_amount__icontains=search) |
            models.Q(items__product__name__icontains=search)
        ).distinct()
    
    orders = orders.order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    # Get quantity from request body
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
    except:
        quantity = 1
    
    # Validate quantity against stock
    if quantity > product.stock:
        return JsonResponse({
            'success': False,
            'message': 'Not enough stock available'
        })
    
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity
        
    # Check if total quantity exceeds stock
    if cart_item.quantity > product.stock:
        return JsonResponse({
            'success': False,
            'message': 'Not enough stock available'
        })
        
    cart_item.save()
    return JsonResponse({'success': True})

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, user=request.user)
    cart_item.delete()
    return JsonResponse({'success': True})




    




#admin interface views

def is_admin(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_admin)
def admin_dashboard(request):
    product_count = Product.objects.count()
    user_count = User.objects.count()
    order_count = Order.objects.count()
    total_sales = Order.objects.filter(payment_status='completed').aggregate(
        total=Sum('total_amount'))['total'] or 0
    recent_products = Product.objects.order_by('-id')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    # Add pagination for orders
    orders = Order.objects.order_by('-created_at')
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'product_count': product_count,
        'user_count': user_count,
        'order_count': order_count,
        'total_sales': total_sales,
        'recent_products': recent_products,
        'recent_users': recent_users,
        'page_obj': page_obj
    }
    return render(request, 'admin/dashboard.html', context)

@user_passes_test(is_admin)
def admin_users(request):
    # Get all users
    users_list = User.objects.all().order_by('-date_joined')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    # Apply search filter
    if search_query:
        users_list = users_list.filter(
            models.Q(username__icontains=search_query) |
            models.Q(email__icontains=search_query) |
            models.Q(first_name__icontains=search_query) |
            models.Q(last_name__icontains=search_query)
        )
    
    # Apply role filter
    if role_filter:
        if role_filter == 'admin':
            users_list = users_list.filter(is_superuser=True)
        elif role_filter == 'user':
            users_list = users_list.filter(is_superuser=False)
    
    # Add pagination
    paginator = Paginator(users_list, 10)  # Show 10 users per page
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter
    }
    return render(request, 'admin/users.html', context)

@user_passes_test(is_admin)
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.is_active = 'is_active' in request.POST
        user.is_staff = 'is_staff' in request.POST
        user.is_superuser = 'is_superuser' in request.POST
        user.save()
        return redirect('admin_users')
    return render(request, 'admin/user_form.html', {'edit_user': user})



@user_passes_test(is_admin)
def admin_user_create(request):
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']
            if not all(request.POST.get(field) for field in required_fields):
                messages.error(request, 'Please fill in all required fields')
                return render(request, 'admin/user_form.html')

            if request.POST['password1'] != request.POST['password2']:
                messages.error(request, 'Passwords do not match')
                return render(request, 'admin/user_form.html')

            # Create user
            user = User.objects.create_user(
                username=request.POST['username'],
                email=request.POST['email'],
                password=request.POST['password1'],
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name']
            )

            # Set admin status if selected
            if request.POST.get('is_superuser'):
                user.is_superuser = True
                user.is_staff = True
                user.save()

            messages.success(request, f'User "{user.username}" created successfully')
            return redirect('admin_users')

        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
            return render(request, 'admin/user_form.html')

    return render(request, 'admin/user_form.html')

@user_passes_test(is_admin)
def admin_user_delete(request, pk):
    if request.method == 'DELETE':
        try:
            user = get_object_or_404(User, pk=pk)
            if user == request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'You cannot delete your own account'
                }, status=400)
            username = user.username
            user.delete()
            return JsonResponse({
                'success': True,
                'message': f'User "{username}" deleted successfully'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=500)
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)

@user_passes_test(is_admin)
def admin_products(request):
    # Add search and filtering
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    type_filter = request.GET.get('clothing_type', '')
    
    products = Product.objects.all()
    
    # Apply filters
    if search_query:
        products = products.filter(
            models.Q(name__icontains=search_query) |
            models.Q(description__icontains=search_query)
        )
    
    if category_filter:
        products = products.filter(category=category_filter)
        
    if type_filter:
        products = products.filter(clothing_type=type_filter)
    
    # Sort products by latest first
    products = products.order_by('-id')
    
    # Add pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'type_filter': type_filter,
        'categories': Product.CATEGORY_CHOICES,
        'clothing_types': Product.CLOTHING_TYPE_CHOICES
    }
    return render(request, 'admin/products.html', context)

@user_passes_test(is_admin)
def admin_product_create(request):
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'description', 'price', 'category', 'clothing_type', 'stock']
            if not all(request.POST.get(field) for field in required_fields):
                messages.error(request, 'Please fill in all required fields')
                return render(request, 'admin/product_form.html')
                
            if 'image' not in request.FILES:
                messages.error(request, 'Product image is required')
                return render(request, 'admin/product_form.html')

            # Create product with validated data
            product = Product.objects.create(
                name=request.POST['name'],
                description=request.POST['description'],
                price=request.POST['price'],
                category=request.POST['category'],
                clothing_type=request.POST['clothing_type'],
                image=request.FILES['image'],
                stock=int(request.POST['stock'])
            )
            messages.success(request, f'Product "{product.name}" created successfully')
            return redirect('admin_products')
            
        except Exception as e:
            messages.error(request, f'Error creating product: {str(e)}')
            return render(request, 'admin/product_form.html')
    
    # GET request - show empty form
    return render(request, 'admin/product_form.html')

@user_passes_test(is_admin)
def admin_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        try:
            # Validate required fields
            required_fields = ['name', 'description', 'price', 'category', 'clothing_type', 'stock']
            if not all(request.POST.get(field) for field in required_fields):
                messages.error(request, 'Please fill in all required fields')
                return render(request, 'admin/product_form.html', {'product': product})

            # Update product with validated data
            product.name = request.POST['name']
            product.description = request.POST['description']
            product.price = Decimal(request.POST['price'])
            product.category = request.POST['category']
            product.clothing_type = request.POST['clothing_type']
            product.stock = int(request.POST['stock'])
            
            # Handle image update if provided
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            messages.success(request, f'Product "{product.name}" updated successfully')
            return redirect('admin_products')
            
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
            return render(request, 'admin/product_form.html', {'product': product})
    
    # GET request - show form with product data
    return render(request, 'admin/product_form.html', {'product': product})

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test


@require_POST
@user_passes_test(is_admin)
def admin_product_delete_view(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        product_name = product.name
        product.delete()
        return JsonResponse({
            'success': True,
            'message': f'Product "{product_name}" has been deleted successfully.'
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@user_passes_test(is_admin)
def admin_orders(request):
    # Add filtering by status
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    orders = Order.objects.all()
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    if date_filter == 'today':
        orders = orders.filter(created_at__date=timezone.now().date())
    elif date_filter == 'week':
        orders = orders.filter(created_at__gte=timezone.now() - timedelta(days=7))
    elif date_filter == 'month':
        orders = orders.filter(created_at__gte=timezone.now() - timedelta(days=30))
    
    # Sort by latest first
    orders = orders.order_by('-created_at')
    
    # Add pagination
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get daily statistics
    today = timezone.now().date()
    todays_orders = Order.objects.filter(created_at__date=today)
    
    # Get monthly statistics
    first_day_of_month = today.replace(day=1)
    monthly_orders = Order.objects.filter(created_at__date__gte=first_day_of_month).count()
    monthly_sales = Order.objects.filter(
        created_at__date__gte=first_day_of_month,
        payment_status='completed'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'total_orders': todays_orders.count(),
        'total_sales': todays_orders.filter(payment_status='completed').aggregate(
            total=Sum('total_amount'))['total'] or 0,
        'monthly_orders': monthly_orders,
        'monthly_sales': monthly_sales,
        'order_statuses': Order.ORDER_STATUS,
        'pending_orders': todays_orders.filter(status='pending').count(),
    }
    return render(request, 'admin/orders.html', context)

@user_passes_test(is_admin)
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.ORDER_STATUS):
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.id} status updated successfully')
        else:
            messages.error(request, 'Invalid status')
    return redirect('admin_orders')
