#!/usr/bin/env bash
set -euo pipefail

echo "=== OS / Python / user ==="
uname -a || true
cat /etc/os-release || true

python3 --version || true
python3 -c "import sys,platform; print(sys.executable, platform.python_version(), platform.platform())" || true

id || true

echo
echo "=== CPU / Memory / Disk ==="
nproc || true
lscpu || cat /proc/cpuinfo | grep -E 'model name|cpu cores|siblings' || true

free -h || true
cat /proc/meminfo | egrep 'MemTotal|MemAvailable' || true

df -h || true
df -i || true                    # inode usage
lsblk -f || true
mount | column -t || true
# optional: show mount options for current working dir (if findmnt available)
command -v findmnt >/dev/null && findmnt -no SOURCE,FSTYPE,OPTIONS "$(pwd)" || true

echo
echo "=== Network ==="
ip addr show || true
ip route show || true

echo "Ping sample (5 pings) to example.com — replace example.com when running"
ping -c 5 example.com || true

echo
echo "curl throughput sample (replace <URL>)"
echo 'curl -o /dev/null -s -w "HTTP %{http_code}  size:%{size_download}  speed:%{speed_download}B/s  time:%{time_total}s\n" "<URL>"'
# user should replace <URL> when running

echo
echo "=== Optional: iperf3 ==="
echo "iperf3 -c <iperf-server-host> (only if you have access and iperf3 installed)"

echo
echo "=== Limits / kernel network tunables ==="
ulimit -n || true
ulimit -u || true
ulimit -a || true

sysctl net.core.somaxconn || true
sysctl net.core.netdev_max_backlog || true
sysctl net.ipv4.tcp_max_syn_backlog || true
sysctl net.ipv4.ip_local_port_range || true
sysctl net.ipv4.tcp_fin_timeout || true
sysctl net.ipv4.tcp_tw_reuse || true

echo
echo "=== Python env / requests ==="
python3 -m pip --version || true
python3 -c "import requests,sys; print('requests', getattr(requests,'__version__','?'), 'python', sys.version.split()[0])" || true

python3 -m pip freeze | sed -n '1,200p' || true

echo
echo "=== Storage write speed test (optional) ==="
echo "This creates a 100 MiB file in the current directory. Remove if not desired."
read -r -p "Run write test? [y/N] " run_write_test || true
if [[ "${run_write_test:-N}" =~ ^[Yy]$ ]]; then
  sync; dd if=/dev/zero of=./download_test_file bs=1M count=100 oflag=direct 2>&1 || true
  sync
  rm -f ./download_test_file || true
fi

echo
echo "=== Proxy / firewall ==="
env | egrep -i 'http_proxy|https_proxy|no_proxy' || true
sudo iptables -L -n -v || sudo nft list ruleset || true

echo
echo "=== URLs summary & probes ==="
if [[ ! -f urls.txt ]]; then
  echo "urls.txt not found in $(pwd). Place your urls.txt here or pass path manually."
else
  wc -l urls.txt || true

  echo
  echo "Unique host counts (helps choose per-host concurrency)"
  awk -F/ 'NF>2{print $3}' urls.txt | sed 's/:.*$//' | sort | uniq -c | sort -rn | head -n 200 || true

  echo
  echo "Show first 50 URLs and probe headers (status, Content-Length, Accept-Ranges, Server, Retry-After)"
  head -n 50 urls.txt | nl -ba | while read -r i url; do
    echo "---- $i $url ----"
    curl -sI -L --max-redirs 5 "$url" | egrep -i 'HTTP/|Content-Length:|Accept-Ranges:|Retry-After:|Server:|Content-Type:|Transfer-Encoding:' || true
    echo
  done

  echo
  echo "Sample Accept-Ranges test (first 20 URLs): try a ranged GET for first 1MiB"
  head -n 20 urls.txt | nl -ba | while read -r i url; do
    echo "[$i] $url"
    # show header then try single ranged request (no output)
    curl -sI -L --max-redirs 5 "$url" | egrep -i 'Accept-Ranges:|Content-Length:' || true
    # try a ranged GET to see server response code and size
    curl -s -r 0-1048575 -o /dev/null -w "  code:%{http_code} size:%{size_download} time:%{time_total}s\n" "$url" || true
    echo
  done

  echo
  echo "Estimate total Content-Length for first N (best-effort; many servers omit Content-Length)"
  head -n 200 urls.txt | xargs -n1 -P10 -I{} sh -c 'curl -sI -L --max-redirs 3 "{}" | awk '\''/Content-Length:/ {print $2} '\'' ' | awk '{s+=$1} END{print s}' || true
fi

echo
echo "=== Environment detection ==="
# detect docker/container/WSL
if grep -qE '/docker|/kubepods|containerd' /proc/1/cgroup 2>/dev/null || [ -f /.dockerenv ]; then
  echo "Running inside a container"
fi
if grep -qi microsoft /proc/version 2>/dev/null; then
  echo "WSL detected"
fi

echo
echo "=== Useful manual checks to run if available ==="
echo "- Compare ulimit -n to expected open files: #workers * (1-3 sockets) + extra"
echo "- Ensure target output directory is on local disk (not slow NFS) or has enough free space"
echo "- If servers return 429/503, capture Retry-After headers to tune backoff"
# ...existing code...
