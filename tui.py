from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input, Button
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding
import threading
import random

from orderbook import OrderBook, Data
from enums import Side
from decimal import Decimal


class OrderBookTUI(App):
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main {
        layout: grid;
        grid-size: 2;
    }
    
    #left-panel {
        width: 100%;
        height: 100%;
    }
    
    #right-panel {
        width: 100%;
        height: 100%;
    }
    
    #orderbook-container {
        height: 100%;
        background: $panel;
    }
    
    .header-row {
        text-style: bold;
        text-align: center;
    }
    
    .bid-header {
        color: $success;
    }
    
    .ask-header {
        color: $error;
    }
    
    #bids-list, #asks-list {
        height: 100%;
    }
    
    .row {
        width: 100%;
    }
    
    .bid-row {
        color: $success;
    }
    
    .ask-row {
        color: $error;
    }
    
    .spread-row {
        text-align: center;
        color: $text-muted;
    }
    
    #form-container {
        height: auto;
        background: $panel;
        border: solid $primary;
        padding: 1;
    }
    
    #order-form {
        width: 100%;
    }
    
    .form-label {
        width: 20;
        text-style: bold;
    }
    
    Input {
        width: 100%;
    }
    
    .btn-row {
        height: auto;
    }
    
    #trade-log {
        height: 100%;
        background: $panel;
    }
    
    .log-header {
        text-style: bold;
        text-align: center;
        color: $accent;
    }
    
    #log-content {
    }
    
    .ticker {
        text-style: bold;
        background: $primary-darken-1;
    }
    
    .ticker-symbol {
        color: $text;
    }
    
    .ticker-price {
        color: $success;
    }
    
    .ticker-change {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("b", "add_bid", "Bid"),
        Binding("a", "add_ask", "Ask"),
    ]

    def __init__(self):
        super().__init__()
        self.orderbook = OrderBook()
        self.trades = []
        self._running = True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="main"):
            with Vertical(id="left-panel"):
                yield Horizontal(
                    Static("BTC/USD", classes="ticker-symbol"),
                    Static("$100.00", classes="ticker-price"),
                    Static("+0.00%", classes="ticker-change"),
                    classes="ticker",
                    id="ticker-bar",
                )

                with Vertical(id="orderbook-container"):
                    yield Static("BIDS", classes="header-row bid-header")
                    yield Static("", id="bids-display")
                    yield Static("─" * 50, classes="spread-row")
                    yield Static("", id="spread-display")
                    yield Static("─" * 50, classes="spread-row")
                    yield Static("ASKS", classes="header-row ask-header")
                    yield Static("", id="asks-display")

            with Vertical(id="right-panel"):
                with Vertical(id="form-container"):
                    yield Static("PLACE ORDER", classes="header-row")
                    yield Horizontal(
                        Static("Side:", classes="form-label"),
                        Input(placeholder="BID/ASK", id="side-input"),
                        id="side-row",
                    )
                    yield Horizontal(
                        Static("Price:", classes="form-label"),
                        Input(placeholder="100.00", id="price-input"),
                        id="price-row",
                    )
                    yield Horizontal(
                        Static("Volume:", classes="form-label"),
                        Input(placeholder="100", id="volume-input"),
                        id="volume-row",
                    )
                    yield Horizontal(
                        Button("Submit Order", variant="primary", id="submit-btn"),
                        Button("Cancel", variant="default", id="cancel-btn"),
                        classes="btn-row",
                    )
                    yield Static(
                        "Press B for BID, A for ASK, ENTER to submit",
                        classes="log-header",
                    )

                with Vertical(id="trade-log"):
                    yield Static("RECENT TRADES", classes="log-header")
                    yield Static("", id="log-content")

        yield Footer()

    def on_mount(self) -> None:
        self.populate_mock_data()
        self.refresh_orderbook()

    def populate_mock_data(self):
        base = 100.0
        for _ in range(15):
            price = base + random.uniform(-3, 3)
            volume = random.randint(50, 500)
            side = random.choice([Side.BID, Side.ASK])
            order = Data(Decimal(str(price)), side, volume)
            self.orderbook.add_order(order)

    def refresh_orderbook(self):
        depth = self.orderbook.get_depth(12)

        bids_text = ""
        for price, vol in depth["bids"]:
            pct = int((vol / 1000) * 20)
            bar = "█" * pct
            bids_text += f"{price:>10.2f}  {vol:>5}  {bar}\n"

        asks_text = ""
        for price, vol in depth["asks"]:
            pct = int((vol / 1000) * 20)
            bar = "█" * pct
            asks_text += f"{price:>10.2f}  {vol:>5}  {bar}\n"

        spread = self.orderbook.bid_ask_spread()
        spread_str = f"Spread: {float(spread):.2f}" if spread else "No spread"

        self.query_one("#bids-display", Static).update(bids_text or "No orders")
        self.query_one("#asks-display", Static).update(asks_text or "No orders")
        self.query_one("#spread-display", Static).update(spread_str)

    def add_order_from_form(self):
        side_input = self.query_one("#side-input", Input)
        price_input = self.query_one("#price-input", Input)
        volume_input = self.query_one("#volume-input", Input)

        try:
            side_str = side_input.value.upper().strip()
            price = float(price_input.value) if price_input.value else 100.0
            volume = int(volume_input.value) if volume_input.value else 100

            if side_str not in ["BID", "ASK", "B", "A"]:
                return

            side = Side.BID if side_str in ["BID", "B"] else Side.ASK

            order = Data(Decimal(str(price)), side, volume)
            self.orderbook.match(order)

            self.refresh_orderbook()
            self.add_trade_log(side, price, volume)

            side_input.value = ""
            price_input.value = ""
            volume_input.value = ""

        except (ValueError, Exception):
            pass

    def add_trade_log(self, side: Side, price: float, volume: int):
        side_str = "BID" if side == Side.BID else "ASK"
        self.trades.insert(0, f"{side_str:4}  {price:>8.2f}  {volume:>5}")
        if len(self.trades) > 15:
            self.trades = self.trades[:15]

        self.query_one("#log-content", Static).update("\n".join(self.trades))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-btn":
            self.add_order_from_form()
        elif event.button.id == "cancel-btn":
            self.query_one("#side-input", Input).value = ""
            self.query_one("#price-input", Input).value = ""
            self.query_one("#volume-input", Input).value = ""

    def action_add_bid(self):
        self.query_one("#side-input", Input).value = "BID"
        self.query_one("#price-input", Input).focus()

    def action_add_ask(self):
        self.query_one("#side-input", Input).value = "ASK"
        self.query_one("#price-input", Input).focus()

    def action_quit(self):
        self._running = False
        self.exit()


if __name__ == "__main__":
    app = OrderBookTUI()
    app.run()
