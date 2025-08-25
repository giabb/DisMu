<div align="center">
<h1>DisMu</h1>
<div style="display: flex; align-items: center; justify-content: center; gap: 20px; border: none;">
<div>
<img src="https://i.ibb.co/gZf37YW8/DisMu.png" alt="Bot Logo" width="150">
</div>
<div>

**A powerful Discord Music Bot with comprehensive audio playback capabilities**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-GPL%203.0-red.svg)](LICENSE.md) 
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://docker.com)

[Features](#-features) • [Installation](#-installation) • [Configuration](#-configuration) • [Contributing](#-configuration)

</div>
</div>
</div>

---

## 📋 Table of Contents
- [✨ Features](#-features)
- [📋 Prerequisites](#-prerequisites)
- [🚀 Installation](#-installation)
  - [🐳 Docker Installation (Recommended)](#-docker-installation-recommended)
  - [🔧 Manual Installation](#-manual-installation)
- [⚙️ Configuration](#-configuration)
- [🎯 Usage](#-usage)
- [⚠️ Known Issues](#️-known-issues)
- [🗺️ Roadmap](#️-roadmap)
- [🤝 Contributing](#-contributing)
- [👥 Contributors](#-contributors)
- [📄 License](#-license)
- [🙏 Credits](#-credits)

## ✨ Features

### 🎶 **Core Features**
- **YouTube Integration**: Play music from URLs, playlists, and search results
- **Multi-Guild Support**: Individual settings and queues per Discord server
- **Advanced Queue Management**: Add, remove, shuffle, bump, and reorder tracks
- **Playlist Support**: Import entire YouTube playlists with automatic shuffling
- **Interactive Search**: Browse and select from YouTube search results
- **Paginated Interfaces**: Clean, navigable embeds for queues and search results
- **Auto-Cleanup**: Automatic message deletion to keep channels tidy
- **Error Handling**: Graceful error management with user-friendly messages

## 📋 Prerequisites

### 🐳 **Docker Installation (Recommended)**
- [Docker](https://docs.docker.com/get-docker/) installed on your system
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker)

### 🔧 **Manual Installation**
- **Python**: 3.12 or higher
- **FFmpeg**: [Download and install](https://ffmpeg.org/download.html)
- **Python Dependencies**: Choose one option:
  - Use `requirements.txt` with pip
  - Use `pyproject.toml` with [Poetry](https://python-poetry.org/)
  - Install manually: `discord.py 2.5.2+`, `PyNaCl 1.5.0+`, `python-dotenv 1.1.1+`, `yt-dlp (latest)`

## 🚀 Installation

### Step 1: Environment Configuration

1. **Clone the repository**
   ```bash
   git clone https://github.com/giabb/DisMu.git
   cd DisMu
   ```

2. **Create environment file**
   ```bash
   cp .env.sample .env
   ```

3. **Get your Discord Bot Token**
   - Follow this [comprehensive guide](https://www.writebots.com/discord-bot-token/)
   - Ensure your bot has these Discord permissions:
      - ✅ Connect to Voice Channels
      - ✅ Speak in Voice Channels  
      - ✅ Send Messages
      - ✅ Embed Links
      - ✅ Read Message History
      - ✅ Manage Messages (for cleanup)

4. **Configure your `.env` file**
   ```env
   # Required
   BOT_TOKEN=your_discord_bot_token_here
   
   # Optional (defaults provided)
   DEFAULT_PREFIX=%
   DEFAULT_DELETE_TIME=15
   EMBED_AUTODELETE=60
   SEARCH_TIMEOUT=60
   ```

### 🐳 **Docker Installation (Recommended)**

**Quick Start:**
```bash
docker compose up --build -d
```

**Reference for other docker compose commands:**
```bash
docker compose logs -f  # View logs in real time
docker compose down     # Stop and remove the container
docker compose stop     # Stop the container
docker compose restart  # Restart the container (if stopped)
```

### 🔧 **Manual Installation**

1. **Install Python dependencies**
   
   **Using pip:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   
   **Using Poetry:**
   ```bash
   poetry config virtualenvs.in-project true # This will create the .venv folder inside the project
   poetry install --no-root
   source .venv/bin/activate
   ```

2. **Run the bot**
   ```bash
   python -m src.main
   ```

## ⚙️ Configuration

### Environment Variables

| Variable              | Default    | Description                               |
|-----------------------|------------|-------------------------------------------|
| `BOT_TOKEN`           | *Required* | Your Discord bot token                    |
| `DEFAULT_PREFIX`      | `%`        | Command prefix for the bot                |
| `DEFAULT_DELETE_TIME` | `15`       | Seconds before auto-deleting messages     |
| `EMBED_AUTODELETE`    | `60`       | Seconds before auto-deleting embeds       |
| `SEARCH_TIMEOUT`      | `60`       | Seconds to wait for user search selection |

## 🎯 Usage

Once the bot is running and invited to your server:

1. **Test the bot**: Type `%help` (or your configured prefix)
2. **Join a voice channel** and use `%join` to connect the bot
3. **Play music**: `%play <YouTube URL>` or `%search <song name>`
4. **Explore commands**: Use `%help` to see all available commands

> **📚 For detailed command documentation, visit the [Wiki](https://github.com/giabb/DisMu/wiki/Extensive-Command-Guide)**

## ⚠️ Known Issues

Currently, there are no known major issues. 

If you encounter any problems:
1. Check the [Issues](https://github.com/giabb/DisMu/issues) page
2. Create a new issue with detailed information
3. Include logs and steps to reproduce

## 🗺️ Roadmap

### 🔄 **Upcoming Features**

- [ ] **Enhanced Commands**: Additional queue management and playback options
- [ ] **Playlist Persistence**: Save and load custom playlists
- [ ] **Spotify Integration**: Play tracks from Spotify playlists

## 🤝 Contributing

We love contributions! Here's how you can help:

### 🐛 **Bug Reports**
- Use the [issue tracker](https://github.com/giabb/DisMu/issues)
- Include detailed reproduction steps
- Provide error logs and environment details

### 🚀 **Feature Requests**
- Describe the feature and its benefits
- Provide use cases and examples
- Discuss implementation approaches

### 💻 **Code Contributions**
1. Fork the repository
2. Create a feature branch
3. Make your changes with proper documentation
4. Commit your changes
5. Push to the branch
6. Open a Pull Request

### 📝 **Documentation**
- Improve README or Wiki pages
- Add code comments and docstrings
- Create tutorials and guides

## 👥 Contributors

<div align="center">

**Project Creator & Maintainer**

[![Giovanbattista Abbate](https://github.com/giabb.png?size=100)](https://github.com/giabb)

**[Giovanbattista Abbate](https://github.com/giabb)**

</div>

---

*Want to contribute? See the [Contributing](#-contributing) section above!*

## 📄 License

This project is licensed under the **GNU General Public License v3.0**.

This means you can:
- ✅ Use the software for any purpose
- ✅ Study and modify the source code
- ✅ Distribute copies of the software
- ✅ Distribute modified versions

**Requirements:**
- 📋 Include the original license
- 📋 State changes made to the code
- 📋 Make source code available when distributing

See the [LICENSE.md](LICENSE.md) file for complete details.

## 🙏 Credits

- **README Template**: Inspired by [PurpleBooth](https://github.com/PurpleBooth)

---

<div align="center">

**Made with ❤️ for the Discord community**

[⭐ Star this repo](https://github.com/giabb/DisMu) • [🐛 Report Issues](https://github.com/giabb/DisMu/issues) • [💬 Discussions](https://github.com/giabb/DisMu/discussions)

</div>
