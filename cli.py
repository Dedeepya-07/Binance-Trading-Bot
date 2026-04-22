#!/usr/bin/env python3
"""Command-line interface for the Binance Futures Trading Bot.

Provides a user-friendly CLI for placing orders on Binance Futures Testnet.
"""

import argparse
import asyncio
import sys
from typing import Optional

from config import load_config, validate_credentials
from bot.client import BinanceClient, BinanceAPIError
from bot.orders import OrderService
from bot.validators import ValidationError
from bot.logging_config import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Place a MARKET BUY order
  python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

  # Place a LIMIT SELL order
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 0.1 --price 3000

  # Place a STOP-LIMIT order (stop-loss)
  python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.01 --price 59000 --stop-price 60000

  # Interactive mode
  python cli.py --interactive
        """
    )
    
    parser.add_argument(
        "--symbol",
        type=str,
        help="Trading pair symbol (e.g., BTCUSDT, ETHUSDT)"
    )
    
    parser.add_argument(
        "--side",
        type=str,
        choices=["BUY", "SELL"],
        help="Order side: BUY or SELL"
    )
    
    parser.add_argument(
        "--type",
        dest="order_type",
        type=str,
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
        help="Order type: MARKET, LIMIT, or STOP_LIMIT"
    )
    
    parser.add_argument(
        "--quantity",
        type=float,
        help="Order quantity (e.g., 0.01 for BTC)"
    )
    
    parser.add_argument(
        "--price",
        type=float,
        default=None,
        help="Limit price (required for LIMIT and STOP_LIMIT orders)"
    )
    
    parser.add_argument(
        "--stop-price",
        type=float,
        default=None,
        help="Stop price (required for STOP_LIMIT orders)"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode with prompts"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose/debug logging"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test connection without placing order"
    )
    
    return parser


def prompt_symbol() -> str:
    """Interactive prompt for symbol input.
    
    Returns:
        Validated symbol string
    """
    while True:
        symbol = input("Enter trading symbol (e.g., BTCUSDT): ").strip().upper()
        if symbol:
            return symbol
        print("Symbol cannot be empty. Please try again.")


def prompt_side() -> str:
    """Interactive prompt for side input.
    
    Returns:
        Validated side string (BUY or SELL)
    """
    while True:
        side = input("Enter side (BUY/SELL): ").strip().upper()
        if side in ["BUY", "SELL"]:
            return side
        print("Invalid side. Please enter BUY or SELL.")


def prompt_order_type() -> str:
    """Interactive prompt for order type input.
    
    Returns:
        Validated order type string
    """
    while True:
        order_type = input("Enter order type (MARKET/LIMIT/STOP_LIMIT): ").strip().upper()
        if order_type in ["MARKET", "LIMIT", "STOP_LIMIT"]:
            return order_type
        print("Invalid order type. Please enter MARKET, LIMIT, or STOP_LIMIT.")


def prompt_quantity() -> float:
    """Interactive prompt for quantity input.
    
    Returns:
        Validated quantity as float
    """
    while True:
        try:
            qty = float(input("Enter quantity: ").strip())
            if qty > 0:
                return qty
            print("Quantity must be greater than 0.")
        except ValueError:
            print("Invalid quantity. Please enter a valid number.")


def prompt_price(order_type: str) -> Optional[float]:
    """Interactive prompt for price input.
    
    Args:
        order_type: Type of order being placed
    
    Returns:
        Price as float, or None for MARKET orders
    """
    if order_type == "MARKET":
        return None
    
    while True:
        try:
            price = float(input("Enter limit price: ").strip())
            if price > 0:
                return price
            print("Price must be greater than 0.")
        except ValueError:
            print("Invalid price. Please enter a valid number.")


def prompt_stop_price() -> float:
    """Interactive prompt for stop price input.
    
    Returns:
        Stop price as float
    """
    while True:
        try:
            stop_price = float(input("Enter stop price: ").strip())
            if stop_price > 0:
                return stop_price
            print("Stop price must be greater than 0.")
        except ValueError:
            print("Invalid stop price. Please enter a valid number.")


def interactive_mode() -> dict:
    """Run interactive mode to collect order parameters.
    
    Returns:
        Dictionary with order parameters
    """
    print("\n" + "="*50)
    print("  Binance Futures Trading Bot - Interactive Mode")
    print("="*50 + "\n")
    
    params = {}
    params["symbol"] = prompt_symbol()
    params["side"] = prompt_side()
    params["order_type"] = prompt_order_type()
    params["quantity"] = prompt_quantity()
    params["price"] = prompt_price(params["order_type"])
    
    if params["order_type"] == "STOP_LIMIT":
        params["stop_price"] = prompt_stop_price()
    
    # Confirm order
    print("\n" + "-"*50)
    print("ORDER SUMMARY:")
    print(f"  Symbol:   {params['symbol']}")
    print(f"  Side:     {params['side']}")
    print(f"  Type:     {params['order_type']}")
    print(f"  Quantity: {params['quantity']}")
    if params["price"]:
        print(f"  Price:    {params['price']}")
    if params.get("stop_price"):
        print(f"  Stop:     {params['stop_price']}")
    print("-"*50)
    
    confirm = input("\nConfirm order? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("Order cancelled.")
        return None
    
    return params


def print_header():
    """Print application header."""
    print("\n" + "="*50)
    print("  Binance Futures Testnet Trading Bot")
    print("="*50 + "\n")


def print_summary(args):
    """Print order request summary.
    
    Args:
        args: Parsed arguments
    """
    print("\nORDER REQUEST SUMMARY:")
    print(f"  Symbol:   {args.symbol}")
    print(f"  Side:     {args.side}")
    print(f"  Type:     {args.order_type}")
    print(f"  Quantity: {args.quantity}")
    if args.price:
        print(f"  Price:    {args.price}")
    if args.stop_price:
        print(f"  Stop:     {args.stop_price}")
    print()


async def main():
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    print_header()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logging(log_level=log_level)
    
    # Load configuration
    try:
        config = load_config()
        if not validate_credentials(config):
            print("Error: Invalid API credentials configuration.")
            sys.exit(1)
        logger.info("Configuration loaded successfully")
    except ValueError as e:
        print(f"Configuration Error: {e}")
        print("\nPlease set the following environment variables:")
        print("  export BINANCE_API_KEY='your_api_key'")
        print("  export BINANCE_API_SECRET='your_api_secret'")
        sys.exit(1)
    
    # Handle interactive mode
    if args.interactive:
        params = interactive_mode()
        if params is None:
            sys.exit(0)
        args.symbol = params["symbol"]
        args.side = params["side"]
        args.order_type = params["order_type"]
        args.quantity = params["quantity"]
        args.price = params.get("price")
        args.stop_price = params.get("stop_price")
    elif not args.test and not all([args.symbol, args.side, args.order_type, args.quantity]):
        parser.print_help()
        print("\nError: Missing required arguments.")
        print("Use --interactive mode or provide all required arguments.")
        sys.exit(1)
    
    # Initialize client and service
    client = BinanceClient(config, logger)
    order_service = OrderService(client, logger, max_retries=3)
    
    try:
        # Test connection if requested
        if args.test:
            print("Testing connection to Binance Futures Testnet...")
            server_time = await client.get_server_time()
            print(f"✅ Connection successful! Server time: {server_time.get('serverTime')}")
            
            account_info = await client.get_account_info()
            print(f"✅ Account connected. Available balance: {account_info.get('availableBalance', 'N/A')} USDT")
            sys.exit(0)
        
        # Print summary
        print_summary(args)
        
        # Place order based on type
        if args.order_type == "MARKET":
            result = await order_service.market_order(
                symbol=args.symbol,
                side=args.side,
                quantity=args.quantity
            )
        elif args.order_type == "LIMIT":
            if args.price is None:
                print("Error: --price is required for LIMIT orders")
                sys.exit(1)
            result = await order_service.limit_order(
                symbol=args.symbol,
                side=args.side,
                quantity=args.quantity,
                price=args.price
            )
        elif args.order_type == "STOP_LIMIT":
            if args.price is None or args.stop_price is None:
                print("Error: --price and --stop-price are required for STOP_LIMIT orders")
                sys.exit(1)
            result = await order_service.stop_limit_order(
                symbol=args.symbol,
                side=args.side,
                quantity=args.quantity,
                price=args.price,
                stop_price=args.stop_price
            )
        
        # Exit with appropriate code
        if result.success:
            logger.info("Order completed successfully")
            sys.exit(0)
        else:
            logger.error(f"Order failed: {result.error}")
            sys.exit(1)
            
    except ValidationError as e:
        print(f"\nValidation Error: {e}")
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except BinanceAPIError as e:
        print(f"\nAPI Error: {e}")
        logger.error(f"API error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        logger.exception("Unexpected error")
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
