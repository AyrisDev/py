import requests
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Notion ve Telegram bot ayarları
NOTION_API_KEY = 'secret_nxUCMm3ffc3H6Q6m442F5ciZyNybgveCP0rI3VkjVJc'
DATABASE_ID = '50fac6c509ba4ab7a4c5cebd56d7cd3e'
PERSON_DATABASE_ID = '5c8f6ca5d342426b961b40b50abcb5de'
LISTINGS_DATABASE_ID = '6eaff8d3ddb34bafb89f33bdbfb46976'
TELEGRAM_API_KEY = '7372360015:AAE4WExfDnhnJ2JtCEkj7jLWQEN644NH1F0'

# State definitions for conversation
NAME, PERSON_NAME, PERSON_PHONE, LISTING, TOTAL_PRICE, KAPORA, CHECK_DATE, START_DATE, END_DATE = range(9)

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Merhaba! "/addReservation" komutunu kullanarak yeni bir rezervasyon ekleyebilirsiniz.')

# Add reservation command handler
def add_reservation(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Rezervasyon eklemeye başlayalım. Lütfen isim girin:')
    return NAME

# Name input handler
def name_input(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text('Lütfen kişinin adını girin:')
    return PERSON_NAME

# Person name input handler
def person_name_input(update: Update, context: CallbackContext) -> int:
    context.user_data['person_name'] = update.message.text
    update.message.reply_text('Lütfen kişinin telefon numarasını girin:')
    return PERSON_PHONE

# Person phone input handler
def person_phone_input(update: Update, context: CallbackContext) -> int:
    context.user_data['person_phone'] = update.message.text
    update.message.reply_text('Lütfen oda numarasını seçin:')
    # Fetch listings from Notion and show them as options
    listings = fetch_listings_from_notion()
    listings_text = "\n".join([f"{i + 1}. {listing['name']}" for i, listing in enumerate(listings)])
    context.user_data['listings'] = listings
    update.message.reply_text(f"Mevcut odalar:\n{listings_text}\n\nOda numarasını girin:")
    return LISTING

# Listing input handler
def listing_input(update: Update, context: CallbackContext) -> int:
    listing_choice = int(update.message.text) - 1
    listings = context.user_data['listings']
    if 0 <= listing_choice < len(listings):
        context.user_data['listing'] = listings[listing_choice]['id']
        update.message.reply_text('Lütfen toplam fiyatı girin:')
        return TOTAL_PRICE
    else:
        update.message.reply_text('Geçersiz seçim. Lütfen tekrar deneyin:')
        return LISTING

# Total price input handler
def total_price_input(update: Update, context: CallbackContext) -> int:
    context.user_data['total_price'] = update.message.text
    update.message.reply_text('Lütfen kapora miktarını girin:')
    return KAPORA

# Kapora input handler
def kapora_input(update: Update, context: CallbackContext) -> int:
    kapora_text = update.message.text.strip()
    if not kapora_text.isdigit():
        update.message.reply_text('Geçersiz kapora miktarı. Lütfen sadece rakam girin.')
        return KAPORA
    
    context.user_data['kapora'] = int(kapora_text)
    update.message.reply_text('Lütfen rezervasyon tarih aralığını girin.\nBaşlangıç tarihi (yyyy-mm-dd):')
    return CHECK_DATE

# Check date input handler
def check_date_input(update: Update, context: CallbackContext) -> int:
    context.user_data['start_date'] = update.message.text
    update.message.reply_text('Bitiş tarihi (yyyy-mm-dd):')
    return END_DATE

# Start date input handler
def start_date_input(update: Update, context: CallbackContext) -> int:
    context.user_data['end_date'] = update.message.text

    try:
        person_id = add_person_to_notion(context.user_data['person_name'], context.user_data['person_phone'])
        context.user_data['person'] = person_id
        add_reservation_to_notion(context.user_data)
        update.message.reply_text('Rezervasyon başarıyla eklendi!')
    except Exception as e:
        update.message.reply_text(f"Bir hata oluştu: {str(e)}")
        logging.error(f"Hata oluştu: {e}")

    return ConversationHandler.END

# End date input handler
def end_date_input(update: Update, context: CallbackContext) -> int:
    context.user_data['end_date'] = update.message.text

    try:
        person_id = add_person_to_notion(context.user_data['person_name'], context.user_data['person_phone'])
        context.user_data['person'] = person_id
        add_reservation_to_notion(context.user_data)
        update.message.reply_text('Rezervasyon başarıyla eklendi!')
    except Exception as e:
        update.message.reply_text(f"Bir hata oluştu: {str(e)}")
        logging.error(f"Hata oluştu: {e}")

    return ConversationHandler.END

# Add person to Notion
def add_person_to_notion(name, phone):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {
        "parent": {"database_id": PERSON_DATABASE_ID},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": name
                        }
                    }
                ]
            },
            "Phone": {
                "rich_text": [
                    {
                        "text": {
                            "content": phone
                        }
                    }
                ]
            }
        }
    }
    logging.info(f"add_person_to_notion Payload: {payload}")
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"add_person_to_notion Response: {response.text}")
    response.raise_for_status()
    return response.json()['id']

# Fetch listings from Notion
def fetch_listings_from_notion():
    url = f"https://api.notion.com/v1/databases/{LISTINGS_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    response = requests.post(url, headers=headers)
    logging.info(f"fetch_listings_from_notion Response: {response.text}")
    response.raise_for_status()
    listings = response.json()['results']
    return [{'id': listing['id'], 'name': listing['properties']['Name']['title'][0]['text']['content']} for listing in listings]

# Add reservation to Notion
def add_reservation_to_notion(data):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {
                "title": [
                    {
                        "text": {
                            "content": data['name']
                        }
                    }
                ]
            },
            "Person": {
                "relation": [
                    {
                        "id": data['person']
                    }
                ]
            },
            "Listings": {
                "relation": [
                    {
                        "id": data['listing']
                    }
                ]
            },
            "Total Price": {
                "number": float(data['total_price'])  # Ensure it's converted to a float if necessary
            },
            "Kapora": {
                "number": float(data['kapora']) 
            },
            "Check Date": {
                "date": {
                    "start": convert_to_iso_date(data['start_date']),
                    "end": convert_to_iso_date(data['end_date'])
                }
            }
        }
    }
    logging.info(f"add_reservation_to_notion Payload: {payload}")
    response = requests.post(url, headers=headers, json=payload)
    logging.info(f"add_reservation_to_notion Response: {response.text}")
    response.raise_for_status()

def convert_to_iso_date(date_str):
    day, month, year = map(int, date_str.split('-'))
    return f"{year:04d}-{month:02d}-{day:02d}"

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Rezervasyon ekleme işlemi iptal edildi.')
    return ConversationHandler.END

def main() -> None:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    # Updater oluşturun ve dispatcher'ı alın
    updater = Updater(TELEGRAM_API_KEY, use_context=True)
    dispatcher = updater.dispatcher

    # Conversation handler for reservation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('addReservation', add_reservation)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, name_input)],
            PERSON_NAME: [MessageHandler(Filters.text & ~Filters.command, person_name_input)],
            PERSON_PHONE: [MessageHandler(Filters.text & ~Filters.command, person_phone_input)],
            LISTING: [MessageHandler(Filters.text & ~Filters.command, listing_input)],
            TOTAL_PRICE: [MessageHandler(Filters.text & ~Filters.command, total_price_input)],
            KAPORA: [MessageHandler(Filters.text & ~Filters.command, kapora_input)],
            CHECK_DATE: [MessageHandler(Filters.text & ~Filters.command, check_date_input)],
            START_DATE: [MessageHandler(Filters.text & ~Filters.command, start_date_input)],
            END_DATE: [MessageHandler(Filters.text & ~Filters.command, end_date_input)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("start", start))

    # Botu başlatın
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
