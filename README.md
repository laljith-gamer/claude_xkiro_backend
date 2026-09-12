# claude_xkiro_backend

A proxy backend that connects Claude Desktop to free AI models via the [xKiro](https://xkiro.com) API.

## Features

- Routes Claude Desktop requests through a local proxy to xKiro's free API
- Model mapping: each Claude model selector maps to a different free model
- Easy setup with batch scripts

## Quick Start

1. Clone this repo
2. Copy `.env.example` to `.env` and add your xKiro API key
3. Run `setup.bat` to install dependencies
4. Run `start-proxy.bat` to start the proxy
5. Configure Claude Desktop to point to `http://127.0.0.1:3000`

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
