from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from django.core.cache import cache
from django.db.models import Prefetch
from django.db.models.functions import Coalesce
from django import forms
from django.forms import ModelChoiceField, ModelMultipleChoiceField, ChoiceField
from tour.services import sms
from tour.models import (
    CustomUser, Operation, OperationCustomer, OperationDay, 
    OperationItem, OperationSalesPrice, OperationSubItem, 
    Currency, City, District, Neighborhood, VehicleType, 
    BuyerCompany, Tour, NoVehicleTour, Transfer, Hotel, 
    Museum, Activity, Guide, VehicleSupplier, ActivitySupplier
)

from .services import LoginService, PasswordResetService, sms
from .forms import (
    CurrencyForm, CityForm, DistrictForm, NeighborhoodForm, 
    OperationItemActivityForm, OperationItemNoVehicleTourForm, 
    OperationItemVehicleForm, OperationSubItemActivityForm, 
    OperationSubItemGuideForm, OperationSubItemHotelForm, 
    OperationSubItemMuseumForm, OperationSubItemOtherForm, 
    OperationSubItemTourForm, OperationSubItemTransferForm, SendSmsForm,
    VehicleTypeForm, BuyerCompanyForm, TourForm, NoVehicleTourForm, 
    TransferForm, HotelForm, MuseumForm, ActivityForm, GuideForm, 
    VehicleSupplierForm, ActivitySupplierForm, VehicleCostForm, 
    ActivityCostForm, OperationForm, OperationCustomerForm, 
    OperationSalesPriceForm
)

from datetime import datetime
from django.utils import timezone

def password_reset_request(request):
    """Parola sıfırlama kodu gönderme sayfası"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        user = CustomUser.objects.get(phone=phone)
        if not user:
            messages.error(request, _('Bu telefon numarasına sahip bir kullanıcı bulunamadı.'))
            return render(request, 'tour/password-reset.html')
        success, message = PasswordResetService.send_reset_code(phone)
        
        if success:
            messages.success(request, message)
            return redirect('password_reset_verify', phone=phone)
        else:
            messages.error(request, message)
    
    return render(request, 'tour/password-reset.html')

def password_reset_verify(request, phone):
    """Parola sıfırlama kodunu doğrulama sayfası"""
    try:
        user = CustomUser.objects.get(phone=phone)
        if request.method == 'POST':
            code = request.POST.get('code')
            new_password = request.POST.get('password1')
            new_password2 = request.POST.get('password2')
            
            if not code:
                messages.error(request, _('Lütfen doğrulama kodunu girin.'))
                return render(request, 'tour/password_reset_verify.html', {'user': user})
            
            if not new_password or not new_password2:
                messages.error(request, _('Lütfen yeni parolanızı girin.'))
                return render(request, 'tour/password_reset_verify.html', {'user': user})
            
            if new_password != new_password2:
                messages.error(request, _('Parolalar eşleşmiyor.'))
                return render(request, 'tour/password_reset_verify.html', {'user': user})
            
            if len(new_password) < 8:
                messages.error(request, _('Parola en az 8 karakter olmalıdır.'))
                return render(request, 'tour/password_reset_verify.html', {'user': user})
            
            success, message = PasswordResetService.reset_password(user.phone, code, new_password)
            
            if success:
                messages.success(request, message)
                return redirect('login')
            else:
                messages.error(request, message)
        
        return render(request, 'tour/password_reset_verify.html', {'user': user})
    except CustomUser.DoesNotExist:
        messages.error(request, _('Kullanıcı bulunamadı.'))
        return redirect('password_reset_request')


# Create your views here.
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = LoginService.authenticate_user(username, password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, _('Başarıyla giriş yaptınız.'))   
                # Kullanıcı rolüne göre yönlendirme
                if user.role == 'admin':
                    return redirect('admin:index')
                elif user.role == 'company_admin':
                    return redirect('company_dashboard')
                elif user.role == 'manager':
                    return redirect('manager_dashboard')
                elif user.role == 'operation_chief':
                    return redirect('operation_chief_dashboard')
                elif user.role == 'operation_staff':
                    return redirect('operation_staff_dashboard')
                elif user.role == 'accounting':
                    return redirect('accounting_dashboard')
            else:
                messages.error(request, _('Hesabınız aktif değil. Lütfen yönetici ile iletişime geçin.'))
        else:
            messages.error(request, _('Geçersiz kullanıcı adı veya şifre.'))
    
    return render(request, 'tour/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, _('Başarıyla çıkış yaptınız.'))
    return redirect('login')


def generic_list_view(request, model):
    try:
        model_class = apps.get_model(app_label="tour", model_name=model)
        objects = model_class.objects.all()
        
        # Form sınıfını belirle
        form_classes = {
            'Currency': CurrencyForm,
            'VehicleType': VehicleTypeForm,
            'BuyerCompany': BuyerCompanyForm,
            'Tour': TourForm,
            'NoVehicleTour': NoVehicleTourForm,
            'Transfer': TransferForm,
            'Hotel': HotelForm,
            'Museum': MuseumForm,
            'Activity': ActivityForm,
            'Guide': GuideForm,
            'VehicleSupplier': VehicleSupplierForm,
            'ActivitySupplier': ActivitySupplierForm,
            'VehicleCost': VehicleCostForm,
            'ActivityCost': ActivityCostForm,
        }
        
        form_class = form_classes.get(model)
        if not form_class:
            raise ValueError(f'Form sınıfı bulunamadı: {model}')
            
        if request.method == 'POST':
            form = form_class(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Kayıt başarıyla eklendi.')
                return redirect('tour:list', model=model)
        else:
            form = form_class()
            
        context = {
            'items': objects,
            'page_title': f'{model} Listesi',
            'model': model,
            'form': form
        }
        return render(request, 'includes/list.html', context)
        
    except (LookupError, ValueError) as e:
        messages.error(request, f'Model bulunamadı: {str(e)}')
        return render(request, 'tour/error.html', {'error': 'Model bulunamadı'})


def generic_update_view(request, model, pk):
    try:
        model_class = apps.get_model(app_label="tour", model_name=model)
        object = model_class.objects.get(id=pk)
        
        # Form sınıfını belirle
        form_classes = {
            'Currency': CurrencyForm,
            'VehicleType': VehicleTypeForm,
            'BuyerCompany': BuyerCompanyForm,
            'Tour': TourForm,
            'NoVehicleTour': NoVehicleTourForm,
            'Transfer': TransferForm,
            'Hotel': HotelForm,
            'Museum': MuseumForm,
            'Activity': ActivityForm,
            'Guide': GuideForm,
            'VehicleSupplier': VehicleSupplierForm,
            'ActivitySupplier': ActivitySupplierForm,
            'VehicleCost': VehicleCostForm,
        }
        
        form_class = form_classes.get(model)
        if not form_class:
            raise ValueError(f'Form sınıfı bulunamadı: {model}')
            
        if request.method == 'POST':
            form = form_class(request.POST, instance=object)
            if form.is_valid():
                form.save()
                messages.success(request, 'Kayıt başarıyla güncellendi.')
                return redirect('tour:list', model=model)
        else:
            form = form_class(instance=object)  
            
        context = {
            'item': object,
            'page_title': f'{model} Düzenle',
            'model': model,
            'form': form
        }
        return render(request, 'includes/update_form.html', context)
        
    except (LookupError, ValueError) as e:
        messages.error(request, f'Model bulunamadı: {str(e)}')
        return render(request, 'tour/error.html', {'error': 'Model bulunamadı'})


def generic_delete_view(request, model, pk):
    try:
        # Model sınıfını al
        model_class = apps.get_model(app_label="tour", model_name=model)
        # Nesneyi bul
        obj = get_object_or_404(model_class, pk=pk)
        
        # Nesneyi sil
        obj.delete()
        messages.success(request, 'Kayıt başarıyla silindi.')
        
        # Liste sayfasına yönlendir
        return redirect('tour:list', model=model)
        
    except (LookupError, ValueError) as e:
        messages.error(request, f'Model bulunamadı: {str(e)}')
        return render(request, 'tour/error.html', {'error': 'Model bulunamadı'})
    except Exception as e:
        messages.error(request, f'Bir hata oluştu: {str(e)}')
        return render(request, 'tour/error.html', {'error': 'Bir hata oluştu'})





def create_operation(request):
    if request.method == 'POST':
        form = OperationForm(request.POST)
        if form.is_valid():
            operation = form.save(commit=False)
            operation.created_by = request.user
            operation.save()
            messages.success(request, 'İşlem başarıyla oluşturuldu.')
            return redirect('tour:create_operation_customer', operation_id=operation.id)
    else:
        form = OperationForm()
    return render(request, 'operation/create_operation.html', {'form': form, 'page_title': 'Operasyon Oluştur'})

def create_operation_customer(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    customers = OperationCustomer.objects.filter(operation=operation)
    if request.method == 'POST':
        form = OperationCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.operation = operation
            customer.save()
            messages.success(request, 'Müşteri başarıyla oluşturuldu.')
            return redirect('tour:create_operation_customer', operation_id=operation_id)
    else:
        form = OperationCustomerForm()
    return render(request, 'operation/create_customer.html', {'form': form, 'operation': operation, 'customers': customers, 'page_title': 'Müşteri Oluştur'})

def create_operation_sales_price(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    customers = OperationCustomer.objects.filter(operation=operation)
    sales_prices = OperationSalesPrice.objects.filter(operation=operation)
    if request.method == 'POST':
        form = OperationSalesPriceForm(request.POST)
        if form.is_valid():
            sales_price = form.save(commit=False)
            sales_price.operation = operation
            sales_price.save() 
            messages.success(request, 'Satış fiyatı başarıyla oluşturuldu.')
            return redirect('tour:create_operation_sales_price', operation_id=operation_id)
    else:
        form = OperationSalesPriceForm()
    return render(request, 'operation/create_sales_price.html', {'form': form, 'operation': operation, 'customers': customers, 'sales_prices': sales_prices, 'page_title': 'Satış Fiyatı Oluştur'})

def create_operation_item(request, operation_id):
    # Ana operasyon verisini al
    operation = get_object_or_404(Operation.objects.select_related(
        'buyer_company',
        'created_by',
        'follow_by'
    ).prefetch_related(
        'customers',
        'sales_prices'
    ), id=operation_id)

    # Müşterileri ve satış fiyatlarını al
    customers = operation.customers.filter(is_active=True).order_by('first_name', 'last_name')
    sales_prices = operation.sales_prices.filter(is_active=True)

    # Form seçeneklerini önbellekten al veya oluştur
    form_choices = cache.get('form_choices')
    if not form_choices:
        # Tüm seçenekleri tek seferde yükle ve önbelleğe al
        form_choices = {
            'currencies': Currency.objects.all(),
            'vehicle_types': VehicleType.objects.all(),
            'vehicle_suppliers': VehicleSupplier.objects.all(),
            'no_vehicle_tours': NoVehicleTour.objects.all(),
            'no_vehicle_activities': Activity.objects.all(),
            'tours': Tour.objects.select_related('start_city', 'end_city').all(),
            'transfers': Transfer.objects.select_related('start_city', 'end_city').all(),
            'museums': Museum.objects.all(),
            'hotels': Hotel.objects.select_related('city').all(),
            'guides': Guide.objects.all(),
            'activity_suppliers': ActivitySupplier.objects.all()
        }
        
        # Seçenekleri önbelleğe al (1 saat)
        cache.set('form_choices', form_choices, 3600)

    # Form sınıflarını hazırla
    form_kwargs = {
        'use_required_attribute': False,
        'initial': {'currency': form_choices['currencies'].first()}
    }

    # Form sınıflarını oluştur
    form_classes = {
        'vehicle': OperationItemVehicleForm,
        'no_vehicle_tour': OperationItemNoVehicleTourForm,
        'no_vehicle_activity': OperationItemActivityForm
    }

    # Form alanlarını önbellekten gelen verilerle doldur
    forms = {}
    for form_name, form_class in form_classes.items():
        form = form_class(**form_kwargs)
        for field_name, field in form.fields.items():
            if field_name in form_choices:
                if isinstance(field, ModelChoiceField):
                    field.queryset = form_choices[field_name]
                elif isinstance(field, ModelMultipleChoiceField):
                    field.queryset = form_choices[field_name]
                elif isinstance(field, ChoiceField):
                    field.choices = [(obj.id, str(obj)) for obj in form_choices[field_name]]
        forms[form_name] = form

    # Alt öğe formlarını oluştur
    subitem_forms = {
        'transfer': OperationSubItemTransferForm(**form_kwargs),
        'tour': OperationSubItemTourForm(**form_kwargs),
        'museum': OperationSubItemMuseumForm(**form_kwargs),
        'hotel': OperationSubItemHotelForm(**form_kwargs),
        'guide': OperationSubItemGuideForm(**form_kwargs),
        'activity': OperationSubItemActivityForm(**form_kwargs),
        'other': OperationSubItemOtherForm(**form_kwargs)
    }

    # Alt öğe formlarının alanlarını doldur
    for form in subitem_forms.values():
        for field_name, field in form.fields.items():
            if field_name in form_choices:
                if isinstance(field, ModelChoiceField):
                    field.queryset = form_choices[field_name]
                elif isinstance(field, ModelMultipleChoiceField):
                    field.queryset = form_choices[field_name]
                elif isinstance(field, ChoiceField):
                    field.choices = [(obj.id, str(obj)) for obj in form_choices[field_name]]

    # Operasyon günlerini al
    operation_days = operation.days.all().order_by('date')

    # Operasyon öğelerini al
    operation_items = OperationItem.objects.filter(
        operation_day__operation=operation
    ).select_related(
        'operation_day',
        'vehicle_type',
        'vehicle_supplier',
        'no_vehicle_tour',
        'no_vehicle_activity',
        'activity_supplier',
        'sales_currency',
        'cost_currency'
    ).prefetch_related(
        'subitems',
        'subitems__tour',
        'subitems__transfer',
        'subitems__hotel',
        'subitems__guide',
        'subitems__activity',
        'subitems__activity_supplier',
        'subitems__sales_currency',
        'subitems__cost_currency',
        'subitems__museums'
    ).order_by('operation_day__date', 'pick_time')

    # Operasyon öğelerini günlere göre grupla
    grouped_items = {}
    for item in operation_items:
        date = item.operation_day.date
        if date not in grouped_items:
            grouped_items[date] = []
        grouped_items[date].append(item)

    context = {
        'operation': operation,
        'customers': customers,
        'sales_prices': sales_prices,
        'forms': forms,
        'subitem_forms': subitem_forms,
        'operation_days': operation_days,
        'grouped_items': grouped_items,
        'form_choices': form_choices,
        'page_title': 'Operasyon Detayı'
    }

    return render(request, 'operation/create_item.html', context)

def create_operation_item_vehicle(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    if request.method == 'POST':
        form = OperationItemVehicleForm(request.POST)
        operation_day = request.POST.get('operation_day')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_day = OperationDay.objects.get(id=operation_day)
            item.item_type = 'VEHICLE'
            item.save()
            messages.success(request, 'Araç başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=operation_id)
        else:
            print(form.errors)
    else:
        form = OperationItemVehicleForm()
    return render(request, 'operation/modals/item_vehicle_modal.html', {'form': form, 'operation': operation})

def create_operation_item_no_vehicle(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    if request.method == 'POST':
        form = OperationItemNoVehicleTourForm(request.POST)
        operation_day = request.POST.get('operation_day')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_day = OperationDay.objects.get(id=operation_day)
            item.item_type = 'NO_VEHICLE_TOUR'
            item.save()
            messages.success(request, 'Araçsız tur başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=operation_id)
    else:
        form = OperationItemNoVehicleTourForm()
    return render(request, 'operation/modals/item_no_vehicle_modal.html', {'form': form, 'operation': operation})

def create_operation_item_activity(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    if request.method == 'POST':
        form = OperationItemActivityForm(request.POST)
        operation_day = request.POST.get('operation_day')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_day = OperationDay.objects.get(id=operation_day)
            item.item_type = 'NO_VEHICLE_ACTIVITY'
            item.save()
            messages.success(request, 'Aktivite başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=operation_id)
    else:
        form = OperationItemActivityForm()
    return render(request, 'operation/modals/item_activity_modal.html', {'form': form, 'operation': operation})

def create_operation_sub_item_tour(request):
    if request.method == 'POST':
        form = OperationSubItemTourForm(request.POST)
        operation_item_id = request.POST.get('operation_item_id')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_item = OperationItem.objects.get(id=operation_item_id)
            item.subitem_type = 'TOUR'
            item.save()
            messages.success(request, 'Tur başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemTourForm()
    return render(request, 'operation/modals/sub_item_tour_modal.html', {'form': form})

def create_operation_sub_item_transfer(request):
    if request.method == 'POST':
        form = OperationSubItemTransferForm(request.POST)
        operation_item_id = request.POST.get('operation_item_id')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_item = OperationItem.objects.get(id=operation_item_id)
            item.subitem_type = 'TRANSFER'
            item.save()
            messages.success(request, 'Transfer başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemTransferForm()
    return render(request, 'operation/modals/sub_item_transfer_modal.html', {'form': form})

def create_operation_sub_item_museum(request):
    if request.method == 'POST':
        form = OperationSubItemMuseumForm(request.POST)
        operation_item_id = request.POST.get('operation_item_id')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_item = OperationItem.objects.get(id=operation_item_id)
            item.subitem_type = 'MUSEUM'
            item.save()
            messages.success(request, 'Müze başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemMuseumForm()
    return render(request, 'operation/modals/sub_item_museum_modal.html', {'form': form})

def create_operation_sub_item_hotel(request):
    if request.method == 'POST':
        form = OperationSubItemHotelForm(request.POST)
        operation_item_id = request.POST.get('operation_item_id')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_item = OperationItem.objects.get(id=operation_item_id)
            item.subitem_type = 'HOTEL'
            item.save()
            messages.success(request, 'Otel başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemHotelForm()
    return render(request, 'operation/modals/sub_item_hotel_modal.html', {'form': form})

def create_operation_sub_item_guide(request):
    if request.method == 'POST':
        form = OperationSubItemGuideForm(request.POST)
        operation_item_id = request.POST.get('operation_item_id')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_item = OperationItem.objects.get(id=operation_item_id)
            item.subitem_type = 'GUIDE'
            item.save()
            messages.success(request, 'Rehber başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=item.operation_item.operation_day.operation.id)
        else:
            print(form.errors)
    else:
        form = OperationSubItemGuideForm()
    return render(request, 'operation/modals/guide_modal.html', {'form': form})

def create_operation_sub_item_activity(request): 
    if request.method == 'POST':
        form = OperationSubItemActivityForm(request.POST)
        operation_item_id = request.POST.get('operation_item_id')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_item = OperationItem.objects.get(id=operation_item_id)
            item.subitem_type = 'ACTIVITY'
            item.save()
            messages.success(request, 'Aktivite başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemActivityForm()
    return render(request, 'operation/modals/sub_item_activity_modal.html', {'form': form})

def create_operation_sub_item_other_price(request): 
    if request.method == 'POST':
        form = OperationSubItemOtherForm(request.POST)
        operation_item_id = request.POST.get('operation_item_id')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_item = OperationItem.objects.get(id=operation_item_id)
            item.subitem_type = 'ACTIVITY'
            item.save()
            messages.success(request, 'Aktivite başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemOtherForm()
    return render(request, 'operation/modals/sub_item_other_price_modal.html', {'form': form})

def operation_list(request):
    # Ay seçenekleri
    months = [
        ('1', 'Ocak'), ('2', 'Şubat'), ('3', 'Mart'), ('4', 'Nisan'),
        ('5', 'Mayıs'), ('6', 'Haziran'), ('7', 'Temmuz'), ('8', 'Ağustos'),
        ('9', 'Eylül'), ('10', 'Ekim'), ('11', 'Kasım'), ('12', 'Aralık')
    ]
    
    # Seçili ayı al veya mevcut ayı kullan
    selected_month = request.GET.get('month', str(timezone.now().month))
    
    # Operasyonları al
    operations = Operation.objects.all()
    
    # Ay filtresi uygula
    operations = operations.filter(start_date__month=selected_month)
    
    # Arama parametrelerini al
    reference_number = request.GET.get('reference_number', '')
    buyer_company = request.GET.get('buyer_company', '')
    
    # Filtreleme işlemleri
    if reference_number:
        operations = operations.filter(reference_number__icontains=reference_number)
    if buyer_company:
        operations = operations.filter(buyer_company__name__icontains=buyer_company)
    
    # Sıralama
    operations = operations.order_by('-created_at')
    
    return render(request, 'operation/list.html', {
        'operations': operations,
        'reference_number': reference_number,
        'buyer_company': buyer_company,
        'months': months,
        'selected_month': selected_month,
        'page_title': 'Operasyonlar'
    })




def send_sms(request):
    if request.method == 'POST':
        form = SendSmsForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['users']
            message = form.cleaned_data['message']
            full_message = f"{user.first_name}, Mesajınız: {message} Gönderen: {request.user.first_name} {request.user.last_name} {request.user.role.title()}"
            sms(user.phone, full_message)
            messages.success(request, 'SMS başarıyla gönderildi.')
            return redirect('tour:send_sms')
    else:
        form = SendSmsForm()
    return render(request, 'header/send_sms.html', {'form': form})


def jobs(request):
    # Bugünün tarihini al
    today = timezone.now().date()
    
    # Bugünden başlayarak 7 günlük operasyon günlerini al
    days = OperationDay.objects.filter(
        date__gte=today,
        date__lt=today + timezone.timedelta(days=7)
    ).select_related(
        'operation',
        'operation__buyer_company',
        'operation__follow_by'
    ).prefetch_related(
        'items',
        'items__vehicle_type',
        'items__vehicle_supplier',
        'items__no_vehicle_tour',
        'items__no_vehicle_activity',
        'items__activity_supplier',
        'items__subitems',
        'items__subitems__tour',
        'items__subitems__transfer',
        'items__subitems__hotel',
        'items__subitems__guide',
        'items__subitems__activity',
        'items__subitems__activity_supplier',
        'items__subitems__museums'
    ).order_by('date')
    
    # Günleri tarihe göre grupla
    grouped_days = {}
    for day in days:
        if day.date not in grouped_days:
            grouped_days[day.date] = []
        grouped_days[day.date].append(day)
    
    # Tarihleri sırala
    grouped_days = dict(sorted(grouped_days.items()))
    
    return render(request, 'operation/jobs.html', {
        'grouped_days': grouped_days,
        'today': today,
        'page_title': '7 Günlük Operasyon Programı'
    })

