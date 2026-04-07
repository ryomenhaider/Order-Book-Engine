import uuid
from decimal import Decimal
from datetime import datetime
from enums import Side
from dataclasses import dataclass, field
from sortedcontainers import SortedDict
from collections import deque

@dataclass
class Data:
    price: Decimal
    volume: int
    side: Side
    timestamps: datetime = field(default_factory=datetime.now)
    order_id: uuid.UUID = field(default_factory=uuid.uuid4)

    def __eq__(self, other):
        if not isinstance(other, Data):
            return NotImplemented
        return self.order_id == other.order_id

    def __hash__(self):
        return hash(self.order_id)

    
class OrderBook:
    def __init__(self):
        self.bid    = SortedDict(lambda neg: -neg) 
        self.ask    = SortedDict() 
        self.orders = {}

    def add_order(self, order: Data):
        if order.volume <= 0:
            raise ValueError('volume cannot be 0 or less')
        
        self.orders[order.order_id] = order
        book_side = self.bid if order.side == Side.BID else self.ask
        
        if order.price not in book_side:
            book_side[order.price] = deque()
        book_side[order.price].append(order)

    def cancel_order(self, order_id: uuid.UUID):
        order = self.orders.get(order_id)
        if order is None:
            return
        
        side = order.side
        price = order.price
        del self.orders[order_id]

        book = self.bid if side == Side.BID else self.ask
        
        if price in book:
            try:
                book[price].remove(order)
            except ValueError:  
                pass
                
            if not book[price]:
                del book[price]
    
    def best_ask(self):
        if not self.ask: return None
        return self.ask.iloc[0]
    
    def best_bid(self):
        if not self.bid: return None
        return self.bid.iloc[0]
    
    def bid_ask_spread(self):
        if not self.ask or not self.bid:
            return None
        
        return self.best_ask() - self.best_bid()
    
    def match(self, order: Data):
        if order.side == Side.ASK:
            while order.volume > 0 and self.bid and order.price <= self.best_bid():
                best_bid_price = self.best_bid()
                order_queue = self.bid[best_bid_price]
                maker_order = order_queue[0]

                match_volume = min(order.volume, maker_order.volume)
                order.volume -= match_volume
                maker_order.volume -= match_volume

                if maker_order.volume == 0:
                    order_queue.popleft()
                    del self.orders[maker_order.order_id]
                    if not order_queue:
                        del self.bid[best_bid_price]

        elif order.side == Side.BID:
            while order.volume > 0 and self.ask and order.price >= self.best_ask():
                best_ask_price = self.best_ask()
                order_queue = self.ask[best_ask_price]
                maker_order = order_queue[0]

                match_volume = min(order.volume, maker_order.volume)
                order.volume -= match_volume
                maker_order.volume -= match_volume

                if maker_order.volume == 0:
                    order_queue.popleft()
                    del self.orders[maker_order.order_id]
                    if not order_queue:
                        del self.ask[best_ask_price]
        
        if order.volume > 0:
            self.add_order(order)
