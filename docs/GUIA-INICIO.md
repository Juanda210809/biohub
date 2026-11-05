# Primeros pasos

## 1. Instalar (una sola vez)

| Herramienta | Comprobar en PowerShell |
|---|---|
| Git | `git --version` |
| Docker Desktop (con WSL 2) | `docker version` debe mostrar **Client** y **Server** |
| Python 3.12 | `python --version` |
| Node.js LTS (solo quien trabaja el portal) | `node --version` |
| VS Code + extensiones | ver abajo |

Extensiones de VS Code (pégalas en PowerShell):

```powershell
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension ms-azuretools.vscode-docker
code --install-extension eamodio.gitlens
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension humao.rest-client
code --install-extension EditorConfig.EditorConfig
```

Configura Git con tu nombre y el correo de tu cuenta de GitHub:

```powershell
git config --global user.name "Tu Nombre"
git config --global user.email "tu-correo@ejemplo.com"
```

## 2. Descargar el proyecto (una sola vez)

```powershell
cd $HOME\git
git clone https://github.com/<organizacion>/biohub.git
cd biohub
Copy-Item .env.example .env
code .
```

## 3. Levantar el sistema

Abre **Docker Desktop** (debe decir *Engine running*). En la terminal de VS Code:

```powershell
docker compose up --build
```

Abre http://localhost:5173: deben salir **5 tarjetas en verde**. La de Consulta debe decir
«Filas replicadas: 1»; eso confirma que la replicación entre bases funciona.

Para detener todo: `Ctrl + C`, o en otra terminal `docker compose down`.

## 4. Comandos del día a día

| Quiero… | Comando |
|---|---|
| Levantar todo en segundo plano | `docker compose up -d` |
| Ver qué contenedores corren | `docker compose ps` |
| Ver los mensajes de mi servicio | `docker compose logs -f registro` |
| Reconstruir solo mi servicio (cambié `requirements.txt`) | `docker compose up -d --build registro` |
| Correr las pruebas de mi servicio | `docker compose exec registro python -m pytest -q` |
| Apagar todo | `docker compose down` |
| **Borrar las bases y empezar de cero** | `docker compose down -v` y luego `docker compose up --build` |

No hace falta reiniciar al editar código Python: el servicio se recarga solo al guardar.

## 5. Revisar las bases con un cliente SQL (opcional)

| Base | Puerto en tu PC | Usuario / contraseña (del `.env`) |
|---|---|---|
| BD Operacional | `localhost:5442` | `postgres` / `postgres_local` |
| BD Consulta | `localhost:5443` | `postgres` / `postgres_local` |
| BD Reportes | `localhost:5444` | `postgres` / `postgres_local` |

Base de datos: `biohub`. Sirve cualquier cliente (DBeaver, pgAdmin o la extensión de PostgreSQL de VS Code).

## 6. Si algo falla

| Síntoma | Solución |
|---|---|
| `error during connect ... dockerDesktopLinuxEngine` | Docker Desktop está cerrado: ábrelo y espera *Engine running* |
| `port is already allocated` | Otro programa usa ese puerto (8000, 5173, 5442–5444). Ciérralo o cambia el puerto en `docker-compose.yml` |
| Una tarjeta en rojo con «sin conexion» | La base aún está arrancando: espera 30 s y recarga. Si sigue, `docker compose logs bd-operacional` |
| `exec ... no such file or directory` en un script `.sh` | El archivo quedó con finales de línea de Windows. Ejecuta `git add --renormalize .` o vuelve a clonar |
| La replicación no trae filas | `docker compose down -v` y `docker compose up --build` (las bases se crean de nuevo) |
| Cualquier otra cosa | Copia el error completo y pégalo en el grupo del equipo |
