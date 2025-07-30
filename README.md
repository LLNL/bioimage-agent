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

---

## 🧪 Testing

The project includes comprehensive test suites to ensure the MCP server and client functionality work correctly.

### Unit Tests

Run the main test suite:

```bash
cd tests
python test_napari_manager.py
```

This test suite includes:
- **Connection diagnostics** - Tests connection with different timeout values
- **Basic functionality** - Core napari operations (load files, list layers, etc.)
- **Layer management** - Create, modify, and remove layers
- **Data export** - Screenshots, data extraction
- **Visualization controls** - Camera, view controls, colormaps
- **Time series functions** - Multi-dimensional data handling
- **Measurement tools** - Distance, area calculations

### Interactive Testing

For interactive testing and exploration, use the Jupyter notebook:

```bash
cd tests
jupyter notebook test_napari_manager_socket.ipynb
```

This notebook provides step-by-step examples of:
- Loading different file formats (TIF, NPZ)
- Managing layers
- Taking screenshots
- Basic napari operations

### Test Data

The `tests/test_files/` directory contains sample data for testing:
- `test_layers.tif` - Sample image data
- `test_screenshot.png` - Expected screenshot output

---

## 📊 Evaluation

The `eval/` directory contains evaluation tools and configurations for testing the MCP server with AI agents.

### MCP Client Evaluation

The `general_mcp_client.py` provides a comprehensive MCP client that supports:
- **Multiple LLM providers** - Claude, OpenAI, and LiteLLM-compatible endpoints
- **Image support** - Handles image inputs and outputs for both providers
- **Tool execution** - Processes MCP tool calls and formats responses
- **Error handling** - Robust error handling and retry logic

### Automated Testing with Promptfoo

Use the `test_general.yaml` configuration to run automated evaluations:

```bash
cd eval
promptfoo eval -c test_general.yaml
```

This evaluates:
- **File loading** - Loading TIF files into napari
- **Layer management** - Checking layer existence and properties
- **Screenshot capture** - Taking and verifying screenshots
- **LLM rubric scoring** - AI-powered evaluation of task completion

### Evaluation Examples

The `eval/eval_examples/` directory contains sample data for evaluation:
- Multi-channel TIF files for testing complex data loading
- Time series data for testing temporal operations

### Evaluation Configuration

The evaluation setup supports:
- **Custom LLM endpoints** - Configure your own API endpoints
- **Model selection** - Choose different LLM models for evaluation
- **Caching control** - Enable/disable result caching
- **Concurrent execution** - Control parallel test execution

---

## Authors 
Napari_MCP was created by Haichao Miao (miao1@llnl.gov) and Shusen Liu (liu42@llnl.gov)

## License
Napari_MCP is distributed under the terms of the BSD-3 license.

LLNL-CODE-XXXXXXX
