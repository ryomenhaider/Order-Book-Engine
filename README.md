# Order Book Engine

A high-performance order book implementation in Python with a beautiful terminal user interface (TUI).

## Features

- **Order Book Management**: Add, cancel, and match orders (bid/ask)
- **Price-Time Priority**: FIFO matching algorithm
- **Market Matching**: Execute market orders against opposite side of book
- **Depth Visualization**: View top N price levels with aggregated volumes
- **Beautiful TUI**: Interactive terminal interface with real-time updates

## Project Structure

```
orderbook_engine/
├── orderbook.py    # Core order book implementation
├── enums.py        # Side enum (BID/ASK)
├── tui.py          # Terminal user interface
└── README.md       # This file
```

## Installation

```bash
pip install -r requirements.txt
```

Required dependencies:
- `sortedcontainers` - For efficient sorted dictionaries
- `textual` - For the TUI framework

## Usage

### Run the TUI

```bash
python tui.py
```

### Use as a Library

```python
from orderbook import OrderBook, Data
from enums import Side
from decimal import Decimal

# Create order book
ob = OrderBook()

# Add orders
ob.add_order(Data(Decimal('100.50'), Side.BID, 100))
ob.add_order(Data(Decimal('101.00'), Side.ASK, 50))

# Get market depth
print(ob.get_depth(10))

# Match a market order
market_order = Data(Decimal('100.50'), Side.BID, 75)
ob.match(market_order)

# Cancel an order
ob.cancel_order(order.order_id)
```

## TUI Controls

- **BID** - Place a limit bid order
- **ASK** - Place a limit ask order  
- **MATCH** - Execute a market order
- Enter price and volume, then click a button

## API Reference

### OrderBook

| Method | Description |
|--------|-------------|
| `add_order(order)` | Add a limit order to the book |
| `cancel_order(order_id)` | Remove an order by ID |
| `match(order)` | Execute a market order (fills against opposite side) |
| `best_bid()` | Get highest bid price |
| `best_ask()` | Get lowest ask price |
| `bid_ask_spread()` | Get current spread |
| `get_depth(n)` | Get top N price levels with aggregated volumes |

### Data

| Property | Description |
|----------|-------------|
| `price` | Order price |
| `side` | BID or ASK |
| `volume` | Order quantity |
| `order_id` | Unique order identifier |
| `timestamps` | Order creation time |
