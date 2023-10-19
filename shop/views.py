from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DeleteView

from shop.models import Product, Order, OrderItem


class ProductsListView(ListView):
    model = Product
    template_name = 'shop/shop.html'

@login_required(login_url=reverse_lazy('login'))
def add_item_to_cart(request, pk):
    if request.method == 'POST':
        cart = Order.get_cart(request.user)
        product = get_object_or_404(Product, pk=pk)
        cart.orderitem_set.create(product=product,
                                  quantity=1,
                                  price=product.price)
        cart.save()
        return redirect('cart-view')
    return redirect('shop')

@login_required(login_url=reverse_lazy('login'))
def cart_view(request):
    cart = Order.get_cart(request.user)
    items = cart.orderitem_set.all()
    context = {
        'cart': cart,
        'items': items,
    }
    return render(request, 'shop/cart.html', context)

@method_decorator(login_required, name='dispatch')
class CartDeleteItem(DeleteView):
    model = OrderItem
    template_name = 'shop/cart.html'
    success_url = reverse_lazy('cart-view')

    def get_queryset(self):
        qs = super().get_queryset()
        qs.filter(order__user=self.request.user)
        return qs

@login_required(login_url=reverse_lazy('login'))
def make_order(request):
    cart = Order.get_cart(request.user)
    cart.make_order()
    return redirect('shop')
