from django.contrib import admin
from .models import ShippingAddress, OrderItem, Order


# Register the model on the admin section thing
admin.site.register(ShippingAddress)
admin.site.register(OrderItem)
admin.site.register(Order)


