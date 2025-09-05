import socket
from typing import Optional
import psutil


def check_port_in_use(port: int) -> bool:
    """Return True if the TCP port is in use on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", port))
            return result == 0
    except Exception:
        return False


def get_process_using_port(port: int) -> Optional[str]:
    """Return a short description of the process using the port, or None.

    Description includes process name and PID; keeps side effects out for reuse.
    """
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                for conn in proc.net_connections(kind="tcp"):
                    if conn.laddr.port == port and conn.status in [
                        psutil.CONN_LISTEN, psutil.CONN_ESTABLISHED
                    ]:
                        status_desc = (
                            "LISTEN" if conn.status == psutil.CONN_LISTEN else "ESTABLISHED"
                        )
                        return f"{proc.info['name']} (PID: {proc.info['pid']}) - {status_desc}"
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass
    return None


def kill_process_on_port(port: int) -> bool:
    """Try to terminate the process listening on the port. Returns True on success.

    Attempts gentle terminate first, then kill as fallback. Silent utility.
    """
    try:
        target_proc = None

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                for conn in proc.net_connections(kind="tcp"):
                    if conn.laddr.port == port and conn.status in [
                        psutil.CONN_LISTEN, psutil.CONN_ESTABLISHED
                    ]:
                        target_proc = proc
                        break
                if target_proc:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        if not target_proc:
            return False

        try:
            target_proc.terminate()
            try:
                target_proc.wait(timeout=3)
                return True
            except psutil.TimeoutExpired:
                target_proc.kill()
                try:
                    target_proc.wait(timeout=2)
                    return True
                except psutil.TimeoutExpired:
                    return False
        except psutil.NoSuchProcess:
            return True
        except psutil.AccessDenied:
            try:
                import os
                import time
                os.system(f"kill -TERM {target_proc.pid}")
                time.sleep(2)
                if not psutil.pid_exists(target_proc.pid):
                    return True
                os.system(f"kill -KILL {target_proc.pid}")
                time.sleep(1)
                return not psutil.pid_exists(target_proc.pid)
            except Exception:
                return False
        except Exception:
            return False
    except Exception:
        return False


