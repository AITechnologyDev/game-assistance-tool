# Game Assistance Tool - Phantom Edition
**Version 1.0.0** | *Created by AiTechnologyDev*

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Advanced game assistance suite featuring:
- 🎯 Motion-based targeting system
- 💰 AI-powered economy management
- 🔫 Adaptive recoil control
- 🤖 Local GGUF model integration
- ⚡ Performance optimized design

## Features
- **Local AI Advisor**: Offline economy recommendations
- **Smart Targeting**: Motion-based enemy detection
- **Quick Setup**: One-time configuration
- **Privacy Focused**: No data leaves your computer
- **Cross-Game**: Works with CS2, Valorant, Apex Legends

## Installation
```bash
git clone https://github.com/AiTechnologyDev/game-assistance-tool
cd game-assistance-tool
pip install -r requirements.txt

# Download AI model (example):
mkdir models
wget -P models/ https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf
```

## Usage
```bash
python src/assistant.py

# First-time setup:
Press Ctrl+S
Enter game: cs2
Enter team: CT

# During gameplay:
- F1: Toggle recoil control
- F2: Toggle motion aim
- Space: Shoot when target locked
```

## Configuration
Edit settings in `src/assistant.py`:
```python
# Essential settings
MONEY_REGION = (100, 50, 200, 40)    # Adjust for your game
ROUND_REGION = (900, 50, 100, 40)    # Adjust for your game
MODEL_PATH = "models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
```

## System Requirements
- OS: Windows 10/11, Linux
- RAM: 8GB+ (16GB recommended for AI)
- Storage: 5GB free space (for models)

## Supported AI Models
| Model | Size | Recommended |
|-------|------|-------------|
| [Mistral-7B](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF) | 4.1GB | ★★★★★ |
| [Phi-2](https://huggingface.co/TheBloke/phi-2-GGUF) | 1.6GB | ★★★★☆ |
| [TinyLlama](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF) | 0.8GB | ★★★☆☆ |

## Legal Notice
**This software is for educational purposes only.** Using game assistance tools in multiplayer games may violate Terms of Service. The developer assumes no responsibility for account penalties or bans. Always respect game developers' rules and other players' experiences.

[Contributing](CONTRIBUTING.md) | [License](LICENSE) | [Telegram](https://t.me/AiTechnologyDev)

---
**Created with ❤️ by AiTechnologyDev**  
*Advanced Game Research Project - v1.0.0*