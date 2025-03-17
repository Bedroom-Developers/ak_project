from django.contrib import admin
from .models import CustomUser, Items, Requests, Details, RequestsItems
# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Items)
admin.site.register(Requests)
admin.site.register(Details)
admin.site.register(RequestsItems)

