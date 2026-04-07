from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.reactive import reactive
from textual import work
import random
import asyncio

from orderbook import OrderBook, Data
from enums import Side
from decimal import Decimal


class OrderBookWidget(Widget):
    book = reactive(OrderBook())
    depth = reactive(10)

    def __init__(self):
        super().__init__()
        self.orderbook = OrderBook()
        self.trades = []

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("🟢 BIDS", classes="title bid-title"),
            Static("", id="bids-display"),
            Static("─" * 40, classes="spread-line"),
            Static("", id="spread-display"),
            Static("─" * 40, classes="spread-line"),
            Static("🔴 ASKS", classes="title ask-title"),
            Static("", id="asks-display"),
            id="orderbook-panel",
        )

    def watch_book(self):
        self.refresh_display()

    def refresh_display(self):
        depth = self.orderbook.get_depth(self.depth)

        bids_text = ""
        for price, vol in depth["bids"]:
            bar_width = min(int(vol / 100), 30)
            bar = "█" * bar_width
            bids_text += f"{price:>10.2f} │ {vol:>6} │ {bar}\n"

        asks_text = ""
        for price, vol in depth["asks"]:
            bar_width = min(int(vol / 100), 30)
            bar = "█" * bar_width
            asks_text += f"{price:>10.2f} │ {vol:>6} │ {bar}\n"

        spread = self.orderbook.bid_ask_spread()
        spread_text = (
            f"Spread: {float(spread) if spread else 'N/A':.2f}"
            if spread
            else "No spread"
        )

        self.query_one("#bids-display", Static).update(bids_text or "No bids")
        self.query_one("#asks-display", Static).update(asks_text or "No asks")
        self.query_one("#spread-display", Static).update(spread_text)

    def add_bid(self, price: float, volume: int):
        order = Data(Decimal(str(price)), Side.BID, volume)
        self.orderbook.add_order(order)
        self.refresh_display()

    def add_ask(self, price: float, volume: int):
        order = Data(Decimal(str(price)), Side.ASK, volume)
        self.orderbook.add_order(order)
        self.refresh_display()

    def add_market_order(self, side: Side, volume: int, base_price: float = 100.0):
        if side == Side.BID:
            price = Decimal(str(base_price + random.uniform(0, 2)))
        else:
            price = Decimal(str(base_price - random.uniform(0, 2)))
        order = Data(price, side, volume)
        self.orderbook.match(order)
        self.refresh_display()


class TickerWidget(Widget):
    def compose(self) -> ComposeResult:
        yield Horizontal(
            Static("BTC/USD", classes="ticker-symbol"),
            Static("$99,450.00", classes="ticker-price"),
            Static("▲ 2.34%", classes="ticker-change"),
            id="ticker-bar",
        )


class OrderPanel(Widget):
    def __init__(self, book_widget: OrderBookWidget):
        super().__init__()
        self.book_widget = book_widget

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("📝 PLACE ORDER", classes="panel-title"),
            Horizontal(
                Button("BID", variant="success", id="bid-btn"),
                Button("ASK", variant="danger", id="ask-btn"),
                Button("MATCH", variant="warning", id="match-btn"),
            ),
            Horizontal(
                Input(placeholder="Price", id="price-input"),
                Input(placeholder="Volume", id="volume-input"),
            ),
            id="order-panel",
        )


class OrderBookTUI(App):
    CSS = """
    Screen {
        background: $surface;
    }
    
    # main-container {
        height: 100%;
        layout: horizontal;
    }
    
    # left-panel {
        width: 60%;
        border: solid $primary;
        padding: 1;
    }
    
    # right-panel {
        width: 40%;
        border: solid $accent;
        padding: 1;
    }
    
    # orderbook-panel {
        height: 100%;
        background: $panel;
        border: solid $primary;
        padding: 1;
    }
    
    .title {
        text-align: center;
        text-style: bold;
        padding: 1;
    }
    
    .bid-title {
        color: $success;
    }
    
    .ask-title {
        color: $error;
    }
    
    #bids-display, #asks-display {
        font: monospace;
        color: $text;
        text-align: left;
    }
    
    .spread-line {
        color: $text-muted;
        text-align: center;
    }
    
    #ticker-bar {
        height: 3;
        background: $primary-darken-1;
        align: center middle;
    }
    
    .ticker-symbol {
        text-style: bold;
        color: $text;
        width: 10;
    }
    
    .ticker-price {
        text-style: bold;
        color: $success;
        width: 15;
    }
    
    .ticker-change {
        color: $success;
        width: 12;
    }
    
    # order-panel {
        height: 100%;
        background: $panel;
    }
    
    .panel-title {
        text-style: bold;
        text-align: center;
        color: $text;
        padding: 1;
    }
    
    # order-panel Horizontal {
        height: auto;
        margin: 1 0;
    }
    
    Input {
        margin: 1;
    }
    
    Button {
        margin: 1;
    }
    
    #trade-log {
        height: 100%;
        background: $panel;
        border: solid $accent;
        padding: 1;
    }
    
    .trade-title {
        text-style: bold;
        text-align: center;
        color: $text;
        padding: 1;
    }
    
    # trades-display {
        font: monospace;
    }
    """

    def __init__(self):
        super().__init__()
        self.book_widget = OrderBookWidget()
        self.trade_history = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Container(
            Vertical(TickerWidget(), self.book_widget, id="left-panel"),
            Vertical(
                OrderPanel(self.book_widget),
                Vertical(
                    Static("📜 TRADE HISTORY", classes="trade-title"),
                    Static("", id="trades-display"),
                    id="trade-log",
                ),
                id="right-panel",
            ),
            id="main-container",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.simulate_market()

    @work(exclusive=True)
    async def simulate_market(self):
        base_price = 100.0
        for _ in range(20):
            price = base_price + random.uniform(-5, 5)
            volume = random.randint(50, 500)

            if random.random() < 0.5:
                self.book_widget.add_bid(price, volume)
            else:
                self.book_widget.add_ask(price, volume)

            await asyncio.sleep(0.1)

        for _ in range(5):
            volume = random.randint(100, 300)
            side = random.choice([Side.BID, Side.ASK])
            self.book_widget.add_market_order(side, volume, base_price)
            await asyncio.sleep(0.2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        price_input = self.query_one("#price-input", Input)
        volume_input = self.query_one("#volume-input", Input)

        try:
            price = float(price_input.value) if price_input.value else 100.0
            volume = int(volume_input.value) if volume_input.value else 100
        except ValueError:
            return

        if event.button.id == "bid-btn":
            self.book_widget.add_bid(price, volume)
            self.add_trade("BID", price, volume)
        elif event.button.id == "ask-btn":
            self.book_widget.add_ask(price, volume)
            self.add_trade("ASK", price, volume)
        elif event.button.id == "match-btn":
            self.book_widget.add_market_order(Side.BID, volume, price)
            self.book_widget.add_market_order(Side.ASK, volume, price)
            self.add_trade("MATCH", price, volume)

        price_input.value = ""
        volume_input.value = ""

    def add_trade(self, side: str, price: float, volume: int):
        self.trade_history.insert(0, f"{side:5} │ {price:>8.2f} │ {volume:>5}")
        if len(self.trade_history) > 10:
            self.trade_history = self.trade_history[:10]

        trades_text = "\n".join(self.trade_history)
        self.query_one("#trades-display", Static).update(trades_text)


if __name__ == "__main__":
    app = OrderBookTUI()
    app.run()
