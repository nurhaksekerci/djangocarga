from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import date, timedelta
import re
from .models import (
    Operation, OperationDay, OperationCustomer,
    Hotel, HotelPriceHistory, Museum, MuseumPriceHistory,
    VehicleCost, VehicleCostHistory, ActivityCost, ActivityCostHistory,
    CustomUser
)
import requests
import random
import string

class LoginService:
    @staticmethod
    def authenticate_user(username, password):
        """Kullanıcı girişini doğrular"""
        try:
            user = CustomUser.objects.get(username=username)
            if user.check_password(password):
                return user
            return None
        except CustomUser.DoesNotExist:
            return None

    @staticmethod
    def create_user(username, password, email, first_name, last_name, role='employee', **kwargs):
        """Yeni kullanıcı oluşturur"""
        user = CustomUser.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            **kwargs
        )
        return user

    @staticmethod
    def update_user(user, **kwargs):
        """Kullanıcı bilgilerini günceller"""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        user.save()
        return user

    @staticmethod
    def deactivate_user(user):
        """Kullanıcıyı deaktif eder"""
        user.is_active = False
        user.save()
        return user

    @staticmethod
    def activate_user(user):
        """Kullanıcıyı aktif eder"""
        user.is_active = True
        user.save()
        return user

class OperationService:
    @staticmethod
    def generate_reference_number(buyer_company_short_name, start_date):
        """Benzersiz referans numarası oluşturur"""
        tarih_format = start_date.strftime("%d%m%y")
        tur_sayisi = 1
        
        while True:
            potansiyel_referans = f"{buyer_company_short_name}{tarih_format}{str(tur_sayisi).zfill(3)}"
            if not Operation.objects.filter(reference_number=potansiyel_referans).exists():
                return potansiyel_referans
            tur_sayisi += 1

    @staticmethod
    def update_operation_days(operation, is_new=False, old_start_date=None, old_end_date=None):
        """Operasyon günlerini günceller"""
        if is_new:
            # Yeni kayıt için tüm günleri oluştur
            OperationDay.objects.bulk_create([
                OperationDay(
                    operation=operation,
                    date=current_date,
                    is_active=True
                )
                for current_date in [
                    operation.start_date + timedelta(days=x)
                    for x in range((operation.end_date - operation.start_date).days + 1)
                ]
            ])
        else:
            # Sadece değişen günleri güncelle
            OperationDay.objects.filter(
                operation=operation,
                date__lt=min(old_start_date, operation.start_date)
            ).delete()
            
            OperationDay.objects.filter(
                operation=operation,
                date__gt=max(old_end_date, operation.end_date)
            ).delete()

            # Yeni günleri ekle
            current_date = operation.start_date
            while current_date <= operation.end_date:
                if not OperationDay.objects.filter(
                    operation=operation,
                    date=current_date
                ).exists():
                    OperationDay.objects.create(
                        operation=operation,
                        date=current_date,
                        is_active=True
                    )
                current_date += timedelta(days=1)

class CustomerService:
    @staticmethod
    def validate_customer(customer):
        """Müşteri validasyonlarını gerçekleştirir"""
        # Satın alan kontrolü
        if customer.pk:  # Sadece kayıtlı müşteriler için kontrol yap
            if not customer.is_buyer and not customer.operation.customers.filter(is_buyer=True).exists():
                raise ValidationError(_("En az bir müşteri satın alan olarak işaretlenmelidir."))

        # Satın alan kişinin iletişim bilgisi zorunlu
        if customer.is_buyer and not customer.contact_info:
            raise ValidationError(_("Contact info is required for buyer"))

        # Doğum tarihi kontrolü
        if customer.birth_date:
            today = date.today()
            age = today.year - customer.birth_date.year - ((today.month, today.day) < (customer.birth_date.month, customer.birth_date.day))
            
            if customer.customer_type == customer.ADULT and age < 18:
                raise ValidationError(_("Yetişkin müşteri için yaş 18'den büyük olmalıdır."))
            elif customer.customer_type == customer.CHILD and (age < 2 or age >= 18):
                raise ValidationError(_("Çocuk müşteri için yaş 2-17 arasında olmalıdır."))
            elif customer.customer_type == customer.INFANT and age >= 2:
                raise ValidationError(_("Bebek müşteri için yaş 2'den küçük olmalıdır."))



    @staticmethod
    def update_operation_total_pax(operation):
        """Operasyon toplam kişi sayısını günceller"""
        active_customers = OperationCustomer.objects.filter(
            operation=operation,
            is_active=True
        ).count()

        operation.total_pax = active_customers
        operation.save(update_fields=['total_pax'])

class PriceHistoryService:
    @staticmethod
    def create_hotel_price_history(hotel):
        """Otel fiyat geçmişi oluşturur"""
        HotelPriceHistory.objects.create(
            hotel=hotel,
            currency=hotel.currency,
            valid_from=timezone.now().date(),
            valid_until=hotel.valid_until,
            single_price=hotel.single_price,
            double_price=hotel.double_price,
            triple_price=hotel.triple_price
        )

    @staticmethod
    def update_hotel_price_history(hotel, old_instance):
        """Otel fiyat geçmişini günceller"""
        if (old_instance.single_price != hotel.single_price or 
            old_instance.double_price != hotel.double_price or
            old_instance.triple_price != hotel.triple_price or
            old_instance.currency != hotel.currency):
            
            HotelPriceHistory.objects.filter(
                hotel=hotel,
                valid_until__gte=timezone.now().date()
            ).update(valid_until=timezone.now().date())
            
            HotelPriceHistory.objects.create(
                hotel=hotel,
                currency=hotel.currency,
                valid_from=timezone.now().date(),
                valid_until=hotel.valid_until,
                single_price=hotel.single_price,
                double_price=hotel.double_price,
                triple_price=hotel.triple_price
            )

    @staticmethod
    def create_museum_price_history(museum):
        """Müze fiyat geçmişi oluşturur"""
        MuseumPriceHistory.objects.create(
            museum=museum,
            currency=museum.currency,
            valid_from=timezone.now().date(),
            valid_until=museum.valid_until,
            local_price=museum.local_price,
            foreign_price=museum.foreign_price
        )

    @staticmethod
    def update_museum_price_history(museum, old_instance):
        """Müze fiyat geçmişini günceller"""
        if (old_instance.local_price != museum.local_price or 
            old_instance.foreign_price != museum.foreign_price or
            old_instance.currency != museum.currency):
            
            MuseumPriceHistory.objects.filter(
                museum=museum,
                valid_until__gte=timezone.now().date()
            ).update(valid_until=timezone.now().date())
            
            MuseumPriceHistory.objects.create(
                museum=museum,
                currency=museum.currency,
                valid_from=timezone.now().date(),
                valid_until=museum.valid_until,
                local_price=museum.local_price,
                foreign_price=museum.foreign_price
            )

    @staticmethod
    def create_vehicle_cost_history(vehicle_cost):
        """Araç maliyet geçmişi oluşturur"""
        VehicleCostHistory.objects.create(
            vehicle_cost=vehicle_cost,
            currency=vehicle_cost.currency,
            valid_from=timezone.now().date(),
            valid_until=vehicle_cost.valid_until,
            car_cost=vehicle_cost.car_cost,
            minivan_cost=vehicle_cost.minivan_cost,
            minibus_cost=vehicle_cost.minibus_cost,
            midibus_cost=vehicle_cost.midibus_cost,
            bus_cost=vehicle_cost.bus_cost
        )

    @staticmethod
    def update_vehicle_cost_history(vehicle_cost, old_instance):
        """Araç maliyet geçmişini günceller"""
        if (old_instance.car_cost != vehicle_cost.car_cost or 
            old_instance.minivan_cost != vehicle_cost.minivan_cost or
            old_instance.minibus_cost != vehicle_cost.minibus_cost or
            old_instance.midibus_cost != vehicle_cost.midibus_cost or
            old_instance.bus_cost != vehicle_cost.bus_cost or
            old_instance.currency != vehicle_cost.currency):
            
            VehicleCostHistory.objects.filter(
                vehicle_cost=vehicle_cost,
                valid_until__gte=timezone.now().date()
            ).update(valid_until=timezone.now().date())
            
            VehicleCostHistory.objects.create(
                vehicle_cost=vehicle_cost,
                currency=vehicle_cost.currency,
                valid_from=timezone.now().date(),
                valid_until=vehicle_cost.valid_until,
                car_cost=vehicle_cost.car_cost,
                minivan_cost=vehicle_cost.minivan_cost,
                minibus_cost=vehicle_cost.minibus_cost,
                midibus_cost=vehicle_cost.midibus_cost,
                bus_cost=vehicle_cost.bus_cost
            )

    @staticmethod
    def create_activity_cost_history(activity_cost):
        """Aktivite maliyet geçmişi oluşturur"""
        ActivityCostHistory.objects.create(
            activity_cost=activity_cost,
            currency=activity_cost.currency,
            valid_from=timezone.now().date(),
            valid_until=activity_cost.valid_until,
            price=activity_cost.price
        )

    @staticmethod
    def update_activity_cost_history(activity_cost, old_instance):
        """Aktivite maliyet geçmişini günceller"""
        if (old_instance.price != activity_cost.price or 
            old_instance.currency != activity_cost.currency):
            
            ActivityCostHistory.objects.filter(
                activity_cost=activity_cost,
                valid_until__gte=timezone.now().date()
            ).update(valid_until=timezone.now().date())
            
            ActivityCostHistory.objects.create(
                activity_cost=activity_cost,
                currency=activity_cost.currency,
                valid_from=timezone.now().date(),
                valid_until=activity_cost.valid_until,
                price=activity_cost.price
            ) 

def sms(phone, mesaj):
    url = "https://api.netgsm.com.tr/sms/send/xml"
    headers = {'Content-Type': 'application/xml'}
    usercode = "8503081334"
    password = "F#D6C7B"
    appkey = "xxxx"
    
    # Sunucu IP'sini al
    try:
        response = requests.get('https://api.ipify.org?format=json')
        print(f"Sunucu IP: {response.json()['ip']}")
    except:
        print("IP adresi alınamadı")
    
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
        <mainbody>
           <header>
            <company>Netgsm</company>
               <usercode>{usercode}</usercode>
               <password>{password}</password>
               <type>n:n</type>
               <appkey>{appkey}</appkey>
               <msgheader>MNC GROUP</msgheader>
           </header>
           <body>
               <mp><msg><![CDATA[{mesaj}]]></msg><no>{phone}</no></mp>
           </body>
        </mainbody>"""

    try:
        response = requests.post(url, data=body, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        print(f"Request Body: {body}")
        response.raise_for_status()
        return True, "SMS başarıyla gönderildi"
    except requests.exceptions.RequestException as e:
        print(f"SMS gönderimi sırasında hata oluştu: {e}")
        return False, f"SMS gönderilemedi: {str(e)}"

def generate_reset_code():
    """6 haneli rastgele kod oluşturur"""
    return ''.join(random.choices(string.digits, k=6))

class PasswordResetService:
    @staticmethod
    def send_reset_code(phone):
        """Telefon numarasına parola sıfırlama kodu gönderir"""
        try:
            user = CustomUser.objects.get(phone=phone)
            if not user.is_active:
                return False, _("Bu hesap aktif değil.")
            
            # Rastgele kod oluştur
            reset_code = generate_reset_code()
            
            # Kodu kullanıcıya kaydet
            user.reset_code = reset_code
            user.reset_code_created_at = timezone.now()
            user.save()
            
            # SMS mesajını hazırla
            message = f"Parola sıfırlama kodunuz: {reset_code}\nBu kod 10 dakika geçerlidir."
            
            # SMS gönder
            success, sms_message = sms(phone, message)
            
            if success:
                return True, _("Parola sıfırlama kodu telefonunuza gönderildi.")
            else:
                return False, sms_message
                
        except CustomUser.DoesNotExist:
            return False, _("Bu telefon numarası ile kayıtlı kullanıcı bulunamadı.")
        except Exception as e:
            return False, str(e)

    @staticmethod
    def verify_reset_code(phone, code):
        """Parola sıfırlama kodunu doğrular"""
        try:
            user = CustomUser.objects.get(phone=phone)
            
            # Kodun geçerlilik süresini kontrol et (10 dakika)
            if not user.reset_code or not user.reset_code_created_at:
                return False, _("Geçersiz kod.")
                
            if timezone.now() - user.reset_code_created_at > timedelta(minutes=10):
                return False, _("Kodun süresi dolmuş.")
                
            if user.reset_code != code:
                return False, _("Geçersiz kod.")
                
            return True, user
            
        except CustomUser.DoesNotExist:
            return False, _("Kullanıcı bulunamadı.")
        except Exception as e:
            return False, str(e)

    @staticmethod
    def reset_password(phone, code, new_password):
        """Parolayı sıfırlar"""
        try:
            # Önce kodu doğrula
            success, result = PasswordResetService.verify_reset_code(phone, code)
            
            if not success:
                return False, result
                
            user = result
            
            # Parolayı güncelle
            user.set_password(new_password)
            user.reset_code = None
            user.reset_code_created_at = None
            user.save()
            
            return True, _("Parolanız başarıyla güncellendi.")
        except Exception as e:
            return False, str(e)
