import json
import os
from django.core.management.base import BaseCommand
from tour.models import BuyerCompany

class Command(BaseCommand):
    help = 'buyer_company.json dosyasındaki alıcı şirketleri veritabanına kaydeder'

    def handle(self, *args, **options):
        # JSON dosyasının yolu
        json_file_path = os.path.join('data', 'buyer_company.json')
        
        try:
            # JSON dosyasını oku
            with open(json_file_path, 'r', encoding='utf-8') as file:
                companies = json.load(file)
            
            # Mevcut şirketleri temizle
            self.stdout.write('Mevcut alıcı şirketler temizleniyor...')
            BuyerCompany.objects.all().delete()
            
            # Şirketleri ekle
            self.stdout.write('Alıcı şirketler ekleniyor...')
            for company_data in companies:
                # contact alanı None ise boş string olarak ayarla
                if company_data['contact'] is None:
                    company_data['contact'] = ''
                
                BuyerCompany.objects.create(**company_data)
                self.stdout.write(f"{company_data['name']} ({company_data['short_name']}) eklendi.")
            
            self.stdout.write(self.style.SUCCESS('Tüm alıcı şirketler başarıyla eklendi!'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası bulunamadı!'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Hata: {json_file_path} dosyası geçerli bir JSON formatında değil!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Hata: {str(e)}'))
