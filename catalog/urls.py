from django.urls import path
from .views import (
    HomeView, PayementView, ProductDetail, add_to_cart, checkout_cancel, checkout_success, generate_invoice, remove_from_cart, 
    decrease_quantity, get_cart_total, order_summary, checkout, 
    product_view, create_checkout_session
)

urlpatterns = [
    path('', HomeView.as_view(), name='homepage'),
    path('product/<slug:slug>/', ProductDetail.as_view(), name='product_detail'),
    path('add_to_cart/<slug:slug>/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<slug:slug>/', remove_from_cart, name='remove_from_cart'),
    path('checkout/', checkout, name='checkout'),
    path('order-summary/', order_summary, name='order_summary'),
    path('decrease/<int:item_id>/', decrease_quantity, name='decrease_quantity'),
    path('get_cart_total/', get_cart_total, name='get_cart_total'),
    path('product/', product_view, name='product_list'),
    path('create-checkout-session/', create_checkout_session, name='create_checkout_session'),
    path('invoice/<int:order_id>/', generate_invoice, name='generate_invoice'),
    path('checkout-success/', checkout_success, name='checkout_success'),
    path('checkout-cancel/', checkout_cancel, name='checkout_cancel'),
    path('payment/<payment_option>/', PayementView.as_view(), name='payment'),
    
]


