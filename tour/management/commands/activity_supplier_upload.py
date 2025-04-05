import json
import os
import re
from django.core.management.base import BaseCommand
from django.db.models import Q
from tour.models import ActivitySupplier, City

class Command(BaseCommand):
    help = 'activity_supplier.json dosyasındaki tedarikçi verilerini veritabanına kaydeder'

    def guess_city_from_name(self, supplier_name):
        """Tedarikçi adından şehri tahmin et"""
        city_hints = {
            'KAPADOKYA': '50',  # Nevşehir
            'FETHİYE': '48',    # Muğla
            'FETHIYE': '48',    # Muğla
            'ANTALYA': '07',    # Antalya
            'PAMUKKALE': '20',  # Denizli
            'İSTANBUL': '34',   # İstanbul
            'ISTANBUL': '34',   # İstanbul
            'URGUP': '50',      # Nevşehir
            'ÜRGÜP': '50',      # Nevşehir
            'GÖREME': '50',     # Nevşehir
            'GOREME': '50',     # Nevşehir
            'BOSPHORUS': '34',  # İstanbul
            'BOĞAZ': '34',      # İstanbul
        }

        supplier_name = supplier_name.upper()
        for hint, code in city_hints.items():
            if hint in supplier_name:
                try:
                    return City.objects.get(code=code)
                except:
                    pass
        return None

    def guess_city_from_activity(self, supplier_name):
        """Tedarikçinin aktivite türünden şehri tahmin et"""
        activity_city_map = {
            'BALON': '50',      # Nevşehir (Kapadokya)
            'ATV': '50',        # Nevşehir (Kapadokya)
            'JEEP': '50',       # Nevşehir (Kapadokya)
            'PARASUT': '48',    # Muğla (Fethiye)
            'PARAŞÜT': '48',    # Muğla (Fethiye)
            'TEKNE': '48',      # Muğla (Fethiye)
            'YACHT': '34',      # İstanbul
            'YAT': '34',        # İstanbul
            'MEET&ASSIST': '34', # İstanbul
            'İGA': '34',        # İstanbul
            'SAW': '34',        # İstanbul (Sabiha Gökçen)
            'PEREME': '34',     # İstanbul
            'TURKISH NIGHT': '34', # İstanbul
            'TÜRK GECESİ': '50', # Nevşehir (Kapadokya)
            'DEVE': '50',       # Nevşehir (Kapadokya)
            'KLASIK ARABA': '50', # Nevşehir (Kapadokya)
            'CLASİC ARBA': '50', # Nevşehir (Kapadokya)
            'SHUTTLE': '50',    # Nevşehir (Kapadokya)
            'KAYAK': '38',      # Kayseri (Erciyes)
            'SEMA': '50',       # Nevşehir (Kapadokya)
            'HELİKOPTER': '34', # İstanbul
            'HELICOPTER': '34',  # İstanbul
            'SPA': '50',        # Nevşehir (Kapadokya)
        }

        supplier_name = supplier_name.upper()
        for activity, code in activity_city_map.items():
            if activity in supplier_name:
                try:
                    return City.objects.get(code=code)
                except:
                    pass
        return None

    def normalize_phone(self, phone):
        """Telefon numarasını normalize eder"""
        if not phone:
            return ""
            
        # Sadece rakamları al
        phone = re.sub(r'\D', '', phone)
        
        # Başında 0 varsa kaldır
        if phone.startswith('0'):
            phone = phone[1:]
            
        # Başında +90 varsa kaldır
        if phone.startswith('90'):
            phone = phone[2:]
            
        return phone

    def handle(self, *args, **options):
        # JSON dosyasının yolu
        json_file_path = os.path.join('data', 'activity_supplier.json')
        
        try:
            # JSON dosyasını oku
            with open(json_file_path, 'r', encoding='utf-8') as file:
                suppliers = json.load(file)
            
            # Mevcut tedarikçileri temizle
            self.stdout.write('Mevcut tedarikçiler temizleniyor...')
            ActivitySupplier.objects.all().delete()
            
            # Tedarikçileri ekle
            self.stdout.write('Tedarikçiler ekleniyor...')
            added_count = 0
            skipped_count = 0
            
            for supplier_data in suppliers:
                # Önce tedarikçi adından şehri tahmin et
                city = self.guess_city_from_name(supplier_data['name'])
                
                # Bulunamadıysa aktivite türünden tahmin et
                if city is None:
                    city = self.guess_city_from_activity(supplier_data['name'])
                
                # Tedarikçiyi oluştur
                supplier = ActivitySupplier.objects.create(
                    name=supplier_data['name']
                )
                
                # Şehir bulunduysa ekle
                if city:
                    supplier.cities.add(city)
                    self.stdout.write(f"{supplier_data['name']} ({city}) eklendi.")
                else:
                    self.stdout.write(f"{supplier_data['name']} (şehir bulunamadı) eklendi.")
                
                added_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Tüm tedarikçiler işlendi! {added_count} tedarikçi eklendi, {skipped_count} tedarikçi atlandı.'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası bulunamadı!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası geçerli bir JSON formatında değil!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hata: {str(e)}')) 