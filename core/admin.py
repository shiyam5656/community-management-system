from django.contrib import admin
from .models import Community, Property, Announcement
from .models import Fee, Payment

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'created_at')
    search_fields = ('name',)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('unit_number', 'owner_name', 'monthly_fee', 'status')
    list_filter = ('status',)
    search_fields = ('unit_number', 'owner_name')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_emergency', 'created_at', 'created_by')
    list_filter = ('category', 'is_emergency')
    search_fields = ('title',)


from django.contrib import admin

# Register your models here.
@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('property', 'amount', 'due_date', 'status')
    list_filter = ('status', 'due_date')
    search_fields = ('property__unit_number',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('fee', 'amount', 'payment_date', 'method', 'receipt_number')
    list_filter = ('method', 'payment_date')

from .models import ParkingSpot

@admin.register(ParkingSpot)
class ParkingSpotAdmin(admin.ModelAdmin):
    list_display = ('spot_number', 'property', 'is_covered', 'is_reserved')
    list_filter = ('is_covered', 'is_reserved')
    search_fields = ('spot_number',)