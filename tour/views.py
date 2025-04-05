from gettext import translation
from django.http import HttpResponse
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
from django.contrib.auth.decorators import login_required
from tour.services import sms
from tour.models import (
    CustomUser, Operation, OperationCustomer, OperationDay, 
    OperationItem, OperationSalesPrice, OperationSubItem, 
    Currency, City, District, Neighborhood, Support, VehicleType, 
    BuyerCompany, Tour, NoVehicleTour, Transfer, Hotel, 
    Museum, Activity, Guide, VehicleSupplier, ActivitySupplier,
    VehicleCost
)

from .services import LoginService, PasswordResetService, sms
from .forms import (
    CurrencyForm, CityForm, DistrictForm, NeighborhoodForm, 
    OperationItemActivityForm, OperationItemNoVehicleTourForm, 
    OperationItemVehicleForm, OperationSubItemActivityForm, 
    OperationSubItemGuideForm, OperationSubItemHotelForm, 
    OperationSubItemMuseumForm, OperationSubItemOtherForm, 
    OperationSubItemTourForm, OperationSubItemTransferForm, SendSmsForm, SupportForm,
    VehicleTypeForm, BuyerCompanyForm, TourForm, NoVehicleTourForm, 
    TransferForm, HotelForm, MuseumForm, ActivityForm, GuideForm, 
    VehicleSupplierForm, ActivitySupplierForm, VehicleCostForm, 
    ActivityCostForm, OperationForm, OperationCustomerForm, 
    OperationSalesPriceForm
)

from datetime import datetime
from django.utils import timezone
from django.db import transaction

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
        next_url = request.POST.get('next')
        user = LoginService.authenticate_user(username, password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, _('Başarıyla giriş yaptınız.'))   
                # Kullanıcı rolüne göre yönlendirme
                if next_url:
                    return redirect(next_url)
                elif user.role == 'admin':
                    return redirect('admin:index')
                else:
                    return redirect('tour:jobs')
            else:
                messages.error(request, _('Hesabınız aktif değil. Lütfen yönetici ile iletişime geçin.'))
        else:
            messages.error(request, _('Geçersiz kullanıcı adı veya şifre.'))
    
    return render(request, 'tour/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, _('Başarıyla çıkış yaptınız.'))
    return redirect('tour:login')


@login_required
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


@login_required
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


@login_required
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





@login_required
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

@login_required
def update_operation(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    if request.method == 'POST':
        form = OperationForm(request.POST, instance=operation)
        if form.is_valid():
            form.save()
            messages.success(request, 'İşlem başarıyla güncellendi.')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('tour:operation_list')
    else:
        form = OperationForm(instance=operation)
    return render(request, 'operation/modals/operation_modal.html', {'form': form, 'operation': operation, 'page_title': 'Operasyon Güncelle'})

@login_required
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

@login_required
def update_operation_customer(request, operation_customer_id):
    operation_customer = get_object_or_404(OperationCustomer, id=operation_customer_id)
    if request.method == 'POST':
        form = OperationCustomerForm(request.POST, instance=operation_customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Müşteri başarıyla güncellendi.')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('tour:create_operation_customer', operation_id=operation_customer.operation.id)
        else:
            print(form.errors)
    else:
        form = OperationCustomerForm(instance=operation_customer)
    return render(request, 'operation/update_customer.html', {'form': form, 'operation_customer': operation_customer, 'page_title': 'Müşteri Güncelle'})

@login_required
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

@login_required
def update_operation_sales_price(request, operation_sales_price_id):
    operation_sales_price = get_object_or_404(OperationSalesPrice, id=operation_sales_price_id)
    if request.method == 'POST':
        form = OperationSalesPriceForm(request.POST, instance=operation_sales_price)
        if form.is_valid():
            form.save()
            messages.success(request, 'Satış fiyatı başarıyla güncellendi.')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('tour:create_operation_sales_price', operation_id=operation_sales_price.operation.id)
    else:
        form = OperationSalesPriceForm(instance=operation_sales_price)
    return render(request, 'operation/update_sales_price.html', {'form': form, 'operation_sales_price': operation_sales_price, 'page_title': 'Satış Fiyatı Güncelle'})


@login_required
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

    # Operasyon güncelleme formunu oluştur
    operation_form = OperationForm(instance=operation)
    
    # Her müşteri için ayrı form oluştur
    customer_forms = {}
    for customer in customers:
        customer_forms[customer.id] = OperationCustomerForm(instance=customer)

    # Satış fiyatları için ayrı form oluştur
    sales_price_forms = {}
    for sales_price in sales_prices:
        sales_price_forms[sales_price.id] = OperationSalesPriceForm(instance=sales_price)

    # Operasyon günlerini al
    operation_days = operation.days.filter(is_active=True).order_by('date')

    # Operasyon öğelerini al
    operation_items = OperationItem.objects.filter(operation_day__in=operation_days, is_active=True)

    operation_sub_items = OperationSubItem.objects.filter(operation_item__in=operation_items, is_active=True)

    vehicle_forms = {}
    for item in operation_items:
        if item.item_type == 'VEHICLE':
            vehicle_forms[item.id] = OperationItemVehicleForm(instance=item)

    no_vehicle_tour_forms = {}
    for item in operation_items:
        if item.item_type == 'NO_VEHICLE_TOUR':
            no_vehicle_tour_forms[item.id] = OperationItemNoVehicleTourForm(instance=item)
            
    no_vehicle_activity_forms = {}
    for item in operation_items:
        if item.item_type == 'NO_VEHICLE_ACTIVITY':
            no_vehicle_activity_forms[item.id] = OperationItemActivityForm(instance=item)

    tour_forms = {}
    for item in operation_sub_items:
        if item.subitem_type == 'TOUR':
            tour_forms[item.id] = OperationSubItemTourForm(instance=item)

    transfer_forms = {}
    for item in operation_sub_items:
        if item.subitem_type == 'TRANSFER':
            transfer_forms[item.id] = OperationSubItemTransferForm(instance=item)

    museum_forms = {}
    for item in operation_sub_items:
        if item.subitem_type == 'MUSEUM':
            museum_forms[item.id] = OperationSubItemMuseumForm(instance=item)

    hotel_forms = {}
    for item in operation_sub_items:
        if item.subitem_type == 'HOTEL':
            hotel_forms[item.id] = OperationSubItemHotelForm(instance=item)
            
    guide_forms = {}
    for item in operation_sub_items:
        if item.subitem_type == 'GUIDE':
            guide_forms[item.id] = OperationSubItemGuideForm(instance=item)

    activity_forms = {}
    for item in operation_sub_items:
        if item.subitem_type == 'ACTIVITY':
            activity_forms[item.id] = OperationSubItemActivityForm(instance=item)

    other_forms = {}
    for item in operation_sub_items:
        if item.subitem_type == 'OTHER_PRICE':
            other_forms[item.id] = OperationSubItemOtherForm(instance=item)

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
    operation_days = operation.days.filter(is_active=True).order_by('date')

    grouped_items = {}
    for item in operation_items:
        date = item.operation_day.date
        if date not in grouped_items:
            grouped_items[date] = []
        grouped_items[date].append(item)

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



    context = {
        'operation': operation,
        'customers': customers,
        'sales_prices': sales_prices,
        'forms': forms,
        'subitem_forms': subitem_forms,
        'operation_days': operation_days,
        'grouped_items': grouped_items,
        'operation_items': operation_items,
        'form_choices': form_choices,
        'operation_form': operation_form,
        'customer_forms': customer_forms,
        'sales_price_forms': sales_price_forms,
        'vehicle_forms': vehicle_forms,
        'no_vehicle_tour_forms': no_vehicle_tour_forms,
        'no_vehicle_activity_forms': no_vehicle_activity_forms,
        'tour_forms': tour_forms,
        'transfer_forms': transfer_forms,
        'museum_forms': museum_forms,
        'hotel_forms': hotel_forms,
        'guide_forms': guide_forms,
        'activity_forms': activity_forms,
        'other_forms': other_forms,
        'operation_sub_items': operation_sub_items,
        'page_title': 'Operasyon Detayı'
    }

    return render(request, 'operation/create_item.html', context)

@login_required
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

@login_required
def update_operation_item_vehicle(request, operation_item_id):
    operation_item = get_object_or_404(OperationItem, id=operation_item_id)
    if request.method == 'POST':
        form = OperationItemVehicleForm(request.POST, instance=operation_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Araç başarıyla güncellendi.')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('tour:create_operation_item', operation_id=operation_item.operation_day.operation.id)
        else:
            print(form.errors)
    else:
        form = OperationItemVehicleForm(instance=operation_item)
    return render(request, 'operation/modals/item_vehicle_modal.html', {'form': form, 'operation': operation_item.operation_day.operation})

@login_required
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

@login_required
def update_operation_item_no_vehicle(request, operation_item_id):
    operation_item = get_object_or_404(OperationItem, id=operation_item_id)
    if request.method == 'POST':
        form = OperationItemNoVehicleTourForm(request.POST, instance=operation_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Araçsız tur başarıyla güncellendi.')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('tour:create_operation_item', operation_id=operation_item.operation_day.operation.id)
    else:
        form = OperationItemNoVehicleTourForm(instance=operation_item)
    return render(request, 'operation/modals/item_no_vehicle_modal.html', {'form': form, 'operation': operation_item.operation_day.operation})

@login_required
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

@login_required
def update_operation_item_activity(request, operation_item_id):
    operation_item = get_object_or_404(OperationItem, id=operation_item_id)
    if request.method == 'POST':
        form = OperationItemActivityForm(request.POST, instance=operation_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Aktivite başarıyla güncellendi.')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('tour:create_operation_item', operation_id=operation_item.operation_day.operation.id)
    else:
        form = OperationItemActivityForm(instance=operation_item)
    return render(request, 'operation/modals/item_activity_modal.html', {'form': form, 'operation': operation_item.operation_day.operation})

@login_required
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

@login_required
def update_operation_sub_item_tour(request, operation_sub_item_id):
    operation_sub_item = get_object_or_404(OperationSubItem, id=operation_sub_item_id)
    if request.method == 'POST':
        form = OperationSubItemTourForm(request.POST, instance=operation_sub_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Tur başarıyla güncellendi.')
            return redirect('tour:create_operation_item', operation_id=operation_sub_item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemTourForm(instance=operation_sub_item)
    return render(request, 'operation/modals/sub_item_tour_modal.html', {'form': form})

@login_required
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

@login_required
def update_operation_sub_item_transfer(request, operation_sub_item_id):
    operation_sub_item = get_object_or_404(OperationSubItem, id=operation_sub_item_id)
    if request.method == 'POST':
        form = OperationSubItemTransferForm(request.POST, instance=operation_sub_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Transfer başarıyla güncellendi.')
            return redirect('tour:create_operation_item', operation_id=operation_sub_item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemTransferForm(instance=operation_sub_item)
    return render(request, 'operation/modals/sub_item_transfer_modal.html', {'form': form})

@login_required
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

@login_required
def update_operation_sub_item_museum(request, operation_sub_item_id):
    operation_sub_item = get_object_or_404(OperationSubItem, id=operation_sub_item_id)
    if request.method == 'POST':
        form = OperationSubItemMuseumForm(request.POST, instance=operation_sub_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Müze başarıyla güncellendi.')
            return redirect('tour:create_operation_item', operation_id=operation_sub_item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemMuseumForm(instance=operation_sub_item)
    return render(request, 'operation/modals/sub_item_museum_modal.html', {'form': form})

@login_required
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

@login_required
def update_operation_sub_item_hotel(request, operation_sub_item_id):
    operation_sub_item = get_object_or_404(OperationSubItem, id=operation_sub_item_id)
    if request.method == 'POST':
        form = OperationSubItemHotelForm(request.POST, instance=operation_sub_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Otel başarıyla güncellendi.')
            return redirect('tour:create_operation_item', operation_id=operation_sub_item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemHotelForm(instance=operation_sub_item)
    return render(request, 'operation/modals/sub_item_hotel_modal.html', {'form': form})

@login_required
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

@login_required
def update_operation_sub_item_guide(request, operation_sub_item_id):
    operation_sub_item = get_object_or_404(OperationSubItem, id=operation_sub_item_id)
    if request.method == 'POST':
        form = OperationSubItemGuideForm(request.POST, instance=operation_sub_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Rehber başarıyla güncellendi.')
            return redirect('tour:create_operation_item', operation_id=operation_sub_item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemGuideForm(instance=operation_sub_item)
    return render(request, 'operation/modals/guide_modal.html', {'form': form})

@login_required
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

def update_operation_sub_item_activity(request, operation_sub_item_id):
    operation_sub_item = get_object_or_404(OperationSubItem, id=operation_sub_item_id)
    if request.method == 'POST':
        form = OperationSubItemActivityForm(request.POST, instance=operation_sub_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Aktivite başarıyla güncellendi.')
            return redirect('tour:create_operation_item', operation_id=operation_sub_item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemActivityForm(instance=operation_sub_item)
    return render(request, 'operation/modals/sub_item_activity_modal.html', {'form': form})

@login_required
def create_operation_sub_item_other_price(request): 
    if request.method == 'POST':
        form = OperationSubItemOtherForm(request.POST)
        operation_item_id = request.POST.get('operation_item_id')
        if form.is_valid():
            item = form.save(commit=False)
            item.operation_item = OperationItem.objects.get(id=operation_item_id)
            item.subitem_type = 'OTHER_PRICE'
            item.save()
            messages.success(request, 'Diğer fiyat başarıyla eklendi.')
            return redirect('tour:create_operation_item', operation_id=item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemOtherForm()
    return render(request, 'operation/modals/sub_item_other_price_modal.html', {'form': form})

@login_required
def update_operation_sub_item_other_price(request, operation_sub_item_id):
    operation_sub_item = get_object_or_404(OperationSubItem, id=operation_sub_item_id)
    if request.method == 'POST':
        form = OperationSubItemOtherForm(request.POST, instance=operation_sub_item)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Diğer fiyat başarıyla güncellendi.')
            return redirect('tour:create_operation_item', operation_id=operation_sub_item.operation_item.operation_day.operation.id)
    else:
        form = OperationSubItemOtherForm(instance=operation_sub_item)
    return render(request, 'operation/modals/sub_item_other_price_modal.html', {'form': form})

@login_required
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
    
    # Arama parametrelerini al
    reference_number = request.GET.get('reference_number', '')
    buyer_company = request.GET.get('buyer_company', '')
    follow_by = request.GET.get('follow_by', '')
    
    # Filtreleme işlemleri
    if reference_number:
        operations = operations.filter(reference_number__icontains=reference_number)
    if buyer_company:
        operations = operations.filter(buyer_company__name__icontains=buyer_company)
    if follow_by:
        operations = operations.filter(follow_by__first_name__icontains=follow_by) | \
                    operations.filter(follow_by__last_name__icontains=follow_by)
    
    # Ay filtresi uygula
    operations = operations.filter(start_date__month=selected_month)
    
    # Sıralama
    operations = operations.order_by('-created_at')
    
    return render(request, 'operation/list.html', {
        'operations': operations,
        'reference_number': reference_number,
        'buyer_company': buyer_company,
        'follow_by': follow_by,
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


def check_item_info(item):
    """Item için eksik veri kontrolü yapar"""
    missing_info = []
    
    # Araçlı item kontrolleri
    if item.item_type == 'VEHICLE':
        if not item.pick_time:
            missing_info.append("Alış saati")
        if not item.pick_up_location:
            missing_info.append("Alış lokasyonu")
        if not item.drop_off_location:
            missing_info.append("Bırakış lokasyonu")
        if not item.vehicle_type:
            missing_info.append("Araç tipi")
        if not item.vehicle_supplier:
            missing_info.append("Araç tedarikçisi")
        if not item.driver_name:
            missing_info.append("Şoför adı")
        if not item.driver_phone:
            missing_info.append("Şoför telefonu")
        if not item.vehicle_plate_no:
            missing_info.append("Araç plakası")
        if not item.cost_price:
            missing_info.append("Maliyet tutarı")
        if not item.cost_currency:
            missing_info.append("Maliyet para birimi")
        
        # Araç maliyeti kontrolü
        if item.vehicle_supplier and not VehicleCost.objects.filter(
            supplier=item.vehicle_supplier,
            tour=item.subitems.first().tour if item.subitems.first() and item.subitems.first().tour else None,
            transfer=item.subitems.first().transfer if item.subitems.first() and item.subitems.first().transfer else None,
            is_active=True
        ).exists():
            missing_info.append("Araç maliyet kaydı")

    # Araçsız tur kontrolleri
    elif item.item_type == 'NO_VEHICLE_TOUR':
        if not item.pick_time:
            missing_info.append("Başlangıç saati")
        if not item.pick_up_location:
            missing_info.append("Başlangıç lokasyonu")
        if not item.drop_off_location:
            missing_info.append("Bitiş lokasyonu")
        if not item.no_vehicle_tour:
            missing_info.append("Araçsız tur")
        if not item.sales_price:
            missing_info.append("Satış tutarı")
        if not item.sales_currency:
            missing_info.append("Satış para birimi")
        if not item.cost_price:
            missing_info.append("Maliyet tutarı")
        if not item.cost_currency:
            missing_info.append("Maliyet para birimi")

    # Araçsız aktivite kontrolleri
    elif item.item_type == 'NO_VEHICLE_ACTIVITY':
        if not item.pick_time:
            missing_info.append("Başlangıç saati")
        if not item.pick_up_location:
            missing_info.append("Başlangıç lokasyonu")
        if not item.drop_off_location:
            missing_info.append("Bitiş lokasyonu")
        if not item.no_vehicle_activity:
            missing_info.append("Araçsız aktivite")
        if not item.activity_supplier:
            missing_info.append("Aktivite tedarikçisi")
        if not item.sales_price:
            missing_info.append("Satış tutarı")
        if not item.sales_currency:
            missing_info.append("Satış para birimi")
        if not item.cost_price:
            missing_info.append("Maliyet tutarı")
        if not item.cost_currency:
            missing_info.append("Maliyet para birimi")

    # Alt öğeler için kontroller
    for subitem in item.subitems.all():
        # Tur veya transfer kontrolü
        if not subitem.tour and not subitem.transfer:
            missing_info.append("Tur/Transfer")
        
        # Subitem tiplerine göre kontroller
        if subitem.subitem_type == 'TOUR':
            if not subitem.tour:
                missing_info.append("Tur seçilmemiş")
            if not subitem.guide:
                missing_info.append("Rehber seçilmemiş")
            if not subitem.sales_price:
                missing_info.append(f"Tur satış tutarı")
            if not subitem.sales_currency:
                missing_info.append(f"Tur satış para birimi")
            if not subitem.cost_price:
                missing_info.append(f"Tur maliyet tutarı")
            if not subitem.cost_currency:
                missing_info.append(f"Tur maliyet para birimi")
            
        elif subitem.subitem_type == 'TRANSFER':
            if not subitem.transfer:
                missing_info.append("Transfer seçilmemiş")
            if not subitem.sales_price:
                missing_info.append(f"Transfer satış tutarı")
            if not subitem.sales_currency:
                missing_info.append(f"Transfer satış para birimi")
            if not subitem.cost_price:
                missing_info.append(f"Transfer maliyet tutarı")
            if not subitem.cost_currency:
                missing_info.append(f"Transfer maliyet para birimi")
            
        elif subitem.subitem_type == 'HOTEL':
            if not subitem.hotel:
                missing_info.append("Otel seçilmemiş")
            if not subitem.sales_price:
                missing_info.append(f"Otel satış tutarı")
            if not subitem.sales_currency:
                missing_info.append(f"Otel satış para birimi")
            if not subitem.cost_price:
                missing_info.append(f"Otel maliyet tutarı")
            if not subitem.cost_currency:
                missing_info.append(f"Otel maliyet para birimi")
            
        elif subitem.subitem_type == 'GUIDE':
            if not subitem.guide:
                missing_info.append("Rehber seçilmemiş")
            if not subitem.cost_price:
                missing_info.append(f"Rehber maliyet tutarı")
            if not subitem.cost_currency:
                missing_info.append(f"Rehber maliyet para birimi")
            
        elif subitem.subitem_type == 'ACTIVITY':
            if not subitem.activity:
                missing_info.append("Aktivite seçilmemiş")
            if not subitem.activity_supplier:
                missing_info.append("Aktivite tedarikçisi seçilmemiş")
            if not subitem.sales_price:
                missing_info.append(f"Aktivite satış tutarı")
            if not subitem.sales_currency:
                missing_info.append(f"Aktivite satış para birimi")
            if not subitem.cost_price:
                missing_info.append(f"Aktivite maliyet tutarı")
            if not subitem.cost_currency:
                missing_info.append(f"Aktivite maliyet para birimi")
            
        elif subitem.subitem_type == 'MUSEUM':
            if not subitem.museums.exists():
                missing_info.append("Müze seçilmemiş")
            if not subitem.sales_price:
                missing_info.append(f"Müze satış tutarı")
            if not subitem.sales_currency:
                missing_info.append(f"Müze satış para birimi")
            if not subitem.cost_price:
                missing_info.append(f"Müze maliyet tutarı")
            if not subitem.cost_currency:
                missing_info.append(f"Müze maliyet para birimi")
            
        elif subitem.subitem_type == 'OTHER_PRICE':
            if not subitem.description:
                missing_info.append("Diğer fiyat açıklaması")
            if not subitem.sales_price:
                missing_info.append(f"Diğer fiyat satış tutarı")
            if not subitem.sales_currency:
                missing_info.append(f"Diğer fiyat satış para birimi")
            if not subitem.cost_price:
                missing_info.append(f"Diğer fiyat maliyet tutarı")
            if not subitem.cost_currency:
                missing_info.append(f"Diğer fiyat maliyet para birimi")

    return list(set(missing_info))  # Tekrar eden eksikleri temizle

@login_required
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
    
    # Günleri tarihe göre grupla ve item bilgilerini ekle
    grouped_days = {}
    for day in days:
        if day.date not in grouped_days:
            grouped_days[day.date] = []
        
        # Her item için eksik bilgileri kontrol et
        for item in day.items.filter(is_active=True):
            item.missing_info = check_item_info(item)
        
        grouped_days[day.date].append(day)
    
    # Tarihleri sırala
    grouped_days = dict(sorted(grouped_days.items()))
    
    return render(request, 'operation/jobs.html', {
        'grouped_days': grouped_days,
        'today': today,
        'page_title': '7 Günlük Operasyon Programı'
    })

@login_required
def toggle_operation(request, operation_id):
    operation = get_object_or_404(Operation, id=operation_id)
    new_status = not operation.is_active
    next_url = request.GET.get('next')
    # Tek bir transaction içinde tüm işlemleri gerçekleştir
    with transaction.atomic():
        # Operasyon durumunu güncelle
        operation.is_active = new_status
        operation.save()

        OperationCustomer.objects.filter(operation=operation).update(is_active=new_status)
        OperationSalesPrice.objects.filter(operation=operation).update(is_active=new_status)
        # İlgili tüm günleri güncelle
        OperationDay.objects.filter(operation=operation).update(is_active=new_status)
        # İlgili tüm öğeleri güncelle
        OperationItem.objects.filter(operation_day__operation=operation).update(is_active=new_status)
        # İlgili tüm alt öğeleri güncelle
        OperationSubItem.objects.filter(operation_item__operation_day__operation=operation).update(is_active=new_status)
    return redirect('tour:operation_list')

@login_required
def toggle_customer(request, operation_customer_id):
    customer = get_object_or_404(OperationCustomer, id=operation_customer_id)
    customer.is_active = not customer.is_active
    customer.save()
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('tour:operation_list')

@login_required
def toggle_sales_price(request, operation_sales_price_id):
    sales_price = get_object_or_404(OperationSalesPrice, id=operation_sales_price_id)
    sales_price.is_active = not sales_price.is_active
    sales_price.save()
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('tour:operation_list')

@login_required
def toggle_operation_day(request, operation_day_id):
    operation_day = get_object_or_404(OperationDay, id=operation_day_id)
    new_status = not operation_day.is_active
    next_url = request.GET.get('next')
    # Tek bir transaction içinde tüm işlemleri gerçekleştir
    with transaction.atomic():
        # Gün durumunu güncelle
        operation_day.is_active = new_status
        operation_day.save()
        
        # İlgili tüm öğeleri güncelle
        OperationItem.objects.filter(operation_day=operation_day).update(is_active=new_status)
        
        # İlgili tüm alt öğeleri güncelle
        OperationSubItem.objects.filter(operation_item__operation_day=operation_day).update(is_active=new_status)
    if next_url:
        return redirect(next_url)
    return redirect('tour:operation_list')

@login_required
def toggle_operation_item(request, operation_item_id):
    operation_item = get_object_or_404(OperationItem, id=operation_item_id)
    new_status = not operation_item.is_active
    next_url = request.GET.get('next')

    with transaction.atomic():
        # Öğe durumunu güncelle
        operation_item.is_active = new_status
        operation_item.save()
        
        # İlgili tüm alt öğeleri güncelle
        OperationSubItem.objects.filter(operation_item=operation_item).update(is_active=new_status)
    if next_url:
        return redirect(next_url)
    return redirect('tour:operation_list')

@login_required
def toggle_operation_sub_item(request, operation_sub_item_id):
    operation_sub_item = get_object_or_404(OperationSubItem, id=operation_sub_item_id)
    operation_sub_item.is_active = not operation_sub_item.is_active
    operation_sub_item.save()
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('tour:operation_list')

@login_required
def create_support(request):
    if request.method == 'POST':
        form = SupportForm(request.POST)
        if form.is_valid():
            support = form.save(commit=False)
            support.user = request.user
            support.save()
            messages.success(request, 'Destek talebi başarıyla oluşturuldu.')
            sms("905054471953", f"Destek talebi: {support.subject} {support.message}, Gönderen: {support.user.first_name} {support.user.last_name}")
            return redirect('tour:create_support')
    else:
        form = SupportForm()
    return render(request, 'header/send_sms.html', {'form': form})

@login_required
def support_list(request):
    supports = Support.objects.filter(is_active=True, user=request.user)
    return render(request, 'header/support_list.html', {'supports': supports})