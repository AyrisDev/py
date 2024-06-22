import requests
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Notion ve Telegram bot ayarları
NOTION_API_KEY = 'secret_nxUCMm3ffc3H6Q6m442F5ciZyNybgveCP0rI3VkjVJc'
MAIN_DATABASE_ID = '50fac6c509ba4ab7a4c5cebd56d7cd3e'
ROOMS_DATABASE_ID = '6eaff8d3ddb34bafb89f33bdbfb46976'
TELEGRAM_API_KEY = '7372360015:AAE4WExfDnhnJ2JtCEkj7jLWQEN644NH1F0'

# Notion API'den veritabanı bilgilerini alın
def fetch_notion_database(api_key, database_id):
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(url, headers=headers)
    response.raise_for_status()  # Hata varsa burada durdurur
    return response.json()

# Veritabanından tarih bilgilerini ve oda ID'lerini çekin
def parse_dates_and_rooms_from_notion(data):
    entries = []
    for result in data['results']:
        try:
            # Listings alanı "relation" mi kontrol edelim
            if 'relation' in result['properties']['Listings']:
                room_id = result['properties']['Listings']['relation'][0]['id']
            else:
                print("Listings alanı beklenen formatta değil:", result['properties']['Listings'])
                continue
            
            # Check Date alanı "date" mi kontrol edelim
            if 'date' in result['properties']['Check Date']:
                start_date = result['properties']['Check Date']['date']['start']
                end_date = result['properties']['Check Date']['date']['end']
            else:
                print("Check Date alanı beklenen formatta değil:", result['properties']['Check Date'])
                continue

            entries.append((room_id, start_date, end_date))
        except IndexError as e:
            print("IndexError:", e, result)
        except KeyError as e:
            print("KeyError:", e, result)
    return entries

# Oda ID'lerinden oda isimlerini çekin
def get_room_names(api_key, rooms_database_id):
    data = fetch_notion_database(api_key, rooms_database_id)
    room_names = {}
    for result in data['results']:
        room_id = result['id']
        room_name = result['properties']['Name']['title'][0]['text']['content']
        room_names[room_id] = room_name
    return room_names

# Boş tarihleri bulun ve bloklar halinde gruplayın
def find_empty_dates_by_room(date_ranges_by_room):
    empty_dates_by_room = {}
    for room, date_ranges in date_ranges_by_room.items():
        all_dates = set()
        for start, end in date_ranges:
            current_date = datetime.strptime(start, '%Y-%m-%d')
            end_date = datetime.strptime(end, '%Y-%m-%d')
            while current_date <= end_date:
                all_dates.add(current_date)
                current_date += timedelta(days=1)

        # En erken ve en geç tarihleri belirleyin
        min_date = min(all_dates)
        max_date = max(all_dates)

        # Boş tarihleri bloklar halinde bulun
        empty_blocks = []
        current_date = min_date
        block_start = None
        while current_date <= max_date:
            if current_date not in all_dates:
                if block_start is None:
                    block_start = current_date
            else:
                if block_start is not None:
                    empty_blocks.append((block_start, current_date - timedelta(days=1)))
                    block_start = None
            current_date += timedelta(days=1)
        
        # Eğer blok sonlanmadıysa, son bloğu ekleyin
        if block_start is not None:
            empty_blocks.append((block_start, max_date))

        empty_dates_by_room[room] = empty_blocks
    return empty_dates_by_room

# Telegram /checkdate komutu işlevi
def check_date(update: Update, context: CallbackContext) -> None:
    try:
        main_data = fetch_notion_database(NOTION_API_KEY, MAIN_DATABASE_ID)
        date_entries = parse_dates_and_rooms_from_notion(main_data)
        
        # Oda ID'lerinden oda isimlerini çekin
        room_names = get_room_names(NOTION_API_KEY, ROOMS_DATABASE_ID)
        
        # Odalara göre tarih aralıklarını gruplayın
        date_ranges_by_room = {}
        for room_id, start_date, end_date in date_entries:
            room_name = room_names.get(room_id, "Unknown Room")
            if room_name not in date_ranges_by_room:
                date_ranges_by_room[room_name] = []
            date_ranges_by_room[room_name].append((start_date, end_date))
        
        # Her oda için boş tarihleri bulun ve bloklar halinde gruplayın
        empty_dates_by_room = find_empty_dates_by_room(date_ranges_by_room)

        # Sonuçları oda isimlerine göre sıralayarak Telegram mesajı hazırlayın
        message = "*Boş Tarihler:*\n"
        for room in sorted(empty_dates_by_room.keys()):
            message += f"*{room} için boş tarihler:*\n"
            for block in empty_dates_by_room[room]:
                message += f"{block[0].strftime('%d/%m/%Y')} → {block[1].strftime('%d/%m/%Y')}\n"
            message += "\n"
        
        # Mesajı kullanıcıya gönderin
        update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        update.message.reply_text(f"Hata: {e}")

def main() -> None:
    # Updater oluşturun ve dispatcher'ı alın
    updater = Updater(TELEGRAM_API_KEY, use_context=True)
    dispatcher = updater.dispatcher

    # Komutları ekleyin
    dispatcher.add_handler(CommandHandler("checkdate", check_date))

    # Botu başlatın
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
