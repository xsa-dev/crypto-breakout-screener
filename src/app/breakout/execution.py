"""Fake execution adapter for deterministic breakout contract tests."""

from src.core.models import ExecutionOrder, ExecutionRequest, ExecutionSnapshot, PositionState


class FakeExecutionAdapter:
    """In-memory idempotent execution adapter with no live side effects."""

    def __init__(self) -> None:
        self.orders: dict[str, ExecutionOrder] = {}
        self._request_to_order: dict[str, str] = {}

    def submit_order(self, request: ExecutionRequest) -> ExecutionOrder:
        """Record an order request once and return existing result for duplicate IDs."""

        existing_order_id = self._request_to_order.get(request.request_id)
        if existing_order_id is not None:
            return self.orders[existing_order_id]

        order_id = f"fake-{len(self.orders) + 1}"
        order = ExecutionOrder(
            order_id=order_id,
            request_id=request.request_id,
            intent_id=request.intent_id,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
        )
        self.orders[order_id] = order
        self._request_to_order[request.request_id] = order_id
        return order

    def simulate_fill(self, order_id: str, *, fill_price: float, quantity: float | None = None) -> ExecutionOrder:
        """Simulate deterministic fill for an accepted fake order."""

        order = self.orders[order_id]
        fill_quantity = order.quantity if quantity is None else min(quantity, order.quantity)
        status = "filled" if fill_quantity >= order.quantity else "partially_filled"
        updated = order.model_copy(
            update={"filled_quantity": fill_quantity, "fill_price": fill_price, "status": status}
        )
        self.orders[order_id] = updated
        return updated

    def cancel_order(self, order_id: str) -> ExecutionOrder:
        """Cancel open fake orders, rejecting cancellation for already-filled orders."""

        order = self.orders[order_id]
        if order.status == "filled":
            updated = order.model_copy(update={"status": "cancel_rejected_filled"})
        else:
            updated = order.model_copy(update={"status": "cancelled"})
        self.orders[order_id] = updated
        return updated

    def modify_order(self, order_id: str, *, price: float | None = None, quantity: float | None = None) -> ExecutionOrder:
        """Modify an open fake order."""

        order = self.orders[order_id]
        if order.status in {"filled", "cancelled"}:
            return order.model_copy(update={"status": f"modify_rejected_{order.status}"})
        updated = order.model_copy(
            update={
                "price": order.price if price is None else price,
                "quantity": order.quantity if quantity is None else quantity,
                "status": "modified",
            }
        )
        self.orders[order_id] = updated
        return updated

    def reconcile(self) -> ExecutionSnapshot:
        """Build a deterministic local order/position snapshot from filled fake orders."""

        positions: dict[str, PositionState] = {}
        for order in self.orders.values():
            if order.filled_quantity <= 0 or order.fill_price is None:
                continue
            current = positions.get(order.symbol)
            if current is None:
                positions[order.symbol] = PositionState(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.filled_quantity,
                    average_price=order.fill_price,
                )
                continue
            signed_quantity = order.filled_quantity if order.side is current.side else -order.filled_quantity
            new_quantity = current.quantity + signed_quantity
            if new_quantity <= 0:
                positions.pop(order.symbol)
                continue
            if order.side is current.side:
                average = (
                    current.average_price * current.quantity + order.fill_price * order.filled_quantity
                ) / new_quantity
            else:
                average = current.average_price
            positions[order.symbol] = current.model_copy(
                update={"quantity": new_quantity, "average_price": average}
            )
        return ExecutionSnapshot(orders=dict(self.orders), positions=positions)

    def query_order(self, order_id: str) -> ExecutionOrder:
        return self.orders[order_id]

    def query_position(self, symbol: str) -> PositionState | None:
        return self.reconcile().positions.get(symbol)
