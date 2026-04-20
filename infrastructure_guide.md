# 🌍 Infrastructure & Deployment Guide

This guide provides the mandatory steps to set up your AWS environment and GitHub Secrets for the Apex Energy AI platform.

## 1. AWS EC2 Instance Setup

### Step A: Create Instance
- **OS**: Ubuntu 22.04 LTS (Recommended)
- **Instance Type**: t3.medium or larger (Kubernetes requires at least 4GB RAM).
- **Storage**: Minimum 20GB.

### Step B: Security Group (Firewall)
Add these **Inbound Rules** to your instance's Security Group:

| Type | Port Range | Protocol | Source | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| SSH | 22 | TCP | 0.0.0.0/0 | GitHub Actions & CLI access |
| HTTP | 80 | TCP | 0.0.0.0/0 | Frontend Access |
| HTTPS | 443 | TCP | 0.0.0.0/0 | Secure Access |
| API | 8000 | TCP | 0.0.0.0/0 | Backend API (Direct Access) |

---

## 2. Server Installation Commands
Run these commands on your AWS instance after logging in:

### Install Docker
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

### Install Kubectl (Control Plane)
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

---

## 3. GitHub Secrets Configuration
Go to your **GitHub Repo > Settings > Secrets and variables > Actions** and add these:

| Secret Name | Value Description |
| :--- | :--- |
| `DOCKERHUB_USERNAME` | Your DockerHub ID |
| `DOCKERHUB_TOKEN` | Your DockerHub Access Token (not password) |
| `VITE_GOOGLE_CLIENT_ID` | Your Google OAuth Client ID |
| `EC2_HOST` | The Public IP of your AWS Instance |
| `EC2_SSH_KEY` | The entire content of your `.pem` private key |
| `KUBECONFIG` | The content of the file at `~/.kube/config` on your server |

---

## 4. Kubernetes Secrets (Final Step)

> [!IMPORTANT]
> Because you are using **7 GROQ API Keys**, you must encode the entire comma-separated string exactly as it appears in your `.env`.

### Step A: Encode all variables
Use these commands on your local terminal or AWS server to get the Base64 values:

```bash
# Groq Keys (Pool 1)
echo -n "key1,key2,key3" | base64

# Groq Keys (Pool 2)
echo -n "key4,key5,key6,key7" | base64

# Tavily (Project 2 Search)
echo -n "tvly-your-key" | base64

# Qdrant & Redis
echo -n "https://your-qdrant-url" | base64
echo -n "your-qdrant-api-key" | base64
echo -n "redis://your-redis-url" | base64

# Mail (SMTP)
echo -n "your-email@gmail.com" | base64
echo -n "your-google-app-password" | base64
```

### Step B: Update `k8s/secrets.yaml`
1. Open `k8s/secrets.yaml`.
2. Paste the long Base64 strings into the corresponding fields.
3. Save the file.

### Step C: Apply to Cluster
Run this command manually on your server:
```bash
kubectl apply -f k8s/secrets.yaml
```

---

**Apex Energy AI is now ready for Global Scalability!** ☸️🛡️🚀
