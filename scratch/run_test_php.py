import subprocess
import json
import sys

payload = json.dumps({"prompt": "ما هي أهم نصيحة بعد خلع ضرس العقل؟"}, ensure_ascii=False).encode('utf-8')

php_code = """
$_SERVER['REQUEST_METHOD'] = 'POST';
require 'dentalpin-main/frontend/public/api/copilot/chat.php';
"""

proc = subprocess.Popen(
    ['php', '-r', php_code],
    cwd=r'D:\important projects\dentalpin-arabic',
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

stdout, stderr = proc.communicate(input=payload, timeout=30)
sys.stdout.buffer.write(b"--- PHP OUTPUT (SSE Stream) ---\n")
sys.stdout.buffer.write(stdout)
sys.stdout.buffer.write(b"\n--- PHP STDERR ---\n")
sys.stdout.buffer.write(stderr)
