import requests

BASE_URL = "https://www.myfxbook.com/api"


def login(email: str, password: str) -> str:
    resp = requests.get(f"{BASE_URL}/login.json", params={"email": email, "password": password}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"Myfxbook login failed: {data.get('message')}")
    return data["session"]


def get_my_accounts(session: str) -> list:
    resp = requests.get(f"{BASE_URL}/get-my-accounts.json", params={"session": session}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(f"Myfxbook get-my-accounts failed: {data.get('message')}")
    return data["accounts"]


def logout(session: str) -> None:
    # Best-effort - a failed logout shouldn't fail the run, the session just
    # expires on its own.
    try:
        requests.get(f"{BASE_URL}/logout.json", params={"session": session}, timeout=15)
    except Exception:
        pass
