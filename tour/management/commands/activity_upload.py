import json
import os
import re
from django.core.management.base import BaseCommand
from django.db.models import Q
from tour.models import Activity, City

class Command(BaseCommand):
    help = 'activity.json dosyasındaki aktivite verilerini veritabanına kaydeder'

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
            'KAPADOKYA': '50',
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
            'FETHİYE': '48',
            'FETHIYE': '48',
            'Bodrum': '48',
            'BODRUM': '48',
            'DLM': '48',
            'ÖLÜDENİZ': '48',
            'OLUDENIZ': '48',
            
            # Antalya (07)
            'Kaş': '07',
            'KAŞ': '07',
            'KAS': '07',
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
            'Kayseri': '38',
            'KAYSERI': '38',
            'KAYSERİ': '38',
            'ASR': '38'  # Kayseri
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
        json_file_path = os.path.join('data', 'activity.json')
        
        try:
            # JSON dosyasını oku
            with open(json_file_path, 'r', encoding='utf-8') as file:
                activities = json.load(file)
            
            # Mevcut aktiviteleri temizle
            self.stdout.write('Mevcut aktiviteler temizleniyor...')
            Activity.objects.all().delete()
            
            # Aktiviteleri ekle
            self.stdout.write('Aktiviteler ekleniyor...')
            added_count = 0
            skipped_count = 0
            
            for activity_data in activities:
                # Şehri bul
                city = self.find_city(activity_data['city'])
                
                if city is None:
                    self.stdout.write(self.style.ERROR(f"Hata: {activity_data['name']} aktivitesi için şehir bulunamadı: {activity_data['city']}"))
                    skipped_count += 1
                    continue
                
                # Aktiviteyi oluştur
                activity = Activity.objects.create(
                    name=activity_data['name']
                )
                
                # Şehri ekle
                activity.cities.add(city)
                
                self.stdout.write(f"{activity_data['name']} ({city}) eklendi.")
                added_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Tüm aktiviteler işlendi! {added_count} aktivite eklendi, {skipped_count} aktivite atlandı.'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası bulunamadı!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası geçerli bir JSON formatında değil!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hata: {str(e)}')) 