import requests

# Telegram bot ayarları
TELEGRAM_API_KEY = '7372360015:AAE4WExfDnhnJ2JtCEkj7jLWQEN644NH1F0'

# Botunuzdan gelen güncellemeleri alın
def get_chat_id(api_key):
    url = f"https://api.telegram.org/bot{api_key}/getUpdates"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print("Gelen güncellemeler:")
        print(data)
        for result in data['result']:
            if 'message' in result:
                chat_id = result['message']['chat']['id']
                print(f"Chat ID: {chat_id}")
                return chat_id
    else:
        print(f"Telegram güncellemeleri alınamadı: {response.status_code} - {response.text}")

# Chat ID'yi al ve yazdır
chat_id = get_chat_id(TELEGRAM_API_KEY)
print(f"Chat ID: {chat_id}")
