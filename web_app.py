"""Web Dashboard for Binance Trading Bot.

A Flask-based web interface for viewing account info, placing orders,
and monitoring trades in real-time.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, jsonify, request, flash, redirect
from flask_cors import CORS

from config import load_config
from bot.client import BinanceClient, BinanceAPIError
from bot.orders import OrderService, OrderResult
from bot.validators import ValidationError, validate_order_params
from bot.logging_config import setup_logging

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Setup logging
logger = setup_logging(log_level="INFO", log_dir=Path(__file__).parent / "logs")

# Global client cache
client_cache = {}


def get_client():
    """Get or create Binance client."""
    if 'client' not in client_cache:
        config = load_config()
        client_cache['client'] = BinanceClient(config, logger)
        client_cache['config'] = config
    return client_cache['client'], client_cache['config']


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/account')
def get_account():
    """Get account information."""
    async def fetch_account():
        client, config = get_client()
        try:
            account = await client.get_account_info()
            # Extract balances with non-zero amounts
            balances = [
                {
                    'asset': b['asset'],
                    'free': float(b['free']),
                    'locked': float(b['locked']),
                    'total': float(b['free']) + float(b['locked'])
                }
                for b in account.get('balances', [])
                if float(b['free']) > 0 or float(b['locked']) > 0
            ]
            return jsonify({
                'success': True,
                'balances': sorted(balances, key=lambda x: x['total'], reverse=True),
                'account_type': account.get('accountType', 'SPOT')
            })
        except BinanceAPIError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return asyncio.run(fetch_account())


@app.route('/api/price/<symbol>')
def get_price(symbol):
    """Get current price for a symbol."""
    async def fetch_price():
        client, config = get_client()
        try:
            # Use exchange info or ticker
            ticker = await client._make_request(
                "GET", 
                "/api/v3/ticker/price", 
                {"symbol": symbol.upper()}, 
                signed=False
            )
            return jsonify({
                'success': True,
                'symbol': ticker.get('symbol'),
                'price': float(ticker.get('price', 0))
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return asyncio.run(fetch_price())


@app.route('/api/order', methods=['POST'])
def place_order():
    """Place a new order."""
    async def do_order():
        data = request.json
        
        symbol = data.get('symbol', '').upper()
        side = data.get('side', '').upper()
        order_type = data.get('type', '').upper()
        quantity = float(data.get('quantity', 0))
        price = data.get('price')
        stop_price = data.get('stop_price')
        
        if price:
            price = float(price)
        if stop_price:
            stop_price = float(stop_price)
        
        try:
            # Validate
            validate_order_params(symbol, side, order_type, quantity, price, stop_price)
            
            # Place order
            client, config = get_client()
            order_service = OrderService(client, logger, max_retries=1)
            
            if order_type == 'MARKET':
                result = await order_service.market_order(symbol, side, quantity)
            elif order_type == 'LIMIT':
                result = await order_service.limit_order(symbol, side, quantity, price)
            elif order_type == 'STOP_LIMIT':
                result = await order_service.stop_limit_order(
                    symbol, side, quantity, price, stop_price
                )
            else:
                return jsonify({'success': False, 'error': f'Unsupported order type: {order_type}'}), 400
            
            if result.success:
                return jsonify({
                    'success': True,
                    'order_id': result.order_id,
                    'status': result.status,
                    'executed_qty': result.executed_qty,
                    'avg_price': result.avg_price,
                    'message': 'Order placed successfully'
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': result.error or 'Unknown error'
                }), 400
                
        except ValidationError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        except BinanceAPIError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return asyncio.run(do_order())


@app.route('/api/orders/open')
def get_open_orders():
    """Get all open orders."""
    async def fetch_orders():
        client, config = get_client()
        try:
            orders = await client._make_request("GET", "/api/v3/openOrders", {})
            formatted_orders = [
                {
                    'order_id': o['orderId'],
                    'symbol': o['symbol'],
                    'side': o['side'],
                    'type': o['type'],
                    'price': float(o.get('price', 0)),
                    'quantity': float(o['origQty']),
                    'executed': float(o['executedQty']),
                    'status': o['status'],
                    'time': datetime.fromtimestamp(o['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                }
                for o in orders
            ]
            return jsonify({'success': True, 'orders': formatted_orders})
        except BinanceAPIError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return asyncio.run(fetch_orders())


@app.route('/api/orders/all')
def get_all_orders():
    """Get recent orders for a symbol."""
    async def fetch_orders():
        client, config = get_client()
        symbol = request.args.get('symbol', 'BTCUSDT').upper()
        try:
            orders = await client._make_request(
                "GET", 
                "/api/v3/allOrders", 
                {"symbol": symbol, "limit": 20}
            )
            formatted_orders = [
                {
                    'order_id': o['orderId'],
                    'symbol': o['symbol'],
                    'side': o['side'],
                    'type': o['type'],
                    'price': float(o.get('price', 0)) or float(o.get('stopPrice', 0)),
                    'quantity': float(o['origQty']),
                    'executed': float(o['executedQty']),
                    'status': o['status'],
                    'time': datetime.fromtimestamp(o['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                }
                for o in orders
            ]
            return jsonify({'success': True, 'orders': formatted_orders})
        except BinanceAPIError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return asyncio.run(fetch_orders())


@app.route('/api/cancel', methods=['POST'])
def cancel_order():
    """Cancel an order."""
    async def do_cancel():
        data = request.json
        symbol = data.get('symbol', '').upper()
        order_id = data.get('order_id')
        
        if not symbol or not order_id:
            return jsonify({'success': False, 'error': 'Missing symbol or order_id'}), 400
        
        client, config = get_client()
        try:
            result = await client.cancel_order(symbol, int(order_id))
            return jsonify({
                'success': True,
                'order_id': result.get('orderId'),
                'status': 'CANCELLED'
            })
        except BinanceAPIError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
    
    return asyncio.run(do_cancel())


if __name__ == '__main__':
    print("="*60)
    print("  Binance Trading Bot - Web Dashboard")
    print("="*60)
    print("\nOpen your browser and go to:")
    print("  http://localhost:5000")
    print("\nPress CTRL+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
