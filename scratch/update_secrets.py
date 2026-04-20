import base64
import os

# This script automatically reads .env and updates k8s/secrets.yaml
env_path = ".env"
yaml_path = "k8s/secrets.yaml"

if not os.path.exists(env_path):
    print("Error: .env file not found!")
    exit()

# Read .env into a dictionary
env_vars = {}
with open(env_path, 'r') as f:
    for line in f:
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.strip().split("=", 1)
            env_vars[k.strip()] = v.strip()

# Mapping between .env and secrets.yaml
MAPPING = {
    "SECRET_KEY": "SECRET_KEY",
    "GROQ_API_KEY": "GROQ_API_KEY",
    "GROQ_API_KEYS": "GROQ_API_KEYS",
    "TAVILY_API_KEY": "TAVILY_API_KEY",
    "REDIS_URL": "REDIS_URL",
    "QDRANT_URL": "QDRANT_URL",
    "QDRANT_API_KEY": "QDRANT_API_KEY",
    "GOOGLE_CLIENT_ID": "VITE_GOOGLE_CLIENT_ID",
    "MAIL_USERNAME": "MAIL_USERNAME",
    "MAIL_PASSWORD": "MAIL_PASSWORD",
    "MAIL_FROM": "MAIL_FROM",
    "MAIL_FROM_NAME": "MAIL_FROM_NAME"
}

def encode(val):
    return base64.b64encode(val.strip().encode()).decode()

with open(yaml_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    updated = False
    for env_k, yaml_k in MAPPING.items():
        if f"  {yaml_k}:" in line:
            if env_k in env_vars:
                new_lines.append(f'  {yaml_k}: "{encode(env_vars[env_k])}"\n')
                updated = True
                print(f"[AUTO-SUCCESS] Migrated {env_k} -> {yaml_k}")
            break
    if not updated:
        new_lines.append(line)

with open(yaml_path, 'w') as f:
    f.writelines(new_lines)

print("\n--- MAGIC COMPLETE! ---")
print("Your k8s/secrets.yaml is now fully populated from your .env file.")
print("Now simply run: kubectl apply -f k8s/secrets.yaml")
