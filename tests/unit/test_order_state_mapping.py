from triggertrade.execution import OrderStatus
from triggertrade.execution.bybit import map_bybit_order_status


def test_bybit_state_mapping():
    assert map_bybit_order_status("New") is OrderStatus.SUBMITTED
    assert map_bybit_order_status("PartiallyFilled") is OrderStatus.PARTIALLY_FILLED
    assert map_bybit_order_status("Filled") is OrderStatus.FILLED
    assert map_bybit_order_status("Cancelled") is OrderStatus.CANCELLED
    assert map_bybit_order_status("Rejected") is OrderStatus.REJECTED
    assert map_bybit_order_status("SomethingNew") is OrderStatus.UNKNOWN
