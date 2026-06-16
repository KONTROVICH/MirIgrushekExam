from django.urls import path
from django.views.generic.base import RedirectView
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.user_login, name='login'),
    # Перенаправление для гостевого входа напрямую на каталог
    path('guest-login/', RedirectView.as_view(url='/catalog/', permanent=False), name='guest_login'),
    path('logout/', views.logout_view, name='logout'),
    path('catalog/', views.product_list, name='product_list'),
    path('catalog/ajax/', views.product_list_ajax, name='product_list_ajax'),
    path('catalog/product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('catalog/product/create/', views.product_create, name='product_create'),
    path('catalog/product/<int:product_id>/update/', views.product_update, name='product_update'),
    path('catalog/product/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('catalog/orders/', views.order_list, name='order_list'),
    path('catalog/order/create/', views.order_create, name='order_create'),
    path('catalog/order/<int:order_id>/update/', views.order_update, name='order_update'),
    path('catalog/order/<int:order_id>/delete/', views.order_delete, name='order_delete'),
]
