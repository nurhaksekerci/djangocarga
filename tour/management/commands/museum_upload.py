import json
import os
import re
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Q
from tour.models import Museum, City, Currency
from django.utils import timezone

class Command(BaseCommand):
    help = 'museum.json dosyasındaki müze verilerini veritabanına kaydeder'

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
            'ESB': '06',  # Ankara,
            'Adana': '01',
            'Afyonkarahisar': '03',
            'Aksaray': '68',
            'Diyarbakır': '21',
            'Gaziantep': '27',
            'Hatay': '31',
            'Kars': '36',
            'Mersin': '33',
            'Şanlıurfa': '63',
            'Van': '65',
            'Trabzon': '61'
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

    def guess_city_from_name(self, museum_name):
        """Müze adından şehri tahmin et"""
        city_hints = {
            'ADANA': '01',
            'AFYONKARAHİSAR': '03',
            'ANKARA': '06',
            'ANTALYA': '07',
            'ALANYA': '07',
            'ASPENDOS': '07',
            'MYRA': '07',
            'OLYMPOS': '07',
            'PATARA': '07',
            'PERGE': '07',
            'PHASELİS': '07',
            'SAGALASSOS': '07',
            'SİDE': '07',
            'MİLET': '09',  # Aydın
            'DİDİM': '09',
            'ASSOS': '17',  # Çanakkale
            'TROİA': '17',
            'HİERAPOLİS': '20',  # Denizli
            'LAODİKEİA': '20',
            'DİYARBAKIR': '21',
            'ZEUGMA': '27',  # Gaziantep
            'HATAY': '31',
            'İSTANBUL': '34',
            'GALATA': '34',
            'TOPKAPI': '34',
            'AGORA': '35',  # İzmir
            'BERGAMA': '35',
            'ÇEŞME': '35',
            'EFES': '35',
            'KARS': '36',
            'ANİ': '36',
            'BODRUM': '48',  # Muğla
            'MARMARİS': '48',
            'KNİDOS': '48',
            'DERİNKUYU': '50',  # Nevşehir
            'GÖREME': '50',
            'KARANLIK': '50',
            'KAYMAKLI': '50',
            'ÖZKONAK': '50',
            'ZELVE': '50',
            'GÖBEKLİTEPE': '63',  # Şanlıurfa
            'SÜMELA': '61',  # Trabzon
            'AKDAMAR': '65'  # Van
        }

        museum_name = museum_name.upper()
        for hint, code in city_hints.items():
            if hint in museum_name:
                try:
                    return City.objects.get(code=code)
                except:
                    pass
        return None

    def handle(self, *args, **options):
        # JSON dosyasının yolu
        json_file_path = os.path.join('data', 'museum.json')
        
        try:
            # JSON dosyasını oku
            with open(json_file_path, 'r', encoding='utf-8') as file:
                museums = json.load(file)
            
            # Mevcut müzeleri temizle
            self.stdout.write('Mevcut müzeler temizleniyor...')
            Museum.objects.all().delete()
            
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
            
            # Müzeleri ekle
            self.stdout.write('Müzeler ekleniyor...')
            added_count = 0
            skipped_count = 0
            
            for museum_data in museums:
                # Önce verilen şehri dene
                city = self.find_city(museum_data['new_city'])
                
                # Şehir bulunamadıysa, müze adından tahmin et
                if city is None:
                    city = self.guess_city_from_name(museum_data['name'])
                
                if city is None:
                    self.stdout.write(self.style.ERROR(f"Hata: {museum_data['name']} müzesi için şehir bulunamadı"))
                    skipped_count += 1
                    continue
                
                # Müzeyi oluştur
                museum = Museum.objects.create(
                    name=museum_data['name'],
                    city=city,
                    local_price=0,  # Varsayılan değerler
                    foreign_price=0,
                    currency=default_currency,
                    valid_until=default_valid_until
                )
                
                self.stdout.write(f"{museum_data['name']} ({city}) eklendi.")
                added_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Tüm müzeler işlendi! {added_count} müze eklendi, {skipped_count} müze atlandı.'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası bulunamadı!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası geçerli bir JSON formatında değil!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hata: {str(e)}')) 