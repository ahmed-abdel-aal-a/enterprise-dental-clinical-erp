import subprocess
import time
import urllib.request
import json
import sys

# 1. Start PHP server on 127.0.0.1:8888
print("Starting PHP Built-in Server on 127.0.0.1:8888 ...")
php_server = subprocess.Popen(
    ['php', '-S', '127.0.0.1:8888', '-t', r'dentalpin-main\frontend\public'],
    cwd=r'D:\important projects\dentalpin-arabic',
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(2)

try:
    url = "http://127.0.0.1:8888/api/copilot/chat.php"
    payload = json.dumps({
        "prompt": "ما هي أهم 3 نصائح بعد خلع ضرس العقل؟"
    }, ensure_ascii=False).encode('utf-8')

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 DentApexTest"
        }
    )

    print("Sending POST request to:", url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        print("HTTP Status:", resp.status)
        print("Content-Type:", resp.headers.get("Content-Type"))
        
        full_text = ""
        while True:
            line = resp.readline()
            if not line:
                break
            line_str = line.decode('utf-8', errors='replace').strip()
            if line_str.startswith("data:"):
                data_content = line_str[5:].strip()
                if data_content == "[DONE]":
                    print("\n[STREAM COMPLETE: [DONE]]")
                    break
                try:
                    obj = json.loads(data_content)
                    if "error" in obj:
                        print("\n[ERROR EVENT]:", obj["error"]["message"])
                    delta = obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if delta:
                        sys.stdout.buffer.write(delta.encode('utf-8'))
                        sys.stdout.buffer.flush()
                        full_text += delta
                except Exception as ex:
                    pass

    print("\n\n--- VERIFICATION RESULT ---")
    if len(full_text) > 10:
        print("SUCCESS! allam-2-7b responded with full Arabic clinical stream.")
        print(f"Total characters received: {len(full_text)}")
    else:
        print("FAILED: Output was too short or empty.")

finally:
    php_server.terminate()
    php_server.wait()
    print("PHP server stopped.")
