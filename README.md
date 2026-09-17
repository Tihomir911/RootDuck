# RootDuck 🦆

Self-hosted monitoring hub for your home Docker server. Lightweight C++
agent secures the connection with a TLS handshake and one-time token;
Python microservices expose Docker container stats, system metrics, and
custom process monitoring; a PySide6 desktop client (Windows/Linux)
visualizes it all in a clean dark-themed GUI.

## Architecture

- `agent/` — C++ CLI/daemon. `rootduck-agent sysconnect` generates a
  TLS certificate and a one-time token, then runs a TLS proxy in front
  of `api-gateway`. No business logic — only connection security.
- `backend/` — Python microservices (FastAPI), run via `docker-compose.yml`:
  `apiGateway`, `authService`, `dockerAgentService`, `processWatcher`,
  `metricsCollector`.
- `client/` — PySide6 desktop client (Windows/Linux).
- `docs/` — architecture notes.

## Status

🚧 Work in progress — see `docs/ARCHITECTURE.md` for the roadmap.

## Quick start (partial — still being built)

```bash
# On the server:
cd agent && mkdir build && cd build && cmake .. && make
sudo ./rootduck-agent sysconnect

# Backend (on the server, next to agent):
docker compose up -d

# Client (on your machine):
cd client && pip install -r requirements.txt
python mainGui.py
```