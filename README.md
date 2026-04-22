# Binance Futures Testnet Trading Bot

A production-quality CLI application for placing MARKET and LIMIT orders on the Binance Futures Testnet platform. Features clean modular architecture, comprehensive logging, input validation, and retry mechanisms.

## Features

- **Order Types**: MARKET, LIMIT, and STOP_LIMIT (stop-loss/take-profit) orders
- **Clean Architecture**: Modular design with separation of concerns
- **API Wrapper**: Custom Binance Futures client with HMAC-SHA256 authentication
- **Validation**: Comprehensive input validation for symbols, quantities, and prices
- **Logging**: Structured logging to both console and rotating file logs
- **Retry Logic**: Automatic retry with exponential backoff for failed API calls
- **Interactive Mode**: User-friendly prompts for order entry
- **Error Handling**: Detailed error messages for API, network, and validation errors

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package initialization
│   ├── client.py            # Binance API client wrapper
│   ├── orders.py            # Order placement logic
│   ├── validators.py        # Input validation
│   └── logging_config.py    # Logging configuration
├── cli.py                   # CLI entry point
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment file
└── logs/                    # Log files (created on first run)
    └── app.log
```

## Setup Instructions

### 1. Create Binance Testnet Account

1. Visit [Binance Testnet](https://testnet.binance.vision/)
2. Log in with your GitHub account
3. Generate API Key and Secret
4. Fund your testnet account with test USDT

### 2. Install Dependencies

```bash
cd trading_bot
pip install -r requirements.txt
```

### 3. Configure API Credentials

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_api_secret_here
```

**Or** set environment variables directly:

**Linux/Mac:**
```bash
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_api_secret"
```

**Windows (PowerShell):**
```powershell
$env:BINANCE_API_KEY="your_api_key"
$env:BINANCE_API_SECRET="your_api_secret"
```

**Windows (CMD):**
```cmd
set BINANCE_API_KEY=your_api_key
set BINANCE_API_SECRET=your_api_secret
```

## Usage

### Test Connection

Verify your API credentials and connection:

```bash
python cli.py --test
```

### Interactive Mode

Run with prompts for guided order entry:

```bash
python cli.py --interactive
```

### CLI Arguments

#### Place a MARKET Order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

#### Place a LIMIT Order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
```

#### Place a STOP_LIMIT Order (Stop-Loss)

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 --price 59000 --stop-price 60000
```

### CLI Options

| Option | Description | Required |
|--------|-------------|----------|
| `--symbol` | Trading pair (e.g., BTCUSDT) | Yes |
| `--side` | BUY or SELL | Yes |
| `--type` | MARKET, LIMIT, or STOP_LIMIT | Yes |
| `--quantity` | Order quantity | Yes |
| `--price` | Limit price (required for LIMIT/STOP_LIMIT) | Conditionally |
| `--stop-price` | Stop price (required for STOP_LIMIT) | Conditionally |
| `--interactive` | Interactive mode with prompts | No |
| `--test` | Test API connection only | No |
| `--verbose` | Enable debug logging | No |

## Example Commands

```bash
# MARKET BUY order for 0.01 BTC
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

# LIMIT SELL order at $60,000
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000

# STOP-LOSS: Sell 0.01 BTC if price drops to $60,000 (trigger), sell at $59,000 (limit)
python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 --price 59000 --stop-price 60000

# ETH example with interactive mode
python cli.py --interactive
```

## Example Log Output

### Successful MARKET Order Log

```
2024-01-15 10:30:45 | INFO     | trading_bot | Logging initialized. Log file: logs/app.log
2024-01-15 10:30:45 | INFO     | trading_bot | ORDER REQUEST | Symbol: BTCUSDT | Side: BUY | Type: MARKET | Quantity: 0.01
2024-01-15 10:30:46 | INFO     | trading_bot | Order attempt 1/3
2024-01-15 10:30:47 | INFO     | trading_bot | ORDER RESPONSE | OrderId: 123456789 | Status: FILLED | ExecutedQty: 0.01 | AvgPrice: 42350.50
2024-01-15 10:30:47 | INFO     | trading_bot | Order completed successfully
```

### Successful LIMIT Order Log

```
2024-01-15 10:35:12 | INFO     | trading_bot | Logging initialized. Log file: logs/app.log
2024-01-15 10:35:12 | INFO     | trading_bot | ORDER REQUEST | Symbol: ETHUSDT | Side: SELL | Type: LIMIT | Quantity: 0.1 | Price: 3000.00
2024-01-15 10:35:13 | INFO     | trading_bot | Order attempt 1/3
2024-01-15 10:35:14 | INFO     | trading_bot | ORDER RESPONSE | OrderId: 987654321 | Status: NEW | ExecutedQty: 0 | AvgPrice: N/A
2024-01-15 10:35:14 | INFO     | trading_bot | Order completed successfully
```

### Failed Order Log (Insufficient Margin)

```
2024-01-15 10:40:20 | INFO     | trading_bot | ORDER REQUEST | Symbol: BTCUSDT | Side: BUY | Type: MARKET | Quantity: 1.0
2024-01-15 10:40:21 | INFO     | trading_bot | Order attempt 1/3
2024-01-15 10:40:21 | ERROR    | trading_bot | API ERROR: API Error -2010: Account has insufficient balance for requested action. | Order attempt 1
2024-01-15 10:40:21 | ERROR    | trading_bot | ORDER FAILED | Response: {'code': -2010, 'msg': 'Account has insufficient balance for requested action.'}
```

## Console Output Examples

### Successful MARKET Order

```
==================================================
  Binance Futures Testnet Trading Bot
==================================================

ORDER REQUEST SUMMARY:
  Symbol:   BTCUSDT
  Side:     BUY
  Type:     MARKET
  Quantity: 0.01

==================================================
✅ ORDER PLACED SUCCESSFULLY
==================================================
Order ID:    123456789
Status:      FILLED
Executed:    0.01
Avg Price:   42350.50
==================================================
```

### Successful LIMIT Order

```
==================================================
  Binance Futures Testnet Trading Bot
==================================================

ORDER REQUEST SUMMARY:
  Symbol:   BTCUSDT
  Side:     SELL
  Type:     LIMIT
  Quantity: 0.01
  Price:    60000.0

==================================================
✅ ORDER PLACED SUCCESSFULLY
==================================================
Order ID:    987654321
Status:      NEW
Executed:    0
Avg Price:   N/A
==================================================
```

## Configuration

The bot uses environment variables for configuration:

| Variable | Description | Required |
|----------|-------------|----------|
| `BINANCE_API_KEY` | Your Binance API key | Yes |
| `BINANCE_API_SECRET` | Your Binance API secret | Yes |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No (default: INFO) |

## API Endpoints Used

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/fapi/v1/ping` | GET | Test connectivity |
| `/fapi/v1/time` | GET | Get server time |
| `/fapi/v2/account` | GET | Account information |
| `/fapi/v1/order` | POST | Place new order |
| `/fapi/v1/order` | GET | Query order status |
| `/fapi/v1/order` | DELETE | Cancel order |

Base URL: `https://testnet.binancefuture.com`

## Error Handling

The bot handles various error scenarios:

| Error Type | Example | Behavior |
|------------|---------|----------|
| Validation | Invalid symbol format | Immediate failure with clear message |
| API | Insufficient margin | Log error, no retry for -2010 codes |
| Network | Connection timeout | Retry up to 3 times with backoff |
| Rate Limit | Too many requests | Retry after delay |

## Bonus Features Implemented

1. **STOP_LIMIT Orders**: Full support for stop-loss and take-profit orders
2. **Interactive Mode**: Guided prompts for user-friendly order entry
3. **Retry Mechanism**: Automatic retry with exponential backoff for transient failures

## Development

### Running Tests (Future)

```bash
pip install pytest pytest-asyncio
pytest tests/
```

### Code Structure

- **client.py**: Handles HTTP requests, HMAC-SHA256 signing, and error handling
- **orders.py**: High-level order operations with validation and retry logic
- **validators.py**: Input validation for all trading parameters
- **logging_config.py**: Centralized logging configuration
- **cli.py**: Argument parsing and user interface
- **config.py**: Environment-based configuration management

## Troubleshooting

### "BINANCE_API_KEY environment variable is not set"

Ensure your `.env` file exists or environment variables are exported.

### "Account has insufficient balance"

Fund your testnet account at [Binance Testnet](https://testnet.binance.vision/).

### "Invalid API Key"

Verify you're using testnet credentials from testnet.binance.vision, not production.

### Network Timeout Errors

Check your internet connection. The retry mechanism will handle transient issues.

## License

MIT License - For educational and testing purposes only.

## Disclaimer

**WARNING**: This bot connects to the Binance Testnet only. Never use production API keys with this code until you thoroughly understand it. Cryptocurrency trading involves significant risk. This software is provided as-is for educational purposes.
