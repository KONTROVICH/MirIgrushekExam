from django.contrib import admin
from .models import User, Category, Supplier, Manufacturer, Product, PickupPoint, Order, OrderItem

admin.site.register(User)
admin.site.register(Category)
admin.site.register(Supplier)
admin.site.register(Manufacturer)
admin.site.register(Product)
admin.site.register(PickupPoint)
admin.site.register(Order)
admin.site.register(OrderItem)
