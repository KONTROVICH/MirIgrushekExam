from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Product, Category, Supplier, Manufacturer, Order, OrderItem
import json

from .forms import ProductForm, OrderForm

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_manager_or_admin(user):
    return user.is_authenticated and user.role in ['manager', 'admin']

def guest_login(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            return redirect('catalog:product_list')
        from .models import User
        guest_user, created = User.objects.get_or_create(
            username='guest',
            defaults={'role': 'guest'},
        )
        if created:
            guest_user.set_password('guestpassword123')
            guest_user.save()
        login(request, guest_user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('catalog:product_list')
    return redirect('catalog:login')

def user_login(request):
    if request.user.is_authenticated:
        return redirect('catalog:product_list')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('catalog:product_list')
        return render(request, 'registration/login.html', {'error': 'Неверный логин или пароль.'})
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('catalog:login')

@login_required
def product_list(request):
    products = Product.objects.select_related(
        'category', 'supplier', 'manufacturer'
    ).all()

    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    manufacturers = Manufacturer.objects.all()

    user_role = getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'

    context = {
        'products': products,
        'categories': categories,
        'suppliers': suppliers,
        'manufacturers': manufacturers,
        'user_role': user_role,
    }
    return render(request, 'catalog/product_list.html', context)

@login_required
def product_list_ajax(request):
    products = Product.objects.select_related(
        'category', 'supplier', 'manufacturer'
    ).all()

    search = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '').strip()
    supplier_id = request.GET.get('supplier', '').strip()
    manufacturer_id = request.GET.get('manufacturer', '').strip()
    sort_by = request.GET.get('sort', '').strip()

    if search:
        products = products.filter(name__icontains=search)

    if category_id:
        products = products.filter(category_id=category_id)

    if supplier_id:
        products = products.filter(supplier_id=supplier_id)

    if manufacturer_id:
        products = products.filter(manufacturer_id=manufacturer_id)

    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'name':
        products = products.order_by('name')
    elif sort_by == 'discount':
        products = products.order_by('-discount')

    data = []
    for product in products:
        data.append({
            'id': product.id,
            'article': product.article,
            'name': product.name,
            'unit': product.unit,
            'price': str(product.price),
            'discount': product.discount,
            'discounted_price': product.discounted_price(),
            'stock_quantity': product.stock_quantity,
            'description': product.description,
            'image_url': product.image.url if product.image else '/static/picture.png',
            'category': product.category.name,
            'supplier': product.supplier.name,
            'manufacturer': product.manufacturer.name,
        })

    return JsonResponse({'products': data, 'user_role': getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'})

def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    user_role = getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'
    return render(request, 'catalog/product_detail.html', {'product': product, 'user_role': user_role})

@login_required
@user_passes_test(is_admin)
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('catalog:product_list')
    else:
        form = ProductForm()
    user_role = getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'
    return render(request, 'catalog/product_form.html', {'form': form, 'form_title': 'Добавление товара', 'user_role': user_role})

@login_required
@user_passes_test(is_admin)
def product_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('catalog:product_list')
    else:
        form = ProductForm(instance=product)
    user_role = getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'
    return render(request, 'catalog/product_form.html', {'form': form, 'form_title': 'Редактирование товара', 'user_role': user_role})

@login_required
@user_passes_test(is_admin)
def product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    try:
        if OrderItem.objects.filter(product=product).exists():
            return render(request, 'catalog/product_confirm_delete.html', {
                'product': product,
                'error': 'Невозможно удалить товар, так как он присутствует в заказах.',
            })
        product.delete()
        return redirect('catalog:product_list')
    except Exception:
        return render(request, 'catalog/product_confirm_delete.html', {
            'product': product,
            'error': 'Ошибка при удалении товара.',
        })

@login_required
@user_passes_test(is_manager_or_admin)
def order_list(request):
    orders = Order.objects.all().order_by('-order_date')
    user_role = getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'
    return render(request, 'orders/order_list.html', {'orders': orders, 'user_role': user_role})

@login_required
@user_passes_test(is_admin)
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('catalog:order_list')
    else:
        form = OrderForm()
    user_role = getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'
    return render(request, 'orders/order_form.html', {'form': form, 'form_title': 'Создание заказа', 'user_role': user_role})

@login_required
@user_passes_test(is_admin)
def order_update(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('catalog:order_list')
    else:
        form = OrderForm(instance=order)
    user_role = getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'
    return render(request, 'orders/order_form.html', {'form': form, 'form_title': 'Редактирование заказа', 'user_role': user_role})

@login_required
@user_passes_test(is_admin)
def order_delete(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == 'POST':
        order.delete()
        return redirect('catalog:order_list')
    user_role = getattr(request.user, 'role', 'guest') if request.user.is_authenticated else 'guest'
    return render(request, 'orders/order_confirm_delete.html', {'order': order, 'user_role': user_role})
