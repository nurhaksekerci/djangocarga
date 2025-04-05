import json
import os
import re
from django.core.management.base import BaseCommand
from django.db.models import Q
from tour.models import VehicleSupplier, City

class Command(BaseCommand):
    help = 'vehicle_supplier.json dosyasındaki araç tedarikçi verilerini veritabanına kaydeder'

    def guess_city_from_name(self, supplier_name):
        """Tedarikçi adından şehri tahmin et"""
        city_hints = {
            'KAPADOKYA': '50',  # Nevşehir
            'CAPPADOCIA': '50', # Nevşehir
            'FETHİYE': '48',    # Muğla
            'FETHIYE': '48',    # Muğla
            'BODRUM': '48',     # Muğla
            'DALAMAN': '48',    # Muğla
            'ANTALYA': '07',    # Antalya
            'AYT': '07',        # Antalya
            'PAMUKKALE': '20',  # Denizli
            'İSTANBUL': '34',   # İstanbul
            'ISTANBUL': '34',   # İstanbul
            'URGUP': '50',      # Nevşehir
            'ÜRGÜP': '50',      # Nevşehir
            'IZMIR': '35',      # İzmir
            'İZMİR': '35',      # İzmir
            'ANKARA': '06',     # Ankara
            'KONYA': '42',      # Konya
        }

        supplier_name = supplier_name.upper()
        for hint, code in city_hints.items():
            if hint in supplier_name:
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
        json_file_path = os.path.join('data', 'vehicle_supplier.json')
        
        try:
            # JSON dosyasını oku
            with open(json_file_path, 'r', encoding='utf-8') as file:
                suppliers = json.load(file)
            
            # Mevcut tedarikçileri temizle
            self.stdout.write('Mevcut araç tedarikçileri temizleniyor...')
            VehicleSupplier.objects.all().delete()
            
            # Tedarikçileri ekle
            self.stdout.write('Araç tedarikçileri ekleniyor...')
            added_count = 0
            skipped_count = 0
            
            for supplier_data in suppliers:
                # Tedarikçi adından şehri tahmin et
                city = self.guess_city_from_name(supplier_data['name'])
                
                # Tedarikçiyi oluştur
                supplier = VehicleSupplier.objects.create(
                    name=supplier_data['name']
                )
                
                # Şehir bulunduysa ekle
                if city:
                    supplier.cities.add(city)
                    self.stdout.write(f"{supplier_data['name']} ({city}) eklendi.")
                else:
                    self.stdout.write(f"{supplier_data['name']} (şehir bulunamadı) eklendi.")
                
                added_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Tüm araç tedarikçileri işlendi! {added_count} tedarikçi eklendi, {skipped_count} tedarikçi atlandı.'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası bulunamadı!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası geçerli bir JSON formatında değil!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hata: {str(e)}')) 