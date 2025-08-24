from django.contrib import admin
from .models import Slider

@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ['title', 'subtitle', 'status', 'order', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'subtitle', 'description']
    list_editable = ['status', 'order']
    ordering = ['order', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'subtitle', 'description')
        }),
        ('Media & Links', {
            'fields': ('img', 'link')
        }),
        ('Settings', {
            'fields': ('status', 'order')
        }),
    )
