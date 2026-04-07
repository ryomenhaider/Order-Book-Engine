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

class OrderBook:
    def __init__(self):
        self.bid    = SortedDict(lambda neg: -neg)
        self.ask    = SortedDict()
        self.orders = {}

    def add_order(self, order: Data):
        
        if order.volume <= 0:
            raise ValueError('volume cannont be 0 or less')
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

        book = self.ask if side == Side.ASK else self.bid
        
        if price in book:
            try:
                book[price].remove(order)
            except ValueError:  
                pass
                
            if not book[price]:
                del book[price]