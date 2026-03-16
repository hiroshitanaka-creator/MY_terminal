# MY Terminal

**iPhone-optimized Python web terminal** — iPhoneだけで動く実験用ターミナル環境。

## Features

| Tab | 機能 |
|-----|------|
| `>_` Terminal | WebSocket PTY — bash/Python REPLをリアルタイム操作 |
| `AI API` | OpenAI / Anthropic Claude API テストUI（プリセット10スロット） |
| `PyPI` | pip install/uninstall/list をワンタップで |
| `Black` | Pythonコードを貼り付けてBlackで整形・コピー |

## Quick Start

```bash
# Clone (or copy terminal/ into any repo)
git clone <this-repo>
cd MY_terminal

# Start (bare-metal)
export MY_TERMINAL_TOKEN=your-secret-token
./start.sh
# → http://<your-ip>:8765

# Or with Docker
MY_TERMINAL_TOKEN=your-secret-token docker-compose up
```

iPhoneのSafariで `http://<IP>:8765` を開き、ホーム画面に追加するとPWAとして動く。

## Multi-Repo Usage

```bash
# 他のリポジトリに流用する場合
cp -r MY_terminal/terminal/ your_repo/terminal/
cp MY_terminal/start.sh your_repo/
cp MY_terminal/docker-compose.yml your_repo/
# → your_repo で ./start.sh
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MY_TERMINAL_TOKEN` | `changeme` | アクセストークン（必ず変更すること） |
| `PORT` | `8765` | サーバーポート |
| `SHELL` | `/bin/bash` | ターミナルシェル |

## Security Note

`MY_TERMINAL_TOKEN` は必ず安全な値に変更してください。
`data/api_presets.json` にはAPIキーが保存されます。`.gitignore` 済みですがコミットしないよう注意。

## Architecture

```
iPhone Safari
    │ WebSocket (PTY I/O)
    │ HTTP (API proxy, pip, Black)
    ▼
FastAPI (uvicorn)
├── /ws/pty          → ptyprocess bash
├── /api/ai-client   → httpx proxy (Anthropic/OpenAI)
├── /api/pip/*       → subprocess pip
└── /api/format      → black.format_str()
```
