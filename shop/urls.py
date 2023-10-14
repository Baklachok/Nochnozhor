from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView

from shop import views

urlpatterns = [
    path('', views.ProductsListView.as_view(), name='shop'),
    path('cart_view/', TemplateView.as_view(template_name='shop/cart.html'), name='cart-view'),
]