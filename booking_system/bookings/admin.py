from django.contrib import admin
from .models import Category, Service, TimeSlot, Booking, Review

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration']
    list_filter = ['category']
    search_fields = ['name']

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['date', 'start_time', 'end_time', 'is_available', 'is_blocked']
    list_filter = ['date', 'is_available', 'is_blocked']
    ordering = ['date', 'start_time']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'service', 'time_slot', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'service']
    search_fields = ['user__username', 'service__name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['booking', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']