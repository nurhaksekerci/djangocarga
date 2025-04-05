import json
import os
import re
from django.core.management.base import BaseCommand
from django.db.models import Q
from tour.models import Tour, City

class Command(BaseCommand):
    help = 'tour.json dosyasındaki tur verilerini veritabanına kaydeder'

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
            'İstanbul (Avrupa)': '83',
            'İstanbul (Anadolu)': '82',
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
        json_file_path = os.path.join('data', 'tour.json')
        
        try:
            # JSON dosyasını oku
            with open(json_file_path, 'r', encoding='utf-8') as file:
                tours = json.load(file)
            
            # Mevcut turları temizle
            self.stdout.write('Mevcut turlar temizleniyor...')
            Tour.objects.all().delete()
            
            # Turları ekle
            self.stdout.write('Turlar ekleniyor...')
            added_count = 0
            skipped_count = 0
            
            for tour_data in tours:
                # Başlangıç ve bitiş şehirlerini kontrol et
                if tour_data['start_city'] is None or tour_data['finish_city'] is None:
                    self.stdout.write(self.style.WARNING(f"Uyarı: {tour_data['route']} turu için başlangıç veya bitiş şehri belirtilmemiş. Atlanıyor."))
                    skipped_count += 1
                    continue
                
                # Şehirleri bul
                start_city = self.find_city(tour_data['start_city'])
                end_city = self.find_city(tour_data['finish_city'])
                
                if start_city is None or end_city is None:
                    self.stdout.write(self.style.ERROR(f"Hata: {tour_data['route']} turu için şehir bulunamadı: Başlangıç={tour_data['start_city']}, Bitiş={tour_data['finish_city']}"))
                    skipped_count += 1
                    continue
                
                # Turu oluştur
                Tour.objects.create(
                    name=tour_data['route'],
                    start_city=start_city,
                    end_city=end_city
                )
                
                self.stdout.write(f"{tour_data['route']} ({start_city} - {end_city}) eklendi.")
                added_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Tüm turlar işlendi! {added_count} tur eklendi, {skipped_count} tur atlandı.'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası bulunamadı!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası geçerli bir JSON formatında değil!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hata: {str(e)}')) 