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
print("Environment variables loaded successfully.")

# Init Kubernetes client
try:
    config.load_incluster_config()  # For run inside the cluster
    api_instance = client.CustomObjectsApi()
    print("Kubernetes client initialized.")
except Exception as e:
    print(f"Error initializing Kubernetes client: {e}")
    raise

NAMESPACE = "argocd"
CRD_GROUP = "argocd-notifier.example.com"
CRD_VERSION = "v1"
CRD_PLURAL = "notifiers"
CRD_NAME = "argocd-notifier-state"

# Functions for CRD
def load_state_from_crd():
    print("Loading state from CRD...")
    try:
        obj = api_instance.get_namespaced_custom_object(
            group=CRD_GROUP,
            version=CRD_VERSION,
            namespace=NAMESPACE,
            plural=CRD_PLURAL,
            name=NOTIFIER_RESOURCE_NAME,
        )
        print("State loaded successfully.")
        return obj["spec"].get("state", {})
    except client.exceptions.ApiException as e:
        if e.status == 404:
            print("CRD state not found, returning empty state.")
            return {}
        else:
            print(f"Error loading state from CRD: {e}")
            raise

def save_state_to_crd(state):
    print("Saving state to CRD...")
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
        print("State saved successfully.")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            print("CRD not found, creating a new one.")
            api_instance.create_namespaced_custom_object(
                group=CRD_GROUP,
                version=CRD_VERSION,
                namespace=NAMESPACE,
                plural=CRD_PLURAL,
                body=body,
            )
        else:
            print(f"Error saving state to CRD: {e}")
            raise

# Functions for ArgoCD
def get_applications():
    print("Fetching applications from ArgoCD...")
    url = f"{ARGOCD_SERVER}/api/v1/applications"
    headers = {"Authorization": f"Bearer {ARGOCD_TOKEN}"}
    verify_ssl = False  # Assuming no SSL verification for simplicity

    response = requests.get(url, headers=headers, verify=verify_ssl)
    
    if response.status_code != 200:
        print(f"Error fetching applications: {response.status_code} - {response.text}")
        return []

    try:
        data = response.json()
        print(f"Applications fetched: {len(data.get('items', []))} found.")
    except ValueError:
        print(f"Invalid JSON response: {response.text}")
        return []

    return data.get("items", [])

# Telegram messaging
def send_telegram_message(message):
    print(f"Sending message to Telegram: {message}")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message: {response.text}")

# Monitoring loop
def monitor_applications():
    print("Starting monitoring ArgoCD applications...")
    saved_states = load_state_from_crd()
    print(f"Initial saved states: {saved_states}")

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
            print(f"Current states: {current_states}")

            # Check for changes
            for app_name, new_state in current_states.items():
                old_state = saved_states.get(app_name)
                if not old_state:
                    send_telegram_message(f"🔔 New application: {app_name}, state: {new_state}")
                elif old_state != new_state:
                    send_telegram_message(
                        f"✏️ Application {app_name} updated:\n"
                        f"Sync: {old_state['sync_status']} → {new_state['sync_status']}\n"
                        f"Health: {old_state['health_status']} → {new_state['health_status']}"
                    )

            # Check for deleted applications
            deleted_apps = set(saved_states.keys()) - set(current_states.keys())
            for app_name in deleted_apps:
                send_telegram_message(f"❌ Application deleted: {app_name}")

            # Save new state
            saved_states = current_states
            save_state_to_crd(saved_states)

            time.sleep(30)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    send_telegram_message("Start")
    print("Notifier started.")
    monitor_applications()