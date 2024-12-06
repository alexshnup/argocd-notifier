import requests
import yaml
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load config
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

ARGOCD_SERVER = config["argocd"]["server"]
ARGOCD_TOKEN = config["argocd"]["token"]
TELEGRAM_TOKEN = config["telegram"]["bot_token"]
CHAT_ID = config["telegram"]["chat_id"]

# get apps list
def get_applications():
    url = f"{ARGOCD_SERVER}/api/v1/applications"
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    verify_ssl = config["argocd"].get("verify_ssl", True)

    response = requests.get(url, headers=headers, verify=verify_ssl)
    
    if response.status_code != 200:
        print(f"Error fetching applications: {response.status_code} - {response.text}")
        return []

    try:
<<<<<<< HEAD
        data = response.json()  # Попробуем разобрать JSON
=======
        data = response.json()  # try to parse JSON
>>>>>>> aac2e63cf042b18fcc04a04c6bbe85c5a37e8e86
    except ValueError:
        print(f"Invalid JSON response: {response.text}")
        return []

    if "items" not in data:
        print(f"Unexpected response format: {data}")
        return []

<<<<<<< HEAD
    return data["items"]  # Возвращаем список приложений
=======
    return data["items"]  # return list apps
>>>>>>> aac2e63cf042b18fcc04a04c6bbe85c5a37e8e86


# send message to telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"Message sent: {message}")
    else:
        print(f"Failed to send message: {response.text}")

# main monitoring
def monitor_applications():
<<<<<<< HEAD
    saved_states = {}  # Сохраняем состояния приложений (имя -> состояние)
=======
    saved_states = {}  # save state of apps
>>>>>>> aac2e63cf042b18fcc04a04c6bbe85c5a37e8e86
    print("Starting monitoring ArgoCD applications...")

    while True:
        try:
<<<<<<< HEAD
            current_apps = get_applications()  # Список приложений
=======
            current_apps = get_applications()  # list apps
>>>>>>> aac2e63cf042b18fcc04a04c6bbe85c5a37e8e86
            current_states = {
                app["metadata"]["name"]: {
                    "sync_status": app["status"]["sync"]["status"],
                    "health_status": app["status"]["health"]["status"]
                }
                for app in current_apps
            }

<<<<<<< HEAD
            # Проверяем изменения в состояниях
            for app_name, new_state in current_states.items():
                old_state = saved_states.get(app_name)

                # Уведомляем о новых состояниях или изменениях
                if not old_state:
                    send_telegram_message(f"🔔 Новое приложение: {app_name}, состояние: {new_state}")
=======
            # check for any apps changes
            for app_name, new_state in current_states.items():
                old_state = saved_states.get(app_name)

                # Notify about new states or changes
                if not old_state:
                    send_telegram_message(f"🔔 New app: {app_name}, status: {new_state}")
>>>>>>> aac2e63cf042b18fcc04a04c6bbe85c5a37e8e86
                elif old_state != new_state:
                    send_telegram_message(
                        f"✏️ Изменение в приложении {app_name}:\n"
                        f"Синхронизация: {old_state['sync_status']} → {new_state['sync_status']}\n"
                        f"Здоровье: {old_state['health_status']} → {new_state['health_status']}"
                    )

<<<<<<< HEAD
            # Проверяем удаление приложений
            deleted_apps = set(saved_states.keys()) - set(current_states.keys())
            for app_name in deleted_apps:
                send_telegram_message(f"❌ Приложение удалено из ArgoCD: {app_name}")

            saved_states = current_states  # Обновляем сохранённые состояния
=======
            # Check for delete apps
            deleted_apps = set(saved_states.keys()) - set(current_states.keys())
            for app_name in deleted_apps:
                send_telegram_message(f"❌ Apps deleted from ArgoCD: {app_name}")

            saved_states = current_states  # refresh saved states
>>>>>>> aac2e63cf042b18fcc04a04c6bbe85c5a37e8e86
            time.sleep(30)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)


if __name__ == "__main__":
    monitor_applications()
