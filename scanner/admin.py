from django.contrib import admin
from .models import QRCode

# Register your models here.
@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'data', 'mobile_number')
