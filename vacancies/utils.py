from .models import Vacancy
import csv
import requests

BASE_URL = "https://gpt.orionsoft.ru/api/External" 
API_KEY = "OrVrQoQ6T43vk0McGmHOsdvvTiX446RJ"
OPERATING_SYSTEM_CODE = 12
USER_DOMAIN_NAME = "TeamO1nFLdmQe9tm"

def get_region_id(region_name):
    url = "https://api.hh.ru/areas" 
    response = requests.get(url)
    if response.status_code == 200:
        areas = response.json()
        for country in areas:
            for area in country['areas']:
                if area['name'].lower() == region_name.lower():
                    return area['id']
    return None

def export_to_csv():
    with open('data.csv', mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        headers = [field.name for field in Vacancy._meta.fields]
        writer.writerow(headers)
        for obj in Vacancy.objects.all():
            row = [getattr(obj, field.name) for field in Vacancy._meta.fields]
            writer.writerow(row)
    
def send_request(message, dialog_identifier=' TeamO1nFLdmQe9tm_4'):
    url = f"{BASE_URL}/PostNewRequest"
    payload = {
        "operatingSystemCode": OPERATING_SYSTEM_CODE,
        "apiKey": API_KEY,
        "userDomainName": USER_DOMAIN_NAME,
        "dialogIdentifier": dialog_identifier,
        "aiModelCode": 1,
        "Message": message
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Запрос успешно отправлен.")
    else:
        print(f"Ошибка при отправке запроса: {response.status_code}, {response.text}")

def get_response(dialog_identifier=' TeamO1nFLdmQe9tm_4'):
    url = f"{BASE_URL}/GetNewResponse"
    payload = {
        "operatingSystemCode": OPERATING_SYSTEM_CODE,
        "apiKey": API_KEY,
        "dialogIdentifier": dialog_identifier
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Ответ получен:", response.json())
        return response.json()
    else:
        print(f"Ошибка при получении ответа: {response.status_code}, {response.text}")
        return None

def reset_context(dialog_identifier=' TeamO1nFLdmQe9tm_4'):
    """
    Сброс контекста диалога.
    """
    url = f"{BASE_URL}/CompleteSession"
    payload = {
        "operatingSystemCode": OPERATING_SYSTEM_CODE,
        "apiKey": API_KEY,
        "dialogIdentifier": dialog_identifier
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Контекст успешно сброшен.")
    else:
        print(f"Ошибка при сбросе контекста: {response.status_code}, {response.text}")