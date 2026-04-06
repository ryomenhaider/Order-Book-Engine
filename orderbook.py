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

    def add_order(self):
        self.orders[Data.order_id] = {
            'order_id': Data.order_id ,
            'price': Data.price, 
            'volume': Data.volume, 
            'side': Data.side, 
            'timestamps': Data.timestamps
        }

        if Data.price not in self.orders:
            self.orders[Data.price] = deque()
            self.orders[Data.price].append(self.orders)
