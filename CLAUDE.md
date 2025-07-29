# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a **期货交易系统** (Futures Trading System) built with Python and PyQt5, using the vn.py trading framework. It's designed for real-time trading on major Chinese futures exchanges (SHFE, DCE, CZCE, CFFEX, INE) via CTP (China Trading Platform) gateway.

## Key Commands

### Development & Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python ui/main.py
# Or on Windows
start.bat

# Run tests
python -m pytest tests/
python tests/test_login.py
python test_simple.py

# Run chart tests
python tests/test_futures_chart.py
run_chart_test.bat
```

### Testing Single Components
```bash
# Test login functionality
python tests/test_login.py

# Test market monitoring
python tests/test_market_monitor.py

# Test order monitoring
python tests/test_order_monitor.py
```

## Architecture Overview

### Core Components
- **MainEngine** (`vnpy.trader.engine.MainEngine`): Central business logic hub
- **EventEngine** (`vnpy.event.EventEngine`): Event-driven message processing
- **CTP Gateway** (`vnpy_ctp.CtpGateway`): Connection to futures brokerage systems
- **MainWindow** (`ui/main.py`): Primary PyQt5 application window

### UI Layout Structure
```
MainWindow
├── Left Panel: SimpleTradingComponent (order placement)
├── Right Panel: 
│   ├── MarketMonitor (real-time quotes)
│   ├── OrderMonitor (active orders)
│   └── TradeMonitor (executed trades)
└── Bottom Panel:
    ├── LogMonitor (system logs)
    ├── AccountMonitor (funds/balance)
    └── PositionMonitor (current positions)
```

### Key Modules
- **Trading**: `ui/trading_component.py` - Order entry and validation
- **Market Data**: `ui/market_monitor.py` - Quote display and subscription
- **Account**: `ui/account_monitor.py` - Balance and position tracking
- **Orders**: `ui/order_monitor.py` - Order status management
- **Trades**: `ui/trade_monitor.py` - Execution history
- **Risk**: `ui/risk_manager.py` - Risk control interface
- **Strategy**: `ui/strategy_manager.py` - Trading strategies

### Configuration System
- **Subscription Management**: `config/subscribed_symbols.py`
- **Logging**: `config/log_manager.py`
- **Paths**: `config/paths.py` - Centralized file locations
- **Risk Settings**: `config/risk_config.py`
- **Strategy Settings**: `config/strategy_config.py`

## Event System

### Core Event Types
- `EVENT_TICK`: Real-time market data
- `EVENT_ORDER`: Order status updates
- `EVENT_TRADE`: Trade executions
- `EVENT_ACCOUNT`: Account balance changes
- `EVENT_POSITION`: Position updates
- `EVENT_LOG`: System logging events

### Event Flow
1. **Data Flow**: CTP Server → CTP Gateway → EventEngine → UI Components → Display
2. **Trading Flow**: UI → TradingComponent → MainEngine → CTP Gateway → Server

## Testing Framework

### Test Structure
- **Unit Tests**: `tests/` directory with individual component tests
- **Integration Tests**: `tests/integration_test_*.py` for system-wide testing
- **Chart Tests**: `tests/test_futures_chart.py` for K-line chart functionality

### Testing Approach
- Uses `unittest` framework
- Mock objects for MainEngine and EventEngine
- PyQt5 QApplication setup for GUI testing
- CTP gateway simulation for trading tests

## File Organization

### Critical Paths
- **Config**: All configuration files in `config/` directory
- **UI Components**: Individual widgets in `ui/` with subdirectories
- **Charts**: Custom K-line charts in `ui/widgets/futures_chart.py`
- **Tests**: Comprehensive test suite in `tests/`
- **Gateways**: Trading gateway integrations in `gateways/`

### Data Storage
- **Subscriptions**: `config/subscribed_symbols.json` - User saved contract subscriptions
- **Logs**: Runtime logs displayed in UI and saved to `test_logs/`
- **Settings**: User preferences stored in JSON format

## Development Notes

### Key Patterns
- **Event-Driven Architecture**: All data flow through EventEngine
- **Signal-Slot Pattern**: PyQt5 signals for UI updates
- **Modular Design**: Each monitor/trading component is self-contained
- **Configuration Management**: Centralized JSON-based settings

### Common Development Tasks
1. **Adding new monitors**: Create new widget class, register event handlers
2. **Extending trading**: Modify TradingComponent for new order types
3. **New exchanges**: Add gateway configurations in gateway manager
4. **Risk controls**: Implement in RiskManager with risk engine integration

### Environment Setup
- **Python**: 3.7+ required (Windows recommended for CTP compatibility)
- **Dependencies**: PyQt5≥5.15.0, vnpy≥2.0.0
- **Platform**: Windows OS required for CTP interface compatibility