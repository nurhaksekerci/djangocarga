from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    CustomUser, Currency, City, District, Neighborhood, VehicleType,
    BuyerCompany, Tour, NoVehicleTour, Transfer, Hotel, Museum,
    Activity, Guide, VehicleSupplier, ActivitySupplier, VehicleCost,
    ActivityCost, HotelPriceHistory, MuseumPriceHistory,
    VehicleCostHistory, ActivityCostHistory, Operation,
    OperationCustomer, OperationSalesPrice, OperationDay,
    OperationItem, OperationSubItem
)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol')
    search_fields = ('code', 'name')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'code')
    list_filter = ('city',)
    search_fields = ('name', 'code')

@admin.register(Neighborhood)
class NeighborhoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'district', 'code')
    list_filter = ('district__city', 'district')
    search_fields = ('name', 'code')

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)

@admin.register(BuyerCompany)
class BuyerCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'contact', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'short_name', 'contact')

@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_city', 'end_city', 'is_active')
    list_filter = ('is_active', 'start_city', 'end_city')
    search_fields = ('name',)

@admin.register(NoVehicleTour)
class NoVehicleTourAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'is_active')
    list_filter = ('is_active', 'city')
    search_fields = ('name',)

@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_city', 'end_city', 'is_active')
    list_filter = ('is_active', 'start_city', 'end_city')
    search_fields = ('name',)

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'currency', 'valid_until', 'is_active')
    list_filter = ('is_active', 'city', 'currency')
    search_fields = ('name',)
    date_hierarchy = 'valid_until'

@admin.register(Museum)
class MuseumAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'currency', 'valid_until', 'is_active')
    list_filter = ('is_active', 'city', 'currency')
    search_fields = ('name',)
    date_hierarchy = 'valid_until'

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('cities',)

@admin.register(Guide)
class GuideAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'document_no', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone', 'document_no')
    filter_horizontal = ('cities',)

@admin.register(VehicleSupplier)
class VehicleSupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('cities',)

@admin.register(ActivitySupplier)
class ActivitySupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('cities',)

@admin.register(VehicleCost)
class VehicleCostAdmin(admin.ModelAdmin):
    list_display = ('supplier', 'tour', 'transfer', 'currency', 'valid_until', 'is_active')
    list_filter = ('is_active', 'supplier', 'currency')
    search_fields = ('supplier__name', 'tour__name', 'transfer__name')
    date_hierarchy = 'valid_until'

@admin.register(ActivityCost)
class ActivityCostAdmin(admin.ModelAdmin):
    list_display = ('activity', 'supplier', 'currency', 'valid_until', 'is_active')
    list_filter = ('is_active', 'activity', 'supplier', 'currency')
    search_fields = ('activity__name', 'supplier__name')
    date_hierarchy = 'valid_until'

@admin.register(HotelPriceHistory)
class HotelPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('hotel', 'currency', 'valid_from', 'valid_until', 'is_active')
    list_filter = ('is_active', 'hotel', 'currency')
    search_fields = ('hotel__name',)
    date_hierarchy = 'valid_from'

@admin.register(MuseumPriceHistory)
class MuseumPriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('museum', 'currency', 'valid_from', 'valid_until', 'is_active')
    list_filter = ('is_active', 'museum', 'currency')
    search_fields = ('museum__name',)
    date_hierarchy = 'valid_from'

@admin.register(VehicleCostHistory)
class VehicleCostHistoryAdmin(admin.ModelAdmin):
    list_display = ('vehicle_cost', 'currency', 'valid_from', 'valid_until', 'is_active')
    list_filter = ('is_active', 'vehicle_cost__supplier', 'currency')
    search_fields = ('vehicle_cost__supplier__name',)
    date_hierarchy = 'valid_from'

@admin.register(ActivityCostHistory)
class ActivityCostHistoryAdmin(admin.ModelAdmin):
    list_display = ('activity_cost', 'currency', 'valid_from', 'valid_until', 'is_active')
    list_filter = ('is_active', 'activity_cost__activity', 'currency')
    search_fields = ('activity_cost__activity__name',)
    date_hierarchy = 'valid_from'

@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('reference_number', 'buyer_company', 'start_date', 'end_date', 'status', 'total_pax', 'is_active')
    list_filter = ('is_active', 'status', 'buyer_company', 'created_by', 'follow_by')
    search_fields = ('reference_number', 'buyer_company__name', 'notes')
    date_hierarchy = 'start_date'

@admin.register(OperationCustomer)
class OperationCustomerAdmin(admin.ModelAdmin):
    list_display = ('operation', 'first_name', 'last_name', 'customer_type', 'is_buyer', 'is_active')
    list_filter = ('is_active', 'customer_type', 'is_buyer', 'operation__status')
    search_fields = ('first_name', 'last_name', 'passport_no', 'operation__reference_number')

@admin.register(OperationSalesPrice)
class OperationSalesPriceAdmin(admin.ModelAdmin):
    list_display = ('operation', 'price', 'currency', 'is_active')
    list_filter = ('is_active', 'currency')
    search_fields = ('operation__reference_number',)

@admin.register(OperationDay)
class OperationDayAdmin(admin.ModelAdmin):
    list_display = ('operation', 'date', 'is_active')
    list_filter = ('is_active', 'operation__status')
    search_fields = ('operation__reference_number',)
    date_hierarchy = 'date'

@admin.register(OperationItem)
class OperationItemAdmin(admin.ModelAdmin):
    list_display = ('operation_day', 'item_type', 'pick_time', 'is_active')
    list_filter = ('is_active', 'item_type', 'operation_day__operation__status')
    search_fields = ('operation_day__operation__reference_number', 'notes')

@admin.register(OperationSubItem)
class OperationSubItemAdmin(admin.ModelAdmin):
    list_display = ('operation_item', 'ordering', 'subitem_type', 'is_active')
    list_filter = ('is_active', 'subitem_type', 'operation_item__item_type')
    search_fields = ('operation_item__operation_day__operation__reference_number', 'notes')
    filter_horizontal = ('museums',)
