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
        

        if order_id in self.orders:
            self.orders.pop(order_id, None)

            side = self.orders['side']
            if side == Side.BID:
                self.bid.pop(order_id, None)
            elif side == Side.ASK:
                self.ask.pop(order_id, None)
            
        if not Data.price:
                del Data.price