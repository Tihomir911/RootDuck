import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path


from cryptography.fernet import Fernet, InvalidToken


APP_DATA_DIR = Path(os.environ.get("ROOTDUCK_DATA_DIR", Path.home() / ".config" / "rootduck"))
KEY_FILE = APP_DATA_DIR / "encryption.key"
SERVERS_FILE = APP_DATA_DIR / "servers.enc"


@dataclass
class ServerEntry:
    
    name: str   
    ip: str
    token: str


def _ensure_data_dir() -> None:
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_or_create_key() -> bytes:


    _ensure_data_dir()


    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()


    key = Fernet.generate_key()
    KEY_FILE.write_bytes(key)


    os.chmod(KEY_FILE, 0o600)


    return key


def load_servers() -> list[ServerEntry]:


    if not SERVERS_FILE.exists():
        return []


    key = _load_or_create_key()
    fernet = Fernet(key)


    encrypted = SERVERS_FILE.read_bytes()
    try:
        decrypted = fernet.decrypt(encrypted)
    except InvalidToken:


        print("serverStorage: не удалось расшифровать список серверов "
              "(повреждён файл или изменился ключ шифрования)")
        return []


    raw_list = json.loads(decrypted.decode("utf-8"))
    return [ServerEntry(**item) for item in raw_list]


def save_servers(servers: list[ServerEntry]) -> None:


    _ensure_data_dir()


    key = _load_or_create_key()
    fernet = Fernet(key)


    raw_list = [asdict(server) for server in servers]
    serialized = json.dumps(raw_list).encode("utf-8")
    encrypted = fernet.encrypt(serialized)


    SERVERS_FILE.write_bytes(encrypted)
    os.chmod(SERVERS_FILE, 0o600)


def add_server(name: str, ip: str, token: str) -> None:


    servers = load_servers()
    servers.append(ServerEntry(name=name, ip=ip, token=token))
    save_servers(servers)


def remove_server(ip: str) -> None:

  
    servers = load_servers()
    servers = [server for server in servers if server.ip != ip]
    save_servers(servers)