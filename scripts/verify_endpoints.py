import urllib.request
import json

def test(name, url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'DentalPin-Test'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = resp.read()
            status = resp.status
            content_type = resp.headers.get('Content-Type', '')
            sample = data[:150].decode('utf-8', errors='replace').replace('\n', ' ')
            print(f"[PASS] {name}: HTTP {status} | Type: {content_type} | Snippet: {sample}")
            return True
    except Exception as e:
        print(f"[FAIL] {name} ({url}): {e}")
        return False

print("="*60)
print("  DentalPin Arabic Edition - Endpoint Verification Suite")
print("="*60)

test("1. Backend Liveness (/health)", "http://127.0.0.1:7071/health")
test("2. Backend Readiness (/health/ready)", "http://127.0.0.1:7071/health/ready")
test("3. Backend API Root (/api/v1)", "http://127.0.0.1:7071/api/v1")
test("4. Caddy Static SPA Root (/)", "http://127.0.0.1:7070/")
test("5. Caddy Reverse Proxy (/api/v1)", "http://127.0.0.1:7070/api/v1")
test("6. Caddy SPA HTML Fallback (/login)", "http://127.0.0.1:7070/login")
test("7. Caddy Port 8000 Proxy (/api/v1)", "http://127.0.0.1:8000/api/v1")
test("8. Caddy Port 8000 Setup Status (/api/v1/auth/setup/status)", "http://127.0.0.1:8000/api/v1/auth/setup/status")
print("="*60)
