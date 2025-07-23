# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Enhanced RS485/TCP communication testing tool with modular architecture. Features GUI and command-line interfaces for testing serial devices, analyzing Modbus protocol packets, managing multiple connections, and exporting communication logs to Excel. The codebase has been refactored for maintainability with clean separation of concerns.

## Common Commands

### Running the Application
```bash
# GUI version (main application)
python rs485_tester/UIVersion.py

# Command-line version  
python rs485_tester/cmdVersion.py

# Run pre-built executable
rs485_tester/dist/UIVersion.exe

# Run as module (if needed)
python -m rs485_tester.UIVersion
```

### Building Executable
```bash
# Build using PyInstaller
pyinstaller rs485_tester/UIVersion.spec

# The executable will be created in rs485_tester/dist/
```

### Development Setup
```bash
# Install required packages
pip install pyserial openpyxl

# tkinter is included with Python standard library
# No additional setup required - code handles missing dependencies gracefully
```

### Testing
```bash
# Test GUI application
cd rs485_tester && python UIVersion.py

# Test imports
python -c "from rs485_tester.constants import *; print('Constants loaded')"
python -c "from rs485_tester.data_utils import DataFormatter; print('Data utils loaded')"
```

## Code Architecture

### Modular Structure (Post-Refactor)

The codebase has been refactored from a single 947-line file into focused modules:

- **`UIVersion.py`** (684 lines) - Main GUI application controller with clean event handling
- **`constants.py`** - All configuration constants, themes, command definitions, timeouts
- **`data_utils.py`** - Data formatting utilities and Modbus packet analysis
- **`connection_manager.py`** - Connection lifecycle, statistics, TCP/Serial abstraction
- **`ui_components.py`** - Reusable UI components (ThemeManager, LogManager, StatusBar, AnalysisPanel)
- **`serial_utils.py`** - Core RS485 communication library
- **`log_exporter.py`** - Excel export functionality for communication logs
- **`cmdVersion.py`** - Simple command-line interface
- **`byteCompare.py`** - Hex data comparison utility

### Architecture Patterns

- **Modular Design**: Each module has single responsibility and clear interfaces
- **MVC Pattern**: Models (ConnectionManager, stats), Views (UI components), Controllers (main app)
- **Component-Based UI**: Reusable components reduce code duplication
- **Dependency Injection**: Components receive dependencies, improving testability
- **Multi-threading**: Non-blocking communication with proper thread safety
- **Strategy Pattern**: Different connection types (Serial/TCP) with unified interface

### Key Classes and Responsibilities

#### Core Application
- **`EnhancedRS485GuiApp`** - Main application controller, coordinates all components
- **`ConnectionDialog`** - Modal dialog for creating new connections with validation

#### Connection Management
- **`ConnectionManager`** - Manages all connection lifecycles, statistics, auto-send states
- **`ConnectionStats`** - Tracks performance metrics for individual connections  
- **`TCPConnection`** - TCP client implementation with error handling

#### UI Components
- **`ThemeManager`** - Handles light/dark theme switching and style application
- **`LogManager`** - Manages multiple log tabs and message routing
- **`StatusBar`** - Status display with real-time clock
- **`AnalysisPanel`** - Packet analysis interface with format conversion

#### Data Processing
- **`DataFormatter`** - Static methods for HEX/ASCII/Decimal/Binary conversions
- **`ModbusPacketAnalyzer`** - Modbus protocol packet parsing and analysis

### Import Strategy

The modules use a flexible import strategy to work both as standalone scripts and as part of the package:

```python
try:
    from .constants import MODBUS_FUNCTIONS  # Relative import
except ImportError:
    from constants import MODBUS_FUNCTIONS   # Absolute import
```

### Error Handling Improvements

- **Specific Exceptions**: `ConnectionError`, `ValueError` with descriptive messages
- **Input Validation**: All user inputs validated before processing
- **Graceful Degradation**: Missing dependencies handled with fallbacks
- **User-Friendly Messages**: Technical errors translated to user-understandable text
- **Timeout Management**: Configurable timeouts for all network operations

### Configuration Management

All configuration moved to `constants.py`:

```python
# UI Constants
MAIN_WINDOW_SIZE = "1200x800"
DEFAULT_TIMEOUT = 5.0
MIN_INTERVAL = 100

# Modbus Commands
COMMON_COMMANDS = {
    "查詢狀態": "01 03 00 00 00 01 84 0A",
    "讀取資料": "01 04 00 00 00 02 71 CB",
    # ...
}

# Themes
THEMES = {
    "light": {"bg": "#FFFFFF", "fg": "#000000"},
    "dark": {"bg": "#2D2D2D", "fg": "#FFFFFF"}
}
```

## Development Guidelines

### Code Style
- Private methods use `_` prefix (e.g., `_setup_ui()`)
- Descriptive method names indicating purpose
- Each method has single responsibility
- Comprehensive docstrings for public methods

### Adding New Features
1. Check if it belongs in existing module or needs new one
2. Add constants to `constants.py` if needed
3. Use dependency injection for testability
4. Follow existing error handling patterns
5. Update CLAUDE.md with new functionality

### Common Patterns
- Event handlers use `_on_*` naming
- UI setup methods use `_create_*` or `_setup_*`
- Thread-safe operations use `root.after()` for UI updates
- All user-facing text in Chinese
- Configuration through constants rather than hard-coded values

## Project Features

### Core Functionality
- **Multi-Connection Support**: Manage multiple Serial/TCP connections simultaneously
- **Real-Time Monitoring**: Live statistics and performance tracking
- **Protocol Analysis**: Built-in Modbus RTU/TCP packet analyzer
- **Data Logging**: Structured logging with Excel export capability
- **Theme Support**: Light/dark mode with consistent styling

### UI Features
- **Tabbed Interface**: Connection management, monitoring, and analysis tabs
- **Multi-Format Display**: HEX, ASCII, Decimal, Binary data representation
- **Auto-Send**: Configurable interval-based command transmission
- **Broadcast Mode**: Send commands to all connections simultaneously
- **Connection Statistics**: Success rates, response times, error tracking

### Technical Features
- **Thread Safety**: Non-blocking UI with proper synchronization
- **Error Recovery**: Automatic reconnection and graceful error handling
- **Flexible Configuration**: Easy customization through constants
- **Modular Design**: Easy to extend and maintain
- **Cross-Platform**: Works on Windows, Linux, macOS

## Notes for Future Development

- The modular structure makes it easy to add new connection types
- UI components are reusable for other projects
- Error handling follows consistent patterns
- All magic numbers have been eliminated
- The codebase is now much more maintainable and testable