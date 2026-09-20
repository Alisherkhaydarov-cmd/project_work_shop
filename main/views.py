from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Category, Product, Review
from .forms import CommentForm


def home(request):
    categories = Category.objects.all()
    products = Product.objects.all()[:8]
    return render(request, 'main/home.html', {'categories': categories, 'products': products})


def product_list(request, category_id=None):
    products = Product.objects.select_related('category').all()
    category = None
    if category_id:
        category = get_object_or_404(Category, pk=category_id)
        products = products.filter(category=category)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(Q(name__icontains=query))

    return render(request, 'main/product_list.html', {
        'products': products,
        'categories': Category.objects.all(),
        'category': category,
        'query': query,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = CommentForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, 'Отзыв добавлен.')
            return redirect('product_detail', product_id=product.id)
    else:
        form = CommentForm()

    reviews = product.reviews.select_related('user').all()

    return render(request, 'main/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'form': form,
    })