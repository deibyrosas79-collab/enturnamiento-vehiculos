import base64, json, sys, urllib.request, urllib.error
from nacl.public import PublicKey, SealedBox

REPO = "deibyrosas79-collab/enturnamiento-vehiculos"
TOKEN = sys.argv[1]
DB_URL = sys.argv[2]
ACR_PASS = sys.argv[3]
AZ_CREDS = sys.argv[4]

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def encrypt(pub_key_b64, value):
    pk = PublicKey(base64.b64decode(pub_key_b64))
    return base64.b64encode(SealedBox(pk).encrypt(value.encode())).decode()

def api(method, path, data=None):
    url = f"https://api.github.com{path}"
    h = {**HEADERS}
    if data:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None, headers=h, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# Obtener clave publica del repo
_, body = api("GET", f"/repos/{REPO}/actions/secrets/public-key")
key_data = json.loads(body)
key_id = key_data["key_id"]
pub_key = key_data["key"]
print(f"Repo key_id: {key_id}")

secrets = {
    "AZURE_CREDENTIALS": AZ_CREDS,
    "ACR_USERNAME": "acrentd79prod",
    "ACR_PASSWORD": ACR_PASS,
    "AZURE_DATABASE_URL": DB_URL,
    "AZURE_WEBAPP_NAME": "enturnamiento-diana-d79-prod",
}

for name, value in secrets.items():
    enc = encrypt(pub_key, value)
    status, resp = api("PUT", f"/repos/{REPO}/actions/secrets/{name}", {"encrypted_value": enc, "key_id": key_id})
    icon = "OK" if status in (201, 204) else f"ERROR {status}"
    print(f"  {name}: {icon}")

# Variable AZURE_ACI_ENABLED
status, resp = api("POST", f"/repos/{REPO}/actions/variables", {"name": "AZURE_ACI_ENABLED", "value": "true"})
if status == 409 or "already exists" in resp:
    status, _ = api("PATCH", f"/repos/{REPO}/actions/variables/AZURE_ACI_ENABLED", {"name": "AZURE_ACI_ENABLED", "value": "true"})
print(f"  AZURE_ACI_ENABLED=true: {'OK' if status in (201, 204) else f'ERROR {status}'}")

print("\nTodos los secrets configurados en GitHub.")
