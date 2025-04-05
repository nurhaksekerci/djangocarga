from django import forms
from .models import (
    Currency, City, CustomUser, District, Neighborhood, OperationItem, Support, VehicleType, 
    BuyerCompany, Tour, NoVehicleTour, Transfer,
    Hotel, Museum, Activity, Guide, VehicleSupplier,
    ActivitySupplier, VehicleCost, ActivityCost, Operation,
    OperationCustomer, OperationSalesPrice, OperationSubItem
)
from django.core.cache import cache

# Select widget'ı için ortak sınıf
class SearchableSelect(forms.Select):
    def __init__(self, attrs=None, choices=()):
        default_attrs = {
            'class': 'w-full rounded-lg border border-[#e0e6ed] px-4 py-2 text-sm dark:border-[#1b2e4b] dark:bg-[#1b2e4b] dark:text-white-dark searchable-select'
        }
        attrs = attrs or {}
        attrs.update(default_attrs)
        super().__init__(attrs, choices)

class SearchableSelectMultiple(forms.SelectMultiple):
    def __init__(self, attrs=None, choices=()):
        default_attrs = {
            'class': 'selectize',
            'multiple': 'multiple'
        }
        if attrs is None:
            attrs = {}
        attrs.update(default_attrs)
        super().__init__(attrs, choices)

class DateInput(forms.DateInput):
    input_type = 'date'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'w-full rounded-lg border border-[#e0e6ed] px-4 py-2 text-sm dark:border-[#1b2e4b] dark:bg-[#1b2e4b] dark:text-white-dark'
        }
        attrs = attrs or {}
        attrs.update(default_attrs)
        super().__init__(attrs, format='%Y-%m-%d')

class CurrencyForm(forms.ModelForm):
    class Meta:
        model = Currency
        fields = ['code', 'name', 'symbol']
        labels = {
            'code': 'Para Birimi Kodu',
            'name': 'Para Birimi Adı',
            'symbol': 'Sembol'
        }

class CityForm(forms.ModelForm):
    class Meta:
        model = City
        fields = ['name', 'code']
        labels = {
            'name': 'Şehir Adı',
            'code': 'Şehir Kodu'
        }

class DistrictForm(forms.ModelForm):
    class Meta:
        model = District
        fields = ['name', 'city', 'code']
        labels = {
            'name': 'İlçe Adı',
            'city': 'Şehir',
            'code': 'İlçe Kodu'
        }
        widgets = {
            'city': SearchableSelect()
        }

class NeighborhoodForm(forms.ModelForm):
    class Meta:
        model = Neighborhood
        fields = ['name', 'district', 'code']
        labels = {
            'name': 'Mahalle Adı',
            'district': 'İlçe',
            'code': 'Mahalle Kodu'
        }
        widgets = {
            'district': SearchableSelect()
        }

class VehicleTypeForm(forms.ModelForm):
    class Meta:
        model = VehicleType
        fields = ['name']
        labels = {
            'name': 'Araç Tipi'
        }

class BuyerCompanyForm(forms.ModelForm):
    class Meta:
        model = BuyerCompany
        fields = ['name', 'short_name', 'contact']
        labels = {
            'name': 'Firma Adı',
            'short_name': 'Kısa Ad',
            'contact': 'İletişim'
        }

class TourForm(forms.ModelForm):
    class Meta:
        model = Tour
        fields = ['name', 'start_city', 'end_city']
        labels = {
            'name': 'Tur Adı',
            'start_city': 'Başlangıç Şehri',
            'end_city': 'Bitiş Şehri'
        }
        widgets = {
            'start_city': SearchableSelect(),
            'end_city': SearchableSelect()
        }

class NoVehicleTourForm(forms.ModelForm):
    class Meta:
        model = NoVehicleTour
        fields = ['name', 'city']
        labels = {
            'name': 'Tur Adı',
            'city': 'Şehir'
        }
        widgets = {
            'city': SearchableSelect()
        }

class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ['name', 'start_city', 'end_city']
        labels = {
            'name': 'Transfer Adı',
            'start_city': 'Başlangıç Şehri',
            'end_city': 'Bitiş Şehri'
        }
        widgets = {
            'start_city': SearchableSelect(),
            'end_city': SearchableSelect()
        }

# Yeni form sınıfları
class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = ['name', 'city', 'single_price', 'double_price', 'triple_price', 'currency', 'valid_until']
        labels = {
            'name': 'Otel Adı',
            'city': 'Şehir',
            'single_price': 'Tek Kişilik Oda Fiyatı',
            'double_price': 'Çift Kişilik Oda Fiyatı',
            'triple_price': 'Üç Kişilik Oda Fiyatı',
            'currency': 'Para Birimi',
            'valid_until': 'Geçerlilik Tarihi'
        }
        widgets = {
            'city': SearchableSelect(),
            'currency': SearchableSelect(),
            'valid_until': DateInput()
        }

class MuseumForm(forms.ModelForm):
    class Meta:
        model = Museum
        fields = ['name', 'city', 'local_price', 'foreign_price', 'currency', 'valid_until']
        labels = {
            'name': 'Müze Adı',
            'city': 'Şehir',
            'local_price': 'Yerli Fiyatı',
            'foreign_price': 'Yabancı Fiyatı',
            'currency': 'Para Birimi',
            'valid_until': 'Geçerlilik Tarihi'
        }
        widgets = {
            'city': SearchableSelect(),
            'currency': SearchableSelect(),
            'valid_until': DateInput()
        }

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['name', 'cities']
        labels = {
            'name': 'Aktivite Adı',
            'cities': 'Şehirler'
        }
        widgets = {
            'cities': SearchableSelectMultiple()
        }

class GuideForm(forms.ModelForm):
    class Meta:
        model = Guide
        fields = ['name', 'phone', 'document_no', 'cities']
        labels = {
            'name': 'Rehber Adı',
            'phone': 'Telefon',
            'document_no': 'Belge Numarası',
            'cities': 'Şehirler'
        }
        widgets = {
            'cities': SearchableSelectMultiple()
        }

class VehicleSupplierForm(forms.ModelForm):
    class Meta:
        model = VehicleSupplier
        fields = ['name', 'cities']
        labels = {
            'name': 'Tedarikçi Adı',
            'cities': 'Hizmet Verilen Şehirler'
        }
        widgets = {
            'cities': SearchableSelectMultiple()
        }

class ActivitySupplierForm(forms.ModelForm):
    class Meta:
        model = ActivitySupplier
        fields = ['name', 'cities']
        labels = {
            'name': 'Tedarikçi Adı',
            'cities': 'Hizmet Verilen Şehirler'
        }
        widgets = {
            'cities': SearchableSelectMultiple()
        }

class VehicleCostForm(forms.ModelForm):
    class Meta:
        model = VehicleCost
        fields = ['supplier', 'tour', 'transfer', 'car_cost', 'minivan_cost', 
                 'minibus_cost', 'midibus_cost', 'bus_cost', 'currency', 'valid_until']
        labels = {
            'supplier': 'Tedarikçi',
            'tour': 'Tur',
            'transfer': 'Transfer',
            'car_cost': 'Otomobil Ücreti',
            'minivan_cost': 'Minivan Ücreti',
            'minibus_cost': 'Minibüs Ücreti',
            'midibus_cost': 'Midibüs Ücreti',
            'bus_cost': 'Otobüs Ücreti',
            'currency': 'Para Birimi',
            'valid_until': 'Geçerlilik Tarihi'
        }
        widgets = {
            'supplier': SearchableSelect(),
            'tour': SearchableSelect(),
            'transfer': SearchableSelect(),
            'currency': SearchableSelect(),
            'valid_until': DateInput()
        }

class ActivityCostForm(forms.ModelForm):
    class Meta:
        model = ActivityCost
        fields = ['activity', 'supplier', 'price', 'currency', 'valid_until']
        labels = {
            'activity': 'Aktivite',
            'supplier': 'Tedarikçi',
            'price': 'Fiyat',
            'currency': 'Para Birimi',
            'valid_until': 'Geçerlilik Tarihi'
        }
        widgets = {
            'activity': SearchableSelect(),
            'supplier': SearchableSelect(),
            'currency': SearchableSelect(),
            'valid_until': DateInput()
        }

class BaseOperationForm(forms.ModelForm):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Önbellekten seçenekleri al
        form_choices = cache.get('form_choices')
        if form_choices:
            # Form alanlarını önbellekten gelen verilerle doldur
            for field_name, field in self.fields.items():
                if field_name in form_choices:
                    # Eğer alan bir ModelChoiceField ise
                    if isinstance(field, forms.ModelChoiceField):
                        field.queryset = form_choices[field_name]
                    # Eğer alan bir ModelMultipleChoiceField ise
                    elif isinstance(field, forms.ModelMultipleChoiceField):
                        field.queryset = form_choices[field_name]
                    # Eğer alan bir ChoiceField ise
                    elif isinstance(field, forms.ChoiceField):
                        field.choices = form_choices[field_name]
                    # Currency alanları için varsayılan değer ayarla
                    if field_name == 'currency' and form_choices[field_name]:
                        field.initial = form_choices[field_name][0]

class OperationSubItemForm(BaseOperationForm):
    class Meta:
        abstract = True
        ordering = ['sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']


class OperationSubItemTourForm(OperationSubItemForm):
    class Meta:
        model = OperationSubItem
        fields = ['ordering', 'tour', 'sales_currency', 'sales_price', 'cost_currency', 'cost_price', 'notes']
        ordering = ['ordering', 'tour', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']

class OperationSubItemTransferForm(OperationSubItemForm):
    class Meta:
        model = OperationSubItem
        fields = ['ordering', 'transfer', 'sales_currency', 'sales_price', 'cost_currency', 'cost_price', 'notes']
        ordering = ['ordering', 'transfer', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']

class OperationSubItemMuseumForm(OperationSubItemForm):
    class Meta:
        model = OperationSubItem
        fields = ['ordering', 'museums', 'sales_currency', 'sales_price', 'cost_currency', 'cost_price', 'notes']
        ordering = ['ordering', 'museums', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']

class OperationSubItemHotelForm(OperationSubItemForm):
    class Meta:
        model = OperationSubItem
        fields = ['ordering', 'hotel', 'room_type', 'sales_currency', 'sales_price', 'cost_currency', 'cost_price', 'notes']
        ordering = ['ordering', 'hotel', 'room_type', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']

class OperationSubItemGuideForm(OperationSubItemForm):
    class Meta:
        model = OperationSubItem
        fields = ['ordering', 'is_guide', 'guide', 'sales_currency', 'sales_price', 'cost_currency', 'cost_price', 'notes']
        ordering = ['ordering', 'is_guide', 'guide', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']

class OperationSubItemActivityForm(OperationSubItemForm):
    class Meta:
        model = OperationSubItem
        fields = ['ordering', 'activity', 'activity_supplier', 'sales_currency', 'sales_price', 'cost_currency', 'cost_price', 'notes']
        ordering = ['ordering', 'activity', 'activity_supplier', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']

class OperationSubItemOtherForm(OperationSubItemForm):
    class Meta:
        model = OperationSubItem
        fields = ['ordering', 'other_price_description', 'sales_currency', 'sales_price', 'cost_currency', 'cost_price', 'notes']
        ordering = ['ordering', 'other_price_description', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']

class OperationItemVehicleForm(BaseOperationForm):
    class Meta:
        model = OperationItem
        fields = [
            'pick_time', 'pick_up_location', 'drop_off_location',
            'vehicle_type', 'vehicle_supplier', 'driver_name',
            'driver_phone', 'vehicle_plate_no', 'sales_price',
            'sales_currency', 'cost_price', 'cost_currency', 'notes'
        ]
        ordering = ['pick_time', 'pick_up_location', 'drop_off_location', 'vehicle_type', 'vehicle_supplier', 'driver_name', 'driver_phone', 'vehicle_plate_no', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']
        widgets = {
            'pick_time': forms.TimeInput(attrs={'type': 'time'}),
        }
class OperationItemNoVehicleTourForm(BaseOperationForm):
    class Meta:
        model = OperationItem
        fields = [
            'pick_time', 'pick_up_location', 'drop_off_location',
            'no_vehicle_tour', 'sales_price', 'sales_currency',
            'cost_price', 'cost_currency', 'notes'
        ]
        ordering = ['pick_time', 'pick_up_location', 'drop_off_location', 'no_vehicle_tour', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']
        widgets = {
            'pick_time': forms.TimeInput(attrs={'type': 'time'}),
        }
class OperationItemActivityForm(BaseOperationForm):
    class Meta:
        model = OperationItem
        fields = [
            'pick_time', 'pick_up_location', 'drop_off_location',
            'no_vehicle_activity', 'activity_supplier', 'sales_price',
            'sales_currency', 'cost_price', 'cost_currency', 'notes'
        ]
        ordering = ['pick_time', 'pick_up_location', 'drop_off_location', 'no_vehicle_activity', 'activity_supplier', 'sales_price', 'sales_currency', 'cost_price', 'cost_currency', 'notes']
        widgets = {
            'pick_time': forms.TimeInput(attrs={'type': 'time'}),
        }
class OperationCustomerForm(forms.ModelForm):
    class Meta:
        model = OperationCustomer
        fields = [
            'first_name', 'last_name', 'customer_type',
            'birth_date', 'passport_no', 'contact_info',
            'notes'
        ]
        widgets = {
            'birth_date': DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_info': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telefon numarası veya e-posta adresi'
            })
        }
        labels = {
            'first_name': 'Ad',
            'last_name': 'Soyad',
            'customer_type': 'Müşteri Tipi',
            'birth_date': 'Doğum Tarihi',
            'passport_no': 'Pasaport No',
            'contact_info': 'İletişim Bilgisi',
            'notes': 'Notlar'
        }

class OperationSalesPriceForm(forms.ModelForm):
    class Meta:
        model = OperationSalesPrice
        fields = ['price', 'currency']
        labels = {
            'price': 'Fiyat',
            'currency': 'Para Birimi'
        }
        widgets = {
            'currency': SearchableSelect(),
            'price': forms.NumberInput(attrs={
                'class': 'w-full rounded-lg border border-[#e0e6ed] px-4 py-2 text-sm dark:border-[#1b2e4b] dark:bg-[#1b2e4b] dark:text-white-dark',
                'step': '0.01'
            })
        }

class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ['reference_number', 'buyer_company', 'follow_by', 'start_date', 'end_date', 'notes']
        labels = {
            'reference_number': 'Referans Numarası',
            'buyer_company': 'Alıcı Firma',
            'follow_by': 'Takip Eden',
            'start_date': 'Başlangıç Tarihi',
            'end_date': 'Bitiş Tarihi',
            'notes': 'Notlar'
        }
        widgets = {
            'buyer_company': SearchableSelect(),
            'start_date': DateInput(),
            'end_date': DateInput(),
            'notes': forms.Textarea(attrs={
                'class': 'w-full rounded-lg border border-[#e0e6ed] px-4 py-2 text-sm dark:border-[#1b2e4b] dark:bg-[#1b2e4b] dark:text-white-dark',
                'rows': 3
            })
        }





class SendSmsForm(forms.Form):
    users = forms.ModelChoiceField(queryset=CustomUser.objects.filter(is_active=True, phone__isnull=False), label='Kullanıcı')
    message = forms.CharField(label='Mesaj', widget=forms.Textarea)



class SupportForm(forms.ModelForm):
    class Meta:
        model = Support
        fields = ['subject', 'message']



