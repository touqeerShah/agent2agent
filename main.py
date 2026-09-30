import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent

SERVER_FILES = {
    "policy": "a2aServer/policy_server.py",
    "provider": "a2aServer/provider_server.py",
    "research": "a2aServer/research_server.py",
    "orchestrator": "a2aServer/orchestrator_server.py",
}
def signal_server(process, sig):
    if process.poll() is not None:
        return

    try:
        # Signal the group only if this process leads its own group.
        if os.getpgid(process.pid) == process.pid:
            os.killpg(process.pid, sig)
        else:
            process.send_signal(sig)
    except ProcessLookupError:
        pass
    except PermissionError:
        # Fall back to signaling only the server process.
        try:
            process.send_signal(sig)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            print(f"Could not stop PID {process.pid}: {error}")


def main() -> None:
    load_dotenv(ROOT / ".env")

    host = os.environ["AGENT_HOST"]
    # Use a connectable address when servers bind to all interfaces.
    connect_host = "127.0.0.1" if host == "0.0.0.0" else host

    ports = {
        "policy": int(os.environ["POLICY_AGENT_PORT"]),
        "provider": int(os.environ["PROVIDER_AGENT_PORT"]),
        "research": int(os.environ["RESEARCH_AGENT_PORT"]),
        "orchestrator": int(os.environ["HEALTHCARE_AGENT_PORT"]),
    }

    if len(set(ports.values())) != 4:
        raise ValueError("Each server needs a different port.")

    for script in SERVER_FILES.values():
        if not (ROOT / script).is_file():
            raise FileNotFoundError(ROOT / script)

    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(ROOT), env.get("PYTHONPATH")])
    )

    processes = {}

    def check_processes():
        for name, process in processes.items():
            code = process.poll()
            if code is not None:
                raise RuntimeError(
                    f"{name} server exited with code {code}. "
                    "Check its output above."
                )

    def start(name):
        print(f"Starting {name} on port {ports[name]}", flush=True)
        processes[name] = subprocess.Popen(
            [sys.executable, "-u", str(ROOT / SERVER_FILES[name])],
            cwd=ROOT,
            env=env,
            start_new_session=True,
        )

    def wait_ready(name, timeout=60):
        deadline = time.monotonic() + timeout
        base_url = f"http://{connect_host}:{ports[name]}"

        while time.monotonic() < deadline:
            check_processes()

            for path in (
                "/.well-known/agent-card.json",
                "/.well-known/agent.json",
            ):
                try:
                    with urlopen(base_url + path, timeout=1) as response:
                        card = json.load(response)
                    if isinstance(card, dict) and card.get("name"):
                        print(f"{name} ready: {card['name']}", flush=True)
                        return
                except (URLError, TimeoutError, OSError, ValueError):
                    pass

            time.sleep(0.5)

        raise TimeoutError(f"{name} was not ready after {timeout}s.")

    try:
        for name in ("policy", "provider", "research"):
            start(name)

        for name in ("policy", "provider", "research"):
            wait_ready(name)

        start("orchestrator")
        wait_ready("orchestrator")

        print(
            f"\nAll servers ready. Orchestrator: "
            f"http://{connect_host}:{ports['orchestrator']}\n"
            "Press Ctrl+C to stop them.",
            flush=True,
        )

        while True:
            check_processes()
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping servers...", flush=True)
    finally:
        for process in reversed(list(processes.values())):
            signal_server(process, signal.SIGTERM)

        for name, process in processes.items():
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                signal_server(process, signal.SIGKILL)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"{name} did not stop; PID {process.pid}")

if __name__ == "__main__":
    main()