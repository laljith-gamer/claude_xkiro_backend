# claude_xkiro_backend

A proxy backend that connects Claude Desktop to free AI models via the [xKiro](https://xkiro.com) API.

## Features

- Routes Claude Desktop requests through a local proxy to xKiro's free API
- Model mapping: each Claude model selector maps to a different free model
- Easy setup with batch scripts

## Setup (PowerShell)

### Step 1: Clone the repo
```powershell
git clone https://github.com/laljith-gamer/claude_xkiro_backend.git
cd claude_xkiro_backend
```
> Downloads the project and enters the folder.

### Step 2: Install dependencies
```powershell
pip install flask requests python-dotenv
```
> Installs the Python packages needed to run the proxy.

### Step 3: Create your `.env` file
```powershell
copy .env.example .env
```
> Then open `.env` and paste your xKiro API key. Get a free key at [xkiro.com](https://xkiro.com) (5M tokens/day, no credit card).

### Step 4: Start the proxy
```powershell
python proxy.py
```
> Starts the local proxy server on `http://127.0.0.1:3000`.

### Step 5: Configure Claude Desktop
Point Claude Desktop to:
```
http://127.0.0.1:3000
```
> Update your `claude_desktop_config.json` or Claude Desktop settings to use the local proxy URL.

---

## Model Mapping

Each Claude model in the selector maps to a free xKiro model:

| Claude Model | xKiro Model |
|-------------|-------------|
| Opus 4.8 | `deepseek/deepseek-v4-pro` |
| Sonnet 5 | `qwen/qwen3.8-max:free` |
| Fable 5 | `qwen/qwen3-coder-plus:free` |
| Opus 5 | `deepseek/deepseek-v4-flash` |
| Sonnet 4.6 | `mistralai/mistral-medium-3.5` |
| Haiku 4.5 | `minimax/minimax-m3:free` |
| Opus 4.6 | `qwen/qwen3.7-max:free` |
| Fable 5.1 | `openai/gpt-5.3-codex-spark` |
| Opus 4.7 | `qwen/qwen3.5-397b-a17b:free` |

## Files

| File | Description |
|------|-------------|
| `proxy.py` | Main proxy server |
| `models.json` | Model configuration and mappings |
| `setup.bat` | Install Python dependencies |
| `start-proxy.bat` | Start the proxy server |
| `stop-proxy.bat` | Stop the proxy server |
| `switch-model.bat` | Switch between AI models |
| `claude_desktop_config.json` | Claude Desktop configuration |

## License

MIT
