from django.shortcuts import render
from django.views.generic import ListView

from shop.models import Product


class ProductsListView(ListView):
    model = Product
    template_name = 'shop/shop.html'
