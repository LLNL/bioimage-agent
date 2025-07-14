# napari-mcp

A lightweight [napari](https://napari.org) plugin that exposes the viewer over **MCP (Message-Control Protocol)** via a Python socket server. Built on top of **[FastMCP](https://github.com/fastmcp/fastmcp)**, it lets external MCP-speaking clients—such as autonomous AI agents running on Claude or OpenAI—**call napari’s public API remotely**.

---

## 🔧 Requirements

| Package    | Version               |
| ---------- | --------------------- |
| Python     | ≥ 3.9                 |
| napari     | ≥ 0.5                 |
| fastmcp    | ≥ 0.3                 |
| Qt / PyQt5 | Installed with napari |

---

## 📦 Napari Installation 

```bash
python -m pip install "napari[all]"
```

### Install Socket Server Plugin

```bash
cd napari-mcp/src/napari_socket
pip install -e .
```

### Install MCP tools in your MCP Client

e.g. For Claude Desktop, go to Developer->Open App Config File and add the below snippet to "mcpServers"
```
"Napari": {
      "command": ".../python.exe",
      "args": [                        
        ".../napari-mcp/src/napari_mcp/napari_mcp_server.py"
      ],
      "env": {}
    }
```

---

## 🚀 Getting Started

1. **Launch napari**:

   ```bash
   napari
   ```
2. Choose **Plugins → Socket Server → Start Server**. You’ll see something like:

   ```text
   Listening on 127.0.0.1:64908
   ```

