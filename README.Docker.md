**Core Lifecycle Commands**

| Command | Description |
| --- | --- |
| `docker compose up -d` | Build, create, and start containers in detached mode (background) |
| `docker compose up --build` | Force a rebuild of images before starting containers |
| `docker compose down` | Stop and remove containers, networks, and anonymous volumes |
| `docker compose down -v` | Stop and remove containers, networks, and **named volumes** |
| `docker compose start` / `stop` | Start or stop existing containers without destroying them |
| `docker compose restart` | Restart running services |
| `docker compose pause` / `unpause` | Pause or resume container processes |

---

**Monitoring & Debugging**

| Command | Description |
| --- | --- |
| `docker compose ps` | List status of all services in current Compose file |
| `docker compose logs -f` | Tail and follow live logs for all services |
| `docker compose logs -f <service>` | Follow logs for a specific service (e.g., `web`, `db`) |
| `docker compose top` | Display the running processes of containers |
| `docker compose config` | Validate, resolve variables, and view effective Compose YAML |

---

**Execution & Maintenance**

| Command | Description |
| --- | --- |
| `docker compose exec -it <service> sh` | Open an interactive shell inside a running service |
| `docker compose run --rm <service> <cmd>` | Run a one-off command in a service container and remove it after |
| `docker compose build --no-cache` | Build/rebuild images without using cache |
| `docker compose pull` | Pull updated remote images defined in the compose file |
