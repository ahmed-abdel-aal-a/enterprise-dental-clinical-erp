import subprocess
import time
import re
import urllib.request
import urllib.parse
import json

CLOUDFLARED_EXE = r"D:\important projects\dentalpin-arabic\bin\cloudflared\cloudflared.exe"
LOCAL_URL = "http://127.0.0.1:7070"

print("=" * 70)
print("  DentApex - Live Mobile Cloudflare Tunnel Authentication Test")
print("=" * 70)

# 1. Start tunnel
proc = subprocess.Popen([CLOUDFLARED_EXE, "tunnel", "--url", LOCAL_URL, "--no-autoupdate"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

tunnel_url = None
start_time = time.time()
pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

print("[*] Starting Cloudflare Quick Tunnel...")
while time.time() - start_time < 30:
    line = proc.stdout.readline()
    if not line:
        time.sleep(0.5)
        continue
    match = pattern.search(line)
    if match:
        tunnel_url = match.group(0)
        break

if not tunnel_url:
    proc.terminate()
    raise RuntimeError("Failed to obtain trycloudflare.com URL.")

print(f"[SUCCESS] Tunnel URL: {tunnel_url}")

# 2. Wait 15s for edge DNS propagation
print("[*] Waiting 15s for global edge DNS propagation...")
time.sleep(15)

# 3. Test Health
print(f"[*] Testing {tunnel_url}/health ...")
res = subprocess.run(["curl.exe", "-k", "-s", "--max-time", "10", f"{tunnel_url}/health"], capture_output=True, text=True)
print("    Health Response:", res.stdout.strip())

# 4. Test Login
login_url = f"{tunnel_url}/api/v1/auth/login"
print(f"[*] Testing Live Mobile Login at {login_url} ...")
login_data = "username=admin@dental.com&password=DentApex2026!"
res_login = subprocess.run(
    ["curl.exe", "-k", "-s", "-X", "POST", login_url,
     "-H", "Content-Type: application/x-www-form-urlencoded",
     "-d", login_data],
    capture_output=True, text=True
)

print("    Login Response:", res_login.stdout.strip())
token_data = json.loads(res_login.stdout)

access_token = token_data.get("access_token")
if access_token:
    print(f"\n[SUCCESS] Access Token acquired: {access_token[:40]}...")
    print(f"[SUCCESS] Token Type: {token_data.get('token_type')}")
    
    # 5. Query /api/v1/auth/me
    me_url = f"{tunnel_url}/api/v1/auth/me"
    print(f"\n[*] Querying Authenticated Doctor Profile: {me_url} ...")
    res_me = subprocess.run(
        ["curl.exe", "-k", "-s", me_url, "-H", f"Authorization: Bearer {access_token}"],
        capture_output=True, text=True
    )
    print("    Profile Response:", res_me.stdout.strip())
else:
    print("[ERROR] Failed to obtain access token:", res_login.stdout)

# Cleanup
print("\n[*] Terminating tunnel...")
subprocess.run(["taskkill", "/IM", "cloudflared.exe", "/F", "/T"], capture_output=True)
print("[OK] Cloudflared process tree terminated.")
