import subprocess
import time
import os

def free_port(port):
    killed = 0
    try:
        out = subprocess.check_output("netstat -ano", shell=True, text=True, errors="ignore")
        for line in out.splitlines():
            parts = line.strip().split()
            if len(parts) >= 5 and f":{port}" in parts[1]:
                pid = parts[-1]
                if pid.isdigit() and int(pid) != os.getpid():
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    killed += 1
    except Exception:
        pass
    return killed

if __name__ == "__main__":
    k8000 = free_port(8000)
    k5173 = free_port(5173)
    time.sleep(0.5)
    print(f"Puertos liberados: 8000 ({k8000} procesos cerrados), 5173 ({k5173} procesos cerrados).")
