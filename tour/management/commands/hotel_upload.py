import json
import os
import re
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from tour.models import Hotel, City, Currency
from django.utils import timezone

class Command(BaseCommand):
    help = 'hotel.json dosyasındaki otel verilerini veritabanına kaydeder'

    def normalize_city_name(self, city_name):
        """Şehir ismini normalize eder"""
        if not city_name:
            return None
            
        # Parantez içindeki kısımları kaldır (örn: İstanbul (Avrupa) -> İstanbul)
        city_name = re.sub(r'\s*\([^)]*\)', '', city_name)
        
        # Boşlukları temizle
        city_name = city_name.strip()
        
        # Türkçe karakterleri normalize et
        city_name = city_name.replace('İ', 'I').replace('ı', 'i')
        
        return city_name

    def find_city(self, city_name):
        """Şehir ismine göre veritabanında şehir arar"""
        if not city_name:
            return None
            
        normalized_name = self.normalize_city_name(city_name)
        
        # Özel durumlar için eşleştirme (şehir kodlarına göre)
        special_cases = {
            # İstanbul (34)
            'İstanbul (Avrupa)': '34',
            'İstanbul (Anadolu)': '34',
            'İstanbul': '34',
            'IST': '34',
            'ISTANBUL': '34',
            
            # Nevşehir (50)
            'Kapadokya': '50',
            'Nevşehir': '50',
            'Nevsehir': '50',
            'NEVŞEHİR': '50',
            'NEVSEHIR': '50',
            
            # İzmir (35)
            'Kusadasi': '35',
            'Kuşadası': '35',
            'KUSDASI': '35',
            'KUSADASI': '35',
            'Kusadasi': '35',
            'Kuşadası': '35',
            'IZMIR': '35',
            'IZMIR': '35',
            'Efes': '35',
            'EFES': '35',
            'Alaçatı': '35',
            'ALACATI': '35',
            'Alaçatı': '35',
            'Çeşme': '35',
            'CESME': '35',
            'Çeşme': '35',
            'ADB': '35',
            'SELCUK': '35',
            'SIRINCE': '35',
            'ŞIRINCE': '35',
            
            # Muğla (48)
            'Fethiye': '48',
            'FETHIYE': '48',
            'Bodrum': '48',
            'BODRUM': '48',
            'DLM': '48',
            'ÖLÜDENİZ': '48',
            'OLUDENIZ': '48',
            
            # Antalya (07)
            'Kaş': '07',
            'KAS': '07',
            'Kaş': '07',
            'KAPUTAS': '07',
            'KAPUTAŞ': '07',
            'ANTALYA': '07',
            'ASPENDOS': '07',
            'KALEICI': '07',
            'KALEİÇİ': '07',
            'ANTIPHELLOS': '07',
            'KALKAN': '07',
            
            # Denizli (20)
            'Pamukkale': '20',
            'PAMUKKALE': '20',
            'DNZ': '20',
            'HIERAPOLIS': '20',
            
            # Diğer şehirler
            'Safranbolu': '78',  # Karabük
            'SAFRANBOLU': '78',
            'Ayvalik': '10',  # Balıkesir
            'AYVALIK': '10',
            'Ayvalık': '10',
            'Canakkale': '17',  # Çanakkale
            'CANAKKALE': '17',
            'Çanakkale': '17',
            'Konya': '42',
            'KONYA': '42',
            'Ankara': '06',
            'ANKARA': '06',
            'Bursa': '16',
            'BURSA': '16',
            'Balikesir': '10',  # Balıkesir
            'BALIKESIR': '10',
            'Balıkesir': '10',
            'Aydin': '09',  # Aydın
            'AYDIN': '09',
            'Aydın': '09',
            'Kayseri': '38',
            'KAYSERI': '38',
            'ASR': '38',  # Kayseri
            'ESB': '06',  # Ankara
        }
        
        # Özel durumları kontrol et
        for key, value in special_cases.items():
            if (normalized_name.lower() == key.lower() or 
                normalized_name.lower() in key.lower() or 
                key.lower() in normalized_name.lower()):
                try:
                    return City.objects.get(code=value)
                except City.DoesNotExist:
                    pass
                except City.MultipleObjectsReturned:
                    # Birden fazla eşleşme varsa, ilkini al
                    return City.objects.filter(code=value).first()
        
        # Tam eşleşme dene
        try:
            return City.objects.get(name=normalized_name)
        except City.DoesNotExist:
            pass
        except City.MultipleObjectsReturned:
            # Birden fazla eşleşme varsa, ilkini al
            return City.objects.filter(name=normalized_name).first()
            
        # Kısmi eşleşme dene
        try:
            return City.objects.get(name__icontains=normalized_name)
        except City.DoesNotExist:
            pass
        except City.MultipleObjectsReturned:
            # Birden fazla eşleşme varsa, ilkini al
            return City.objects.filter(name__icontains=normalized_name).first()
        
        # Son çare: Tüm şehirleri kontrol et
        for city in City.objects.all():
            if (normalized_name.lower() in city.name.lower() or 
                city.name.lower() in normalized_name.lower()):
                return city
        
        return None

    def handle(self, *args, **options):
        # JSON dosyasının yolu
        json_file_path = os.path.join('data', 'hotel.json')
        
        try:
            # JSON dosyasını oku
            with open(json_file_path, 'r', encoding='utf-8') as file:
                hotels = json.load(file)
            
            # Mevcut otelleri temizle
            self.stdout.write('Mevcut oteller temizleniyor...')
            Hotel.objects.all().delete()
            
            # Varsayılan para birimini al (TRY)
            try:
                default_currency = Currency.objects.get(code='TRY')
            except Currency.DoesNotExist:
                default_currency = Currency.objects.create(
                    name='Türk Lirası',
                    code='TRY',
                    symbol='₺'
                )
            
            # Geçerlilik tarihi için varsayılan değer (1 yıl sonrası)
            default_valid_until = timezone.now().date() + timedelta(days=365)
            
            # Otelleri ekle
            self.stdout.write('Oteller ekleniyor...')
            added_count = 0
            skipped_count = 0
            
            for hotel_data in hotels:
                # Şehri bul
                city = self.find_city(hotel_data['new_city'])
                
                if city is None:
                    self.stdout.write(self.style.ERROR(f"Hata: {hotel_data['name']} oteli için şehir bulunamadı: {hotel_data['new_city']}"))
                    skipped_count += 1
                    continue
                
                # Oteli oluştur
                hotel = Hotel.objects.create(
                    name=hotel_data['name'],
                    city=city,
                    single_price=0,  # Varsayılan değerler
                    double_price=0,
                    triple_price=0,
                    currency=default_currency,
                    valid_until=default_valid_until
                )
                
                self.stdout.write(f"{hotel_data['name']} ({city}) eklendi.")
                added_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Tüm oteller işlendi! {added_count} otel eklendi, {skipped_count} otel atlandı.'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası bulunamadı!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası geçerli bir JSON formatında değil!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hata: {str(e)}')) 