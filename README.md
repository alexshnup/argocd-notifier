# ArgoCD Notifier

ArgoCD Notifier is a Kubernetes-based application that monitors ArgoCD applications for state changes and sends notifications to a specified Telegram chat. Notifications include details about new applications, updates to existing applications, and deletions.

## Features

- Monitors ArgoCD applications for:
  - Newly added applications.
  - State changes (e.g., `Sync` and `Health` statuses).
  - Deleted applications.
- Sends real-time notifications to a Telegram chat.
- Stores state information in a Custom Resource Definition (CRD).

## Prerequisites

1. Kubernetes cluster with ArgoCD installed.
2. Helm installed on your local machine.
3. Telegram bot token and chat ID for receiving notifications.
4. `kubectl` configured to interact with your Kubernetes cluster.

## Installation

### Step 1: Clone the repository
```bash
git clone <repository-url>
cd argocd-notifier
```

### Step 2: Deploy with Helm

#### Create a `values.yml` file
Customize the configuration:

```yaml
image:
  repository:  alexshnup/argocd-notifier
  tag: latest
  pullPolicy: IfNotPresent

env:
  ARGOCD_SERVER: "https://your-argocd-server"
  ARGOCD_TOKEN: "your-argocd-token"
  TELEGRAM_BOT_TOKEN: "your-telegram-bot-token"
  TELEGRAM_CHAT_ID: "your-telegram-chat-id"

resources: {}
```

#### Install the Helm chart
Run the following command:

```bash
helm upgrade --install argocd-notifier ./helm --namespace argocd -f values.yml
```

## How It Works

1. **Monitoring Applications:** The application continuously polls the ArgoCD API for the list of applications and their states (`Sync` and `Health`).
2. **State Comparison:** Current states are compared with the saved states stored in the CRD.
3. **Notification Trigger:** If a state change is detected (new application, update, or deletion), a Telegram message is sent.
4. **State Persistence:** The application saves the latest state in the Kubernetes CRD to ensure continuity after restarts.

## Custom Resource Definition (CRD)

The state is stored in a Kubernetes CRD. Below is the structure:

```yaml
apiVersion: argocd-notifier.example.com/v1
kind: Notifier
metadata:
  name: argocd-notifier-state
  namespace: argocd
spec:
  state: {}
```

## Troubleshooting

### Logs
Check logs for debugging:

```bash
kubectl logs -n argocd pod/argocd-notifier-<pod-id>
```

### Common Issues

1. **Forbidden Error for CRD:**
   Ensure the correct RBAC rules are applied:

   ```bash
   kubectl apply -f helm/templates/role.yaml
   kubectl apply -f helm/templates/rolebinding.yaml
   ```

2. **Telegram Notifications Not Working:**
   - Check the Telegram bot token and chat ID.
   - Ensure the Telegram API is accessible from the cluster.

3. **Missing Applications in Notifications:**
   - Verify the ArgoCD server and token configuration in `values-argocd-notifier.yml`.

## Contributing
Contributions are welcome! Feel free to submit issues or create pull requests.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
