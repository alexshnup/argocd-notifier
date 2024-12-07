import os
import requests
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from kubernetes import client, config


# Reading environment variables
ARGOCD_SERVER = os.getenv("ARGOCD_SERVER")
ARGOCD_TOKEN = os.getenv("ARGOCD_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
NOTIFIER_RESOURCE_NAME = os.getenv("NOTIFIER_RESOURCE_NAME")


# Check vars
if not all([ARGOCD_SERVER, ARGOCD_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise EnvironmentError("Not all required environment variables are set!")

# Init Kubernetes client
config.load_incluster_config()  # For run inside the cluster
api_instance = client.CustomObjectsApi()

NAMESPACE = "argocd"
CRD_GROUP = "argocd-notifier.example.com"
CRD_VERSION = "v1"
CRD_PLURAL = "notifiers"
CRD_NAME = "argocd-notifier-state"


def load_state_from_crd():
    try:
        obj = api_instance.get_namespaced_custom_object(
            group=CRD_GROUP,
            version=CRD_VERSION,
            namespace=NAMESPACE,
            plural=CRD_PLURAL,
            name=NOTIFIER_RESOURCE_NAME,
        )
        return obj["spec"].get("state", {})
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return {}
        else:
            raise

def save_state_to_crd(state):
    body = {
        "apiVersion": "argocd-notifier.example.com/v1",
        "kind": "Notifier",
        "metadata": {"name": NOTIFIER_RESOURCE_NAME},
        "spec": {"state": state},
    }
    try:
        api_instance.replace_namespaced_custom_object(
            group=CRD_GROUP,
            version=CRD_VERSION,
            namespace=NAMESPACE,
            plural=CRD_PLURAL,
            name=NOTIFIER_RESOURCE_NAME,
            body=body,
        )
    except client.exceptions.ApiException as e:
        if e.status == 404:
            api_instance.create_namespaced_custom_object(
                group=CRD_GROUP,
                version=CRD_VERSION,
                namespace=NAMESPACE,
                plural=CRD_PLURAL,
                name=NOTIFIER_RESOURCE_NAME,
                body=body,
            )
        else:
            raise



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
        data = response.json()  # try to parse JSON
    except ValueError:
        print(f"Invalid JSON response: {response.text}")
        return []

    if "items" not in data:
        print(f"Unexpected response format: {data}")
        return []

    return data["items"]  # return list apps


# send message to telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print(f"Message sent: {message}")
    else:
        print(f"Failed to send message: {response.text}")

def monitor_applications():
        saved_states = load_state_from_crd()  # Загружаем состояние из CRD
        print("Starting monitoring ArgoCD applications...")

        while True:
            try:
                current_apps = get_applications()
                current_states = {
                    app["metadata"]["name"]: {
                        "sync_status": app["status"]["sync"]["status"],
                        "health_status": app["status"]["health"]["status"]
                    }
                    for app in current_apps
                }

                # Проверяем изменения
                for app_name, new_state in current_states.items():
                    old_state = saved_states.get(app_name)
                    if not old_state:
                        send_telegram_message(f"🔔 Новое приложение: {app_name}, состояние: {new_state}")
                    elif old_state != new_state:
                        send_telegram_message(
                            f"✏️ Изменение в приложении {app_name}:\n"
                            f"Синхронизация: {old_state['sync_status']} → {new_state['sync_status']}\n"
                            f"Здоровье: {old_state['health_status']} → {new_state['health_status']}"
                        )

                # Удаление
                deleted_apps = set(saved_states.keys()) - set(current_states.keys())
                for app_name in deleted_apps:
                    send_telegram_message(f"❌ Приложение удалено из ArgoCD: {app_name}")

                # Обновляем состояние в CRD
                saved_states = current_states
                save_state_to_crd(saved_states)

                time.sleep(30)
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)


# # main monitoring
# def monitor_applications():
#     saved_states = {}  # save state of apps
#     print("Starting monitoring ArgoCD applications...")

#     while True:
#         try:
#             current_apps = get_applications()  # list apps
#             current_states = {
#                 app["metadata"]["name"]: {
#                     "sync_status": app["status"]["sync"]["status"],
#                     "health_status": app["status"]["health"]["status"]
#                 }
#                 for app in current_apps
#             }

#             # check for any apps changes
#             for app_name, new_state in current_states.items():
#                 old_state = saved_states.get(app_name)

#                 # Notify about new states or changes
#                 if not old_state:
#                     send_telegram_message(f"🔔 New app: {app_name}, status: {new_state}")
#                 elif old_state != new_state:
#                     send_telegram_message(
#                         f"✏️ App changes {app_name}:\n"
#                         f"Sync: {old_state['sync_status']} → {new_state['sync_status']}\n"
#                         f"Health: {old_state['health_status']} → {new_state['health_status']}"
#                     )

#             # Check for delete apps
#             deleted_apps = set(saved_states.keys()) - set(current_states.keys())
#             for app_name in deleted_apps:
#                 send_telegram_message(f"❌ Apps deleted from ArgoCD: {app_name}")

#             saved_states = current_states  # refresh saved states
#             time.sleep(30)
#         except Exception as e:
#             print(f"Error: {e}")
#             time.sleep(60)


if __name__ == "__main__":
    monitor_applications()
