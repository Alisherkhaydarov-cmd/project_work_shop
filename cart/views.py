from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from main.models import Product
from .forms import OrderForm
from .models import Cart, CartItem, Order, OrderItem


def get_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart

@login_required
def cart_detail(request):
    cart = get_cart(request.user)
    return render(request, 'cart/cart.html', {'cart': cart, 'items': cart.items.select_related('product')})

@login_required
def add_to_cart(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)
    product = get_object_or_404(Product, pk=product_id)
    if product.quantity < 1:
        messages.error(request, 'Товар закончился.')
        return redirect('product_detail', product_id=product.id)
    cart = get_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if item.quantity < product.quantity:
            item.quantity += 1
            item.save()
        else:
            messages.error(request, 'Нельзя добавить больше товара, чем есть на складе.')
            return redirect('cart_detail')
    messages.success(request, 'Товар добавлен в корзину.')
    return redirect('cart_detail')

@login_required
def update_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except ValueError:
            quantity = 1
        if 1 <= quantity <= item.product.quantity:
            item.quantity = quantity
            item.save()
        else:
            messages.error(request, 'Некорректное количество.')
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    if request.method == 'POST':
        item.delete()
    return redirect('cart_detail')

@login_required
def checkout(request):
    cart = get_cart(request.user)
    items = list(cart.items.select_related('product'))
    if not items:
        messages.error(request, 'Корзина пуста.')
        return redirect('cart_detail')

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                for item in items:
                    if item.quantity > item.product.quantity:
                        messages.error(request, f'Недостаточно товара: {item.product.name}')
                        return redirect('cart_detail')
                order = form.save(commit=False)
                order.user = request.user
                order.total = cart.total_price()
                order.save()
                for item in items:
                    OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
                    item.product.quantity -= item.quantity
                    item.product.save(update_fields=['quantity'])
                cart.items.all().delete()
            messages.success(request, f'Заказ #{order.id} оформлен.')
            return redirect('order_success', order_id=order.id)
    else:
        form = OrderForm(initial={'name': request.user.get_full_name()})

    return render(request, 'cart/checkout.html', {'form': form, 'cart': cart, 'items': items})

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'cart/success.html', {'order': order})
