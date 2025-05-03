import requests
from bs4 import BeautifulSoup
import os
import time
from colorama import init, Fore

# Colorama'yı başlat
init()

# Başlangıç ve bitiş sayfa numaralarını burada belirleyin
BASLANGIC_SAYFA = 501 # 1  # İndirmeye başlanacak sayfa numarası
BITIS_SAYFA = 605 # 605    # İndirmenin biteceği sayfa numarası
INDRIME_KLASORU = "E:\\oku"



def get_file_size_str(size_bytes):
    """Bayt cinsinden boyutu okunaklı formata çevirir"""
    for unit in ['B', 'KB', 'MB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} GB"

def download_mp3(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        print(f"{Fore.RED}Hata oluştu: {e}{Fore.RESET}")
        return False

def main():
    # İndirme başlangıç zamanını kaydet
    baslangic_zamani = time.time()
    
    # İndirme klasörünü oluştur
    download_dir = INDRIME_KLASORU
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Toplam başarılı ve başarısız indirmeleri takip et
    successful_downloads = 0
    failed_downloads = 0
    total_size = 0

    # Belirtilen sayfa aralığını tara
    for page_num in range(BASLANGIC_SAYFA, BITIS_SAYFA + 1):
        # Sayfa numarasını 3 haneli formata çevir (001, 002, ...)
        page_str = str(page_num).zfill(3)
        mp3_url = f"http://qrkodkuran.com/sesler/{page_str}_sau.mp3"
        save_path = os.path.join(download_dir, f"{page_str}_sau.mp3")

        print(f"\nİndiriliyor: {mp3_url}")
        
        if download_mp3(mp3_url, save_path):
            successful_downloads += 1
            file_size = os.path.getsize(save_path)
            total_size += file_size
            size_str = get_file_size_str(file_size)
            print(f"{Fore.GREEN}Başarıyla indirildi: {page_str}_sau.mp3 (Boyut: {size_str}){Fore.RESET}")
        else:
            failed_downloads += 1
            print(f"{Fore.RED}İndirilemedi: {page_str}_sau.mp3{Fore.RESET}")
        
        # Sunucuya aşırı yük bindirmemek için her indirmeden sonra kısa bir bekleme
        time.sleep(1)

    print(f"\n{Fore.CYAN}İndirme işlemi tamamlandı!{Fore.RESET}")
    print(f"{Fore.GREEN}Başarılı indirmeler: {successful_downloads}{Fore.RESET}")
    print(f"{Fore.RED}Başarısız indirmeler: {failed_downloads}{Fore.RESET}")
    print(f"{Fore.CYAN}Toplam indirilen boyut: {get_file_size_str(total_size)}{Fore.RESET}")
    
    # Geçen süreyi hesapla
    bitis_zamani = time.time()
    gecen_sure = bitis_zamani - baslangic_zamani
    dakika = int(gecen_sure // 60)
    saniye = int(gecen_sure % 60)
    print(f"{Fore.CYAN}Toplam geçen süre: {dakika} dakika {saniye} saniye{Fore.RESET}")
    
    print(f"{Fore.YELLOW}Dosyaların kaydedildiği klasör: {os.path.abspath(download_dir)}{Fore.RESET}")

if __name__ == "__main__":
    main()