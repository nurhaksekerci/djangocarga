from django.db import models
from django.core.validators import MinValueValidator, MinLengthValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
import re

class CustomUser(AbstractUser):
    GENDER_CHOICES = (
        ('male', _('Erkek')),
        ('female', _('Kadın')),
        ('other', _('Diğer')),
    )

    ROLE_CHOICES = (
        ('admin', _('Sistem Yöneticisi')),
        ('company_admin', _('Şirket Yöneticisi')),
        ('manager', _('Müdür')),
        ('operation_chief', _('Operasyon Şefi')),
        ('operation_staff', _('Operasyon Personeli')),
        ('accounting', _('Muhasebe')),
    )

    phone = models.CharField(
        _('Telefon Numarası'),
        max_length=20,
        null=True,
        blank=True
    )
    gender = models.CharField(
        _('Cinsiyet'),
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )
    photo = models.ImageField(
        _('Profil Fotoğrafı'),
        upload_to='user_photos/',
        null=True,
        blank=True
    )
    role = models.CharField(
        _('Rol'),
        max_length=20,
        choices=ROLE_CHOICES,
        default='employee'
    )
    reset_code = models.CharField(
        _('Parola Sıfırlama Kodu'),
        max_length=6,
        null=True,
        blank=True
    )
    reset_code_created_at = models.DateTimeField(
        _('Parola Sıfırlama Kodu Oluşturulma Tarihi'),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _('Kullanıcı')
        verbose_name_plural = _('Kullanıcılar')
        
    def __str__(self):
        return f"{self.get_full_name()} - {self.get_role_display()}"
    
class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True, verbose_name="Para Birimi Kodu")  # USD, EUR, TRY
    name = models.CharField(max_length=50, verbose_name="Para Birimi Adı")  # US Dollar, Euro, Turkish Lira
    symbol = models.CharField(max_length=5, verbose_name="Sembol")  # $, €, ₺

    class Meta:
        verbose_name = "Para Birimi"
        verbose_name_plural = "Para Birimleri"

    def __str__(self):
        return f"{self.code} ({self.symbol})"

class City(models.Model):
    name = models.CharField(verbose_name=("City Name"), max_length=100, unique=True)
    code = models.CharField(verbose_name=("City Code"), max_length=10, unique=True, validators=[MinLengthValidator(2), MaxLengthValidator(10)])

    class Meta:
        verbose_name = _("City")
        verbose_name_plural = _("Cities")

    def __str__(self):
        return self.name

class District(models.Model):
    name = models.CharField(verbose_name=("District Name"), max_length=100)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='districts')
    code = models.CharField(verbose_name=("District Code"), max_length=10, validators=[MinLengthValidator(2), MaxLengthValidator(10)])

    class Meta:
        verbose_name = _("District")
        verbose_name_plural = _("Districts")
        unique_together = ('city', 'name')

    def __str__(self):
        return f"{self.name}, {self.city.name}"

class Neighborhood(models.Model):
    name = models.CharField(verbose_name=("Neighborhood Name"), max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='neighborhoods')
    code = models.CharField(verbose_name=("Neighborhood Code"), max_length=10, validators=[MinLengthValidator(2), MaxLengthValidator(10)])

    class Meta:
        verbose_name = _("Neighborhood")
        verbose_name_plural = _("Neighborhoods")
        unique_together = ('district', 'name')

    def __str__(self):
        return f"{self.name}, {self.district.name}"


class VehicleType(models.Model):
    name = models.CharField(verbose_name=_("Vehicle Type"), max_length=50)  # Binek, Minivan vs.
    created_at = models.DateTimeField(verbose_name=_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Updated At"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Vehicle Type")
        verbose_name_plural = _("Vehicle Types")

class BuyerCompany(models.Model):
    
    name = models.CharField(verbose_name="Company Name", max_length=255)
    short_name = models.CharField(verbose_name="Short Name", max_length=50, unique=True)
    contact = models.CharField(verbose_name="Contact", max_length=255)
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.name} ({self.short_name})"

    class Meta:
        verbose_name_plural = "Buyer Companies"

class Tour(models.Model):
    
    name = models.CharField(verbose_name="Tour Name", max_length=255)
    start_city = models.ForeignKey(City, verbose_name="Start City", on_delete=models.CASCADE, related_name='tour_starts')
    end_city = models.ForeignKey(City, verbose_name="End City", on_delete=models.CASCADE, related_name='tour_ends')
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.name} ({self.start_city} - {self.end_city})"

class NoVehicleTour(models.Model):
    
    name = models.CharField(verbose_name="Tour Name", max_length=255)
    city = models.ForeignKey(City, verbose_name="City", on_delete=models.CASCADE)
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.name} ({self.city})"

class Transfer(models.Model):
    
    name = models.CharField(verbose_name="Transfer Name", max_length=255)
    start_city = models.ForeignKey(City, verbose_name="Start City", on_delete=models.CASCADE, related_name='transfer_starts')
    end_city = models.ForeignKey(City, verbose_name="End City", on_delete=models.CASCADE, related_name='transfer_ends')
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.name} ({self.start_city} - {self.end_city})"

class Hotel(models.Model):
    
    name = models.CharField(verbose_name=_("Hotel Name"), max_length=255)
    city = models.ForeignKey(City, verbose_name=_("City"), on_delete=models.CASCADE)
    single_price = models.DecimalField(verbose_name=_("Single Room Price"), max_digits=10, decimal_places=2)
    double_price = models.DecimalField(verbose_name=_("Double Room Price"), max_digits=10, decimal_places=2)
    triple_price = models.DecimalField(verbose_name=_("Family Room Price"), max_digits=10, decimal_places=2)
    currency = models.ForeignKey(
        Currency, 
        verbose_name=_("Currency"), 
        on_delete=models.PROTECT,
        related_name='hotels'
    )
    valid_until = models.DateField(verbose_name=_("Valid Until"))
    created_at = models.DateTimeField(verbose_name=_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Updated At"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)

    def __str__(self):
        return f"{self.name} ({self.city})"

    def clean(self):
        if self.valid_until and self.valid_until < timezone.now().date():
            raise ValidationError(_("Geçerlilik tarihi geçmiş tarih olamaz"))

    def save(self, *args, **kwargs):
        from .services import PriceHistoryService
        
        if not self.pk:
            super().save(*args, **kwargs)
            PriceHistoryService.create_hotel_price_history(self)
        else:
            old_instance = Hotel.objects.get(pk=self.pk)
            super().save(*args, **kwargs)
            PriceHistoryService.update_hotel_price_history(self, old_instance)

    def get_price_for_date(self, target_date):
        return self.price_history.filter(
            valid_from__lte=target_date,
            valid_until__gte=target_date
        ).first()

    class Meta:
        verbose_name = _("Hotel")
        verbose_name_plural = _("Hotels")

class Museum(models.Model):
    
    name = models.CharField(verbose_name=_("Museum Name"), max_length=255)
    city = models.ForeignKey(City, verbose_name=_("City"), on_delete=models.CASCADE)
    local_price = models.DecimalField(
        verbose_name=_("Local Price"), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    foreign_price = models.DecimalField(
        verbose_name=_("Foreign Price"), 
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.ForeignKey(Currency, verbose_name=_("Currency"), on_delete=models.PROTECT, related_name='museums')
    valid_until = models.DateField(verbose_name=_("Valid Until"))
    created_at = models.DateTimeField(verbose_name=_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Updated At"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)

    def __str__(self):
        return f"{self.name} ({self.city})"

    def clean(self):
        if self.valid_until and self.valid_until < timezone.now().date():
            raise ValidationError(_("Geçerlilik tarihi geçmiş tarih olamaz"))

    def save(self, *args, **kwargs):
        from .services import PriceHistoryService
        
        if not self.pk:
            super().save(*args, **kwargs)
            PriceHistoryService.create_museum_price_history(self)
        else:
            old_instance = Museum.objects.get(pk=self.pk)
            super().save(*args, **kwargs)
            PriceHistoryService.update_museum_price_history(self, old_instance)

    def get_price_for_date(self, target_date):
        return self.price_history.filter(
            valid_from__lte=target_date,
            valid_until__gte=target_date
        ).first()

    class Meta:
        verbose_name = _("Museum")
        verbose_name_plural = _("Museums")

class Activity(models.Model):
    
    name = models.CharField(verbose_name="Activity Name", max_length=255)
    cities = models.ManyToManyField(City, verbose_name="Cities")
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"


class Guide(models.Model):
    
    name = models.CharField(verbose_name="Guide Name", max_length=255)
    phone = models.CharField(verbose_name="Phone Number", max_length=20)
    document_no = models.CharField(verbose_name="Document Number", max_length=50)
    cities = models.ManyToManyField(City, verbose_name="Cities")
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return self.name

class VehicleSupplier(models.Model):
    
    name = models.CharField(verbose_name="Supplier Name", max_length=255)
    cities = models.ManyToManyField(City, verbose_name="Service Cities")
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return self.name

class ActivitySupplier(models.Model):
    
    name = models.CharField(verbose_name="Supplier Name", max_length=255)
    cities = models.ManyToManyField(City, verbose_name="Service Cities")
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return self.name

class VehicleCost(models.Model):
    
    supplier = models.ForeignKey(VehicleSupplier, verbose_name=_("Supplier"), on_delete=models.CASCADE)
    tour = models.ForeignKey(Tour, verbose_name=_("Tour"), on_delete=models.CASCADE, null=True, blank=True)
    transfer = models.ForeignKey(Transfer, verbose_name=_("Transfer"), on_delete=models.CASCADE, null=True, blank=True)
    car_cost = models.DecimalField(verbose_name=_("Car Cost"), max_digits=10, decimal_places=2)
    minivan_cost = models.DecimalField(verbose_name=_("Minivan Cost"), max_digits=10, decimal_places=2)
    minibus_cost = models.DecimalField(verbose_name=_("Minibus Cost"), max_digits=10, decimal_places=2)
    midibus_cost = models.DecimalField(verbose_name=_("Midibus Cost"), max_digits=10, decimal_places=2)
    bus_cost = models.DecimalField(verbose_name=_("Bus Cost"), max_digits=10, decimal_places=2)
    currency = models.ForeignKey(
        Currency, 
        verbose_name=_("Currency"), 
        on_delete=models.PROTECT,
        related_name='vehicle_costs'
    )
    valid_until = models.DateField(verbose_name=_("Valid Until"))
    created_at = models.DateTimeField(verbose_name=_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Updated At"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)

    def clean(self):
        if self.tour and self.transfer:
            raise ValidationError(_("Cannot select both tour and transfer"))
        if not self.tour and not self.transfer:
            raise ValidationError(_("Must select either tour or transfer"))

    def save(self, *args, **kwargs):
        from .services import PriceHistoryService
        
        self.clean()
        if not self.pk:
            super().save(*args, **kwargs)
            PriceHistoryService.create_vehicle_cost_history(self)
        else:
            old_instance = VehicleCost.objects.get(pk=self.pk)
            super().save(*args, **kwargs)
            PriceHistoryService.update_vehicle_cost_history(self, old_instance)

    def __str__(self):
        return f"{self.supplier.name} - {'Tour' if self.tour else 'Transfer'}"

    def get_price_for_date(self, target_date):
        return self.price_history.filter(
            valid_from__lte=target_date,
            valid_until__gte=target_date,
            is_active=True
        ).first()

    class Meta:
        verbose_name = _("Vehicle Cost")
        verbose_name_plural = _("Vehicle Costs")

class ActivityCost(models.Model):
    
    activity = models.ForeignKey(Activity, verbose_name=_("Activity"), on_delete=models.CASCADE)
    supplier = models.ForeignKey(ActivitySupplier, verbose_name=_("Supplier"), on_delete=models.CASCADE)
    price = models.DecimalField(verbose_name=_("Price"), max_digits=10, decimal_places=2)
    currency = models.ForeignKey(
        Currency, 
        verbose_name=_("Currency"), 
        on_delete=models.PROTECT,
        related_name='activity_costs'
    )
    valid_until = models.DateField(verbose_name=_("Valid Until"))
    created_at = models.DateTimeField(verbose_name=_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Updated At"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)

    def __str__(self):
        return f"{self.activity.name} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        from .services import PriceHistoryService
        
        if not self.pk:
            super().save(*args, **kwargs)
            PriceHistoryService.create_activity_cost_history(self)
        else:
            old_instance = ActivityCost.objects.get(pk=self.pk)
            super().save(*args, **kwargs)
            PriceHistoryService.update_activity_cost_history(self, old_instance)

    def get_price_for_date(self, target_date):
        return self.price_history.filter(
            valid_from__lte=target_date,
            valid_until__gte=target_date,
            is_active=True
        ).first()

    class Meta:
        verbose_name = _("Activity Cost")
        verbose_name_plural = _("Activity Costs")

# Fiyat geçmişi için abstract base model
class PriceHistoryBase(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    valid_from = models.DateField(verbose_name="Valid From")
    valid_until = models.DateField(verbose_name="Valid Until")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def clean(self):
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError("Bitiş tarihi başlangıç tarihinden önce olamaz")

# Otel fiyat geçmişi
class HotelPriceHistory(PriceHistoryBase):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='price_history')
    single_price = models.DecimalField(max_digits=10, decimal_places=2)
    double_price = models.DecimalField(max_digits=10, decimal_places=2)
    triple_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.hotel.name} ({self.valid_from} - {self.valid_until})"

    class Meta:
        verbose_name = "Hotel Price History"
        verbose_name_plural = "Hotel Price Histories"
        ordering = ['-valid_from']

# Müze fiyat geçmişi
class MuseumPriceHistory(PriceHistoryBase):
    museum = models.ForeignKey(Museum, on_delete=models.CASCADE, related_name='price_history')
    local_price = models.DecimalField(max_digits=10, decimal_places=2)
    foreign_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.museum.name} ({self.valid_from} - {self.valid_until})"

    class Meta:
        verbose_name = "Museum Price History"
        verbose_name_plural = "Museum Price Histories"
        ordering = ['-valid_from']

# Araç maliyet geçmişi
class VehicleCostHistory(PriceHistoryBase):
    vehicle_cost = models.ForeignKey(VehicleCost, on_delete=models.CASCADE, related_name='price_history')
    car_cost = models.DecimalField(max_digits=10, decimal_places=2)
    minivan_cost = models.DecimalField(max_digits=10, decimal_places=2)
    minibus_cost = models.DecimalField(max_digits=10, decimal_places=2)
    midibus_cost = models.DecimalField(max_digits=10, decimal_places=2)
    bus_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.vehicle_cost.supplier.name} ({self.valid_from} - {self.valid_until})"

    class Meta:
        verbose_name = "Vehicle Cost History"
        verbose_name_plural = "Vehicle Cost Histories"
        ordering = ['-valid_from']

# Aktivite maliyet geçmişi
class ActivityCostHistory(PriceHistoryBase):
    activity_cost = models.ForeignKey(ActivityCost, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.activity_cost.activity.name} ({self.valid_from} - {self.valid_until})"

    class Meta:
        verbose_name = "Activity Cost History"
        verbose_name_plural = "Activity Cost Histories"
        ordering = ['-valid_from']

class Operation(models.Model):
    DRAFT = 'DRAFT'
    CONFIRMED = 'CONFIRMED'
    COMPLETED = 'COMPLETED'
    CANCELLED = 'CANCELLED'

    STATUS_CHOICES = [
        (DRAFT, _('Taslak')),
        (CONFIRMED, _('Onaylandı')),
        (COMPLETED, _('Tamamlandı')),
        (CANCELLED, _('İptal Edildi')),
    ]

    buyer_company = models.ForeignKey(BuyerCompany, verbose_name=_("Buyer Company"), on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        CustomUser,
        verbose_name=_("Created By"),
        on_delete=models.PROTECT,
        related_name='created_operations'
    )
    follow_by = models.ForeignKey(
        CustomUser,
        verbose_name=_("Follow By"),
        on_delete=models.PROTECT,
        related_name='following_operations'
    )
    reference_number = models.CharField(
        verbose_name=_("Reference Number"),
        max_length=50,
        unique=True,
        blank=True
    )
    start_date = models.DateField(verbose_name=_("Start Date"))
    end_date = models.DateField(verbose_name=_("End Date"))
    status = models.CharField(
        verbose_name=_("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=DRAFT
    )
    total_pax = models.PositiveIntegerField(verbose_name=_("Total Pax"), default=0)
    notes = models.TextField(verbose_name=_("Notes"), blank=True, null=True)
    created_at = models.DateTimeField(verbose_name=_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Updated At"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError(_("End date cannot be before start date"))

    def save(self, *args, **kwargs):
        from .services import OperationService
        
        is_new = self.pk is None
        old_start_date = None
        old_end_date = None

        # Referans numarası oluşturma
        if not self.reference_number:
            if not self.pk or self.buyer_company.short_name != Operation.objects.get(pk=self.pk).buyer_company.short_name or self.start_date != Operation.objects.get(pk=self.pk).start_date:
                self.reference_number = OperationService.generate_reference_number(
                    self.buyer_company.short_name,
                    self.start_date
                )

        # Gün oluşturma işlemleri
        if not is_new:
            old_instance = Operation.objects.get(pk=self.pk)
            old_start_date = old_instance.start_date
            old_end_date = old_instance.end_date

        super().save(*args, **kwargs)

        # Yeni kayıt veya tarihler değişmişse günleri oluştur
        if is_new or old_start_date != self.start_date or old_end_date != self.end_date:
            OperationService.update_operation_days(
                self,
                is_new=is_new,
                old_start_date=old_start_date,
                old_end_date=old_end_date
            )

    def __str__(self):
        return f"{self.reference_number} - {self.buyer_company.name} (Follow by: {self.follow_by.get_full_name()})"

    class Meta:
        verbose_name = _("Operation")
        verbose_name_plural = _("Operations")
        ordering = ['-start_date', 'reference_number']

class OperationCustomer(models.Model):
    ADULT = 'ADULT'
    CHILD = 'CHILD'
    INFANT = 'INFANT'

    CUSTOMER_TYPE_CHOICES = [
        (ADULT, _('Yetişkin')),
        (CHILD, _('Çocuk')),
        (INFANT, _('Bebek')),
    ]

    operation = models.ForeignKey(Operation, verbose_name=_("Operation"), on_delete=models.CASCADE, related_name='customers')
    first_name = models.CharField(verbose_name=_("First Name"), max_length=100)
    last_name = models.CharField(verbose_name=_("Last Name"), max_length=100)
    customer_type = models.CharField(verbose_name=_("Customer Type"), max_length=20, choices=CUSTOMER_TYPE_CHOICES)
    birth_date = models.DateField(verbose_name=_("Birth Date"), null=True, blank=True)
    passport_no = models.CharField(verbose_name=_("Passport No"), max_length=50, null=True, blank=True)
    notes = models.TextField(verbose_name=_("Notes"), null=True, blank=True)
    created_at = models.DateTimeField(verbose_name=_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name=_("Updated At"), auto_now=True)
    is_active = models.BooleanField(verbose_name=_("Is Active"), default=True)
    is_buyer = models.BooleanField(verbose_name=_("Is Buyer"), default=False)
    contact_info = models.CharField(
        verbose_name=_("Contact Info"), 
        max_length=100, 
        null=True, 
        blank=True, 
        help_text=_("Phone number or email")
    )


    def get_full_name(self):
        """Müşterinin tam adını döndürür"""
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        self.clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Müşteri eklendiğinde veya silindiğinde total_pax'i güncelle
        if is_new or not self.is_active:
            from .services import CustomerService
            CustomerService.update_operation_total_pax(self.operation)

    def delete(self, *args, **kwargs):
        operation = self.operation
        super().delete(*args, **kwargs)

        # Müşteri silindiğinde total_pax'i güncelle
        from .services import CustomerService
        CustomerService.update_operation_total_pax(operation)

    class Meta:
        verbose_name = _("Operation Customer")
        verbose_name_plural = _("Operation Customers")

class OperationSalesPrice(models.Model):
    operation = models.ForeignKey(Operation, verbose_name="Operation", on_delete=models.CASCADE, related_name='sales_prices')
    price = models.DecimalField(verbose_name="Price", max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, verbose_name="Currency", on_delete=models.PROTECT)
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.operation.reference_number} - {self.price} {self.currency} Price"

class OperationDay(models.Model):
    operation = models.ForeignKey(Operation, verbose_name="Operation", on_delete=models.CASCADE, related_name='days')
    date = models.DateField(verbose_name="Date")
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.operation} - {self.date}"

    class Meta:
        ordering = ['date']

class OperationItem(models.Model):
    VEHICLE = 'VEHICLE'
    NO_VEHICLE_TOUR = 'NO_VEHICLE_TOUR'
    NO_VEHICLE_ACTIVITY = 'NO_VEHICLE_ACTIVITY'

    ITEM_TYPE_CHOICES = [
        (VEHICLE, 'Araçlı'),
        (NO_VEHICLE_TOUR, 'Araçsız Tur'),
        (NO_VEHICLE_ACTIVITY, 'Araçsız Aktivite'),
    ]

    operation_day = models.ForeignKey(OperationDay, verbose_name="Operation Day", on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(verbose_name="Item Type", max_length=20, choices=ITEM_TYPE_CHOICES)
    
    #ortak alanlar 1
    pick_time = models.TimeField(verbose_name="Pick Time", null=True, blank=True)
    pick_up_location = models.CharField(verbose_name="Pick Up Location", max_length=100, null=True, blank=True)
    drop_off_location = models.CharField(verbose_name="Drop Off Location", max_length=100, null=True, blank=True)
    
    #Seçim araç ise
    vehicle_type = models.ForeignKey(VehicleType, verbose_name="Vehicle Type", on_delete=models.PROTECT, null=True, blank=True)
    vehicle_supplier = models.ForeignKey(VehicleSupplier, verbose_name="Vehicle Supplier", on_delete=models.PROTECT, null=True, blank=True)
    vehicle_cost = models.ForeignKey(VehicleCost, verbose_name="Vehicle Cost", on_delete=models.CASCADE, null=True, blank=True)
    driver_name = models.CharField(verbose_name="Driver Name", max_length=100, null=True, blank=True)
    driver_phone = models.CharField(verbose_name="Driver Phone", max_length=100, null=True, blank=True)
    vehicle_plate_no = models.CharField(verbose_name="Vehicle Plate No", max_length=100, null=True, blank=True)

    #Seçim araçsız tur ise
    no_vehicle_tour = models.ForeignKey(NoVehicleTour, verbose_name="No Vehicle Tour", on_delete=models.PROTECT, null=True, blank=True)

    #seçim araçsız aktivite ise
    no_vehicle_activity = models.ForeignKey(Activity, verbose_name="No Vehicle Activity", on_delete=models.PROTECT, null=True, blank=True)
    activity_supplier = models.ForeignKey(ActivitySupplier, verbose_name="Activity Supplier", on_delete=models.PROTECT, null=True, blank=True)
    activity_cost = models.ForeignKey(ActivityCost, verbose_name="Activity Cost", on_delete=models.CASCADE, null=True, blank=True)

    #ortak alanlar 2
    notes = models.TextField(verbose_name="Notes", null=True, blank=True)
    sales_price = models.DecimalField(verbose_name="Sales Price", max_digits=10, decimal_places=2, blank=True, null=True)
    sales_currency = models.ForeignKey(Currency, verbose_name="Sales Currency", related_name='item_sales_currency', on_delete=models.PROTECT, null=True, blank=True)
    cost_price = models.DecimalField(verbose_name="Cost Price", max_digits=10, decimal_places=2, blank=True, null=True)
    cost_currency = models.ForeignKey(Currency, verbose_name="Cost Currency", related_name='item_cost_currency', on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)


    def __str__(self):
        return f"{self.operation_day} - {self.get_item_type_display()}"

    class Meta:
        verbose_name = "Operation Item"
        verbose_name_plural = "Operation Items"
        ordering = ['pick_time']

class OperationSubItem(models.Model):
    TOUR = 'TOUR'
    TRANSFER = 'TRANSFER'
    ACTIVITY = 'ACTIVITY'
    MUSEUM = 'MUSEUM'
    HOTEL = 'HOTEL'
    GUIDE = 'GUIDE'
    OTHER_PRICE = 'OTHER_PRICE'

    ROOM_TYPE_CHOICES = [
        ('SINGLE', 'Tek Kişilik'),
        ('DOUBLE', 'Çift Kişilik'),
        ('TRIPLE', 'Aile'),
    ]
    SUBITEM_TYPE_CHOICES = [
        (TOUR, 'Tur'),
        (TRANSFER, 'Transfer'),
        (ACTIVITY, 'Aktivite'),
        (MUSEUM, 'Müze'),
        (HOTEL, 'Otel'),
        (GUIDE, 'Rehber'),
        (OTHER_PRICE, 'Diğer Ücret'),
    ]

    operation_item = models.ForeignKey(OperationItem, verbose_name="Operation Item", on_delete=models.CASCADE, related_name='subitems')
    ordering = models.PositiveIntegerField(verbose_name="Ordering")
    subitem_type = models.CharField(verbose_name="Subitem Type", max_length=20, choices=SUBITEM_TYPE_CHOICES)

    tour = models.ForeignKey(Tour, verbose_name="Tour", on_delete=models.PROTECT, null=True, blank=True)

    transfer = models.ForeignKey(Transfer, verbose_name="Transfer", on_delete=models.PROTECT, null=True, blank=True)

    museums = models.ManyToManyField(Museum, verbose_name="Museums", blank=True, related_name='museums')

    hotel = models.ForeignKey(Hotel, verbose_name="Hotel", on_delete=models.PROTECT, null=True, blank=True)
    room_type = models.CharField(verbose_name="Room Type", max_length=20, choices=ROOM_TYPE_CHOICES, null=True, blank=True)

    is_guide = models.BooleanField(verbose_name="Is Guide", default=False)
    guide = models.ForeignKey(Guide, verbose_name="Guide", on_delete=models.PROTECT, null=True, blank=True)

    activity = models.ForeignKey(Activity, verbose_name="Activity", on_delete=models.PROTECT, null=True, blank=True)
    activity_supplier = models.ForeignKey(ActivitySupplier, verbose_name="Activity Supplier", on_delete=models.PROTECT, null=True, blank=True)
    activity_cost = models.ForeignKey(ActivityCost, verbose_name="Activity Cost", on_delete=models.CASCADE, null=True, blank=True)

    other_price_description = models.CharField(verbose_name="Other Price Description", max_length=255, null=True, blank=True)

    notes = models.TextField(verbose_name="Notes", null=True, blank=True)

    sales_price = models.DecimalField(verbose_name="Sales Price", max_digits=10, decimal_places=2, blank=True, null=True)
    sales_currency = models.ForeignKey(Currency, verbose_name="Sales Currency", related_name='subitem_sales_currency', on_delete=models.PROTECT, null=True, blank=True)
    cost_price = models.DecimalField(verbose_name="Cost Price", max_digits=10, decimal_places=2, blank=True, null=True)
    cost_currency = models.ForeignKey(Currency, verbose_name="Cost Currency", related_name='subitem_cost_currency', on_delete=models.PROTECT, null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated At", auto_now=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)


    def __str__(self):
        return f"{self.operation_item} - {self.get_subitem_type_display()}"

    class Meta:
        ordering = ['ordering']

class Support(models.Model):
    user = models.ForeignKey(CustomUser, verbose_name="User", on_delete=models.CASCADE)
    subject = models.CharField(verbose_name="Subject", max_length=255)
    message = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.user} - {self.subject}"

class SupportMessage(models.Model):
    support = models.ForeignKey(Support, verbose_name="Support", on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, verbose_name="Sender", on_delete=models.CASCADE)
    message = models.TextField(verbose_name="Message")
    created_at = models.DateTimeField(verbose_name="Created At", auto_now_add=True)
    is_active = models.BooleanField(verbose_name="Is Active", default=True)

    def __str__(self):
        return f"{self.support} - {self.sender}"



