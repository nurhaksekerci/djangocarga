import json
import os
from datetime import date
from django.core.management.base import BaseCommand
from django.db.models import Q
from tour.models import VehicleCost, VehicleSupplier, Tour, Transfer, Currency

class Command(BaseCommand):
    help = 'vehicle_cost.json dosyasındaki araç maliyet verilerini veritabanına kaydeder'

    def normalize_name(self, name):
        """İsmi normalleştirir"""
        if not name:
            return None
        return name.strip().upper()

    def find_tour(self, tour_name):
        """Tur adına göre Tour objesini bulur"""
        if not tour_name:
            return None
            
        normalized_name = self.normalize_name(tour_name)
        
        # Özel durumlar
        special_cases = {
            'GUNLUK TUR IST': 'ISTANBUL GUNLUK TUR',
            'LD TUR + IST': 'ISTANBUL LONG DAY TUR',
            'IST + LD TUR': 'ISTANBUL LONG DAY TUR',
            'TUR + IST TRANSFER': 'ISTANBUL GUNLUK TUR',
            'IST TRANSFER + TUR': 'ISTANBUL GUNLUK TUR',
            'LD KISA TUR IST': 'ISTANBUL LONG DAY TUR',
            'KAPADOKYA GUNLUK TUR': 'CAPPADOCIA DAILY TOUR',
            'FETHİYE GÜNLÜK TUR': 'FETHIYE DAILY TOUR',
            'ANTALYA GUNLUK TUR': 'ANTALYA DAILY TOUR',
            'BODRUM GÜNLÜK TUR': 'BODRUM DAILY TOUR',
            'IZMIR GUNLUK TUR': 'IZMIR DAILY TOUR',
            'ANKARA GÜNLÜK TUR': 'ANKARA DAILY TOUR',
            'KONYA GÜNLÜK TUR': 'KONYA DAILY TOUR'
        }
        
        if normalized_name in special_cases:
            normalized_name = special_cases[normalized_name]
            
        try:
            # Tam eşleşme ara
            return Tour.objects.get(name__iexact=normalized_name)
        except Tour.DoesNotExist:
            try:
                # Benzer isimli turu ara
                return Tour.objects.filter(name__icontains=normalized_name).first()
            except:
                return None

    def find_transfer(self, transfer_name):
        """Transfer adına göre Transfer objesini bulur"""
        if not transfer_name:
            return None
            
        normalized_name = self.normalize_name(transfer_name)
        
        # Özel durumlar
        special_cases = {
            'AVR OTEL-IST': 'ISTANBUL AIRPORT-HOTEL EUROPE',
            'IST-AVR OTEL': 'HOTEL EUROPE-ISTANBUL AIRPORT',
            'SAW-AVR OTEL': 'SABIHA AIRPORT-HOTEL EUROPE',
            'AVR OTEL-SAW': 'HOTEL EUROPE-SABIHA AIRPORT',
            'AND OTEL-IST': 'ISTANBUL AIRPORT-HOTEL ASIA',
            'IST-AND OTEL': 'HOTEL ASIA-ISTANBUL AIRPORT',
            'SAW-AND OTEL': 'SABIHA AIRPORT-HOTEL ASIA',
            'AYT-OTEL': 'ANTALYA AIRPORT-HOTEL',
            'OTEL-AYT': 'HOTEL-ANTALYA AIRPORT',
            'DLM-FETHIYE': 'DALAMAN AIRPORT-FETHIYE',
            'FETHIYE-DLM': 'FETHIYE-DALAMAN AIRPORT',
            'ESB-OTEL': 'ANKARA AIRPORT-HOTEL',
            'OTEL-ESB': 'HOTEL-ANKARA AIRPORT',
            'ADB-OTEL': 'IZMIR AIRPORT-HOTEL',
            'OTEL-ADB': 'HOTEL-IZMIR AIRPORT',
            'BJV-OTEL': 'BODRUM AIRPORT-HOTEL',
            'OTEL-BJV': 'HOTEL-BODRUM AIRPORT'
        }
        
        if normalized_name in special_cases:
            normalized_name = special_cases[normalized_name]
            
        try:
            # Tam eşleşme ara
            return Transfer.objects.get(name__iexact=normalized_name)
        except Transfer.DoesNotExist:
            try:
                # Benzer isimli transferi ara
                return Transfer.objects.filter(name__icontains=normalized_name).first()
            except:
                return None

    def handle(self, *args, **options):
        # JSON dosyasının yolu
        json_file_path = os.path.join('data', 'vehicle_cost.json')
        
        try:
            # JSON dosyasını oku
            with open(json_file_path, 'r', encoding='utf-8') as file:
                costs = json.load(file)
            
            # Mevcut maliyetleri temizle
            self.stdout.write('Mevcut araç maliyetleri temizleniyor...')
            VehicleCost.objects.all().delete()
            
            # Varsayılan para birimini al (TRY)
            try:
                currency = Currency.objects.get(code='TRY')
            except Currency.DoesNotExist:
                self.stdout.write(self.style.ERROR('Hata: TRY para birimi bulunamadı!'))
                return
            
            # Maliyetleri ekle
            self.stdout.write('Araç maliyetleri ekleniyor...')
            added_count = 0
            skipped_count = 0
            error_count = 0
            
            for cost_data in costs:
                # Boş kayıtları atla
                if not cost_data['supplier']:
                    skipped_count += 1
                    continue
                
                # Tedarikçiyi bul
                try:
                    supplier = VehicleSupplier.objects.get(name=cost_data['supplier'])
                except VehicleSupplier.DoesNotExist:
                    self.stdout.write(f"Hata: {cost_data['supplier']} tedarikçisi bulunamadı!")
                    error_count += 1
                    continue
                
                # Tur veya transfer bul
                tour = self.find_tour(cost_data['tour'])
                transfer = self.find_transfer(cost_data['transfer'])
                
                # En az birinin bulunması gerekiyor
                if not tour and not transfer:
                    self.stdout.write(f"Hata: {cost_data['supplier']} için tur/transfer bulunamadı!")
                    error_count += 1
                    continue
                
                # Maliyet değerlerini kontrol et ve varsayılan 0 ata
                car_cost = cost_data.get('car', 0) or 0
                minivan_cost = cost_data.get('minivan', 0) or 0
                minibus_cost = cost_data.get('minibus', 0) or 0
                midibus_cost = cost_data.get('midibus', 0) or 0
                bus_cost = cost_data.get('bus', 0) or 0
                
                # Tüm maliyetler 0 ise atla
                if not any([car_cost, minivan_cost, minibus_cost, midibus_cost, bus_cost]):
                    skipped_count += 1
                    continue
                
                try:
                    # Eğer hem tur hem transfer varsa, iki ayrı kayıt oluştur
                    if tour and transfer:
                        # Önce tur kaydını oluştur
                        VehicleCost.objects.create(
                            supplier=supplier,
                            tour=tour,
                            transfer=None,
                            car_cost=car_cost,
                            minivan_cost=minivan_cost,
                            minibus_cost=minibus_cost,
                            midibus_cost=midibus_cost,
                            bus_cost=bus_cost,
                            currency=currency,
                            valid_until=date(2024, 12, 31),
                            is_active=True
                        )
                        added_count += 1
                        
                        # Sonra transfer kaydını oluştur
                        VehicleCost.objects.create(
                            supplier=supplier,
                            tour=None,
                            transfer=transfer,
                            car_cost=car_cost,
                            minivan_cost=minivan_cost,
                            minibus_cost=minibus_cost,
                            midibus_cost=midibus_cost,
                            bus_cost=bus_cost,
                            currency=currency,
                            valid_until=date(2024, 12, 31),
                            is_active=True
                        )
                        added_count += 1
                    else:
                        # Tek kayıt oluştur
                        VehicleCost.objects.create(
                            supplier=supplier,
                            tour=tour,
                            transfer=transfer,
                            car_cost=car_cost,
                            minivan_cost=minivan_cost,
                            minibus_cost=minibus_cost,
                            midibus_cost=midibus_cost,
                            bus_cost=bus_cost,
                            currency=currency,
                            valid_until=date(2024, 12, 31),
                            is_active=True
                        )
                        added_count += 1
                    
                    self.stdout.write(f"Maliyet eklendi: {supplier.name} - {tour.name if tour else transfer.name if transfer else 'N/A'}")
                    
                except Exception as e:
                    self.stdout.write(f"Hata: {str(e)}")
                    error_count += 1
                    continue
            
            self.stdout.write(self.style.SUCCESS(
                f'Tüm araç maliyetleri işlendi!\n'
                f'Eklenen: {added_count}\n'
                f'Atlanan: {skipped_count}\n'
                f'Hata: {error_count}'
            ))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası bulunamadı!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası geçerli bir JSON formatında değil!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hata: {str(e)}')) 