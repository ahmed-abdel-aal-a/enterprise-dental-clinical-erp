import psutil

def measure():
    pg_rss = 0.0
    pg_private = 0.0
    pg_count = 0

    py_rss = 0.0
    py_private = 0.0
    py_count = 0

    caddy_rss = 0.0
    caddy_private = 0.0
    caddy_count = 0

    print("=" * 70)
    print("   DentalPin Arabic Edition - Detailed Memory Audit (RSS vs Private)")
    print("=" * 70)

    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            name = (proc.info['name'] or '').lower()
            cmd = ' '.join(proc.info['cmdline'] or []).lower()
            mem = proc.info['memory_info']
            rss_mb = mem.rss / (1024 * 1024)
            # Private bytes (commit charge on Windows)
            priv_mb = getattr(mem, 'private', getattr(mem, 'pagefile', 0)) / (1024 * 1024)

            if 'postgres' in name and 'dentalpin-arabic' in cmd:
                pg_rss += rss_mb
                pg_private += priv_mb
                pg_count += 1
                print(f"  [PG]    PID {proc.info['pid']:5d} | RSS: {rss_mb:6.2f} MB | Private: {priv_mb:6.2f} MB")
            elif 'python' in name and ('uvicorn' in cmd or 'app.main' in cmd) and 'scripts' not in cmd:
                py_rss += rss_mb
                py_private += priv_mb
                py_count += 1
                print(f"  [Py]    PID {proc.info['pid']:5d} | RSS: {rss_mb:6.2f} MB | Private: {priv_mb:6.2f} MB")
            elif 'caddy' in name:
                caddy_rss += rss_mb
                caddy_private += priv_mb
                caddy_count += 1
                print(f"  [Caddy] PID {proc.info['pid']:5d} | RSS: {rss_mb:6.2f} MB | Private: {priv_mb:6.2f} MB")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    print("-" * 70)
    print(f"PostgreSQL 16 Portable ({pg_count} procs): RSS = {pg_rss:6.2f} MB | Private Commit = {pg_private:6.2f} MB")
    print(f"FastAPI Backend Port 7071 ({py_count} procs): RSS = {py_rss:6.2f} MB | Private Commit = {py_private:6.2f} MB")
    print(f"Caddy Web Server Port 7070 ({caddy_count} procs): RSS = {caddy_rss:6.2f} MB | Private Commit = {caddy_private:6.2f} MB")
    print("-" * 70)

    total_private = pg_private + py_private + caddy_private
    total_rss = pg_rss + py_rss + caddy_rss

    print(f"TOTAL STACK (Private Commit / True RAM): {total_private:6.2f} MB (Budget <= 150 MB)")
    print(f"TOTAL STACK (Working Set / Naive Sum):   {total_rss:6.2f} MB")
    print("-" * 70)
    if total_private <= 150.0:
        print(f"STATUS: [PASS] Physical Memory Budget strictly respected! Headroom: {150.0 - total_private:.2f} MB")
    else:
        print(f"STATUS: [WARN] Private memory exceeds 150 MB by {total_private - 150.0:.2f} MB")
    print("=" * 70)

if __name__ == '__main__':
    measure()
