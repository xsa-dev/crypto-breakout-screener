"""Entry-intent generation and finite state machine for breakout lifecycle."""

from datetime import UTC, datetime

from src.core.enums import EntryMode, FsmState, Side
from src.core.models import (
    BreakoutScore,
    BreakoutStrategyConfig,
    ExitPlan,
    LifecycleTransition,
    MarketSnapshot,
    TradeIntent,
)


class EntryEngine:
    """Creates deterministic broker-neutral entry intents."""

    def __init__(self, config: BreakoutStrategyConfig | None = None) -> None:
        self.config = config or BreakoutStrategyConfig()

    def generate_intents(
        self,
        *,
        score: BreakoutScore,
        side: Side,
        level_price: float,
        base_quantity: float,
        stop_price: float,
        market: MarketSnapshot,
        pre_entry_ready: bool = False,
        at_level_ready: bool = False,
        lower_protorgovka_ready: bool = False,
    ) -> list[TradeIntent]:
        """Generate entry intents capped by configured base-position shares."""

        if base_quantity <= 0 or score.eligibility == "blocked":
            return []

        intents: list[TradeIntent] = []
        if (
            lower_protorgovka_ready
            and self.config.entries.lower_protorgovka_entry_enabled
            and side is Side.LONG
        ):
            intents.append(
                self._intent(
                    mode=EntryMode.PRE_ENTRY,
                    share=self.config.entries.pre_entry_share,
                    score=score,
                    side=side,
                    level_price=level_price,
                    base_quantity=base_quantity,
                    entry_price=market.price,
                    stop_price=stop_price,
                    reason="lower_protorgovka_ready",
                    entry_subtype="lower_protorgovka_boundary",
                )
            )
        if pre_entry_ready:
            intents.append(
                self._intent(
                    mode=EntryMode.PRE_ENTRY,
                    share=self.config.entries.pre_entry_share,
                    score=score,
                    side=side,
                    level_price=level_price,
                    base_quantity=base_quantity,
                    entry_price=market.price,
                    stop_price=stop_price,
                    reason="pre_entry_ready",
                )
            )
        if at_level_ready:
            intents.append(
                self._intent(
                    mode=EntryMode.AT_LEVEL,
                    share=self.config.entries.at_level_share,
                    score=score,
                    side=side,
                    level_price=level_price,
                    base_quantity=base_quantity,
                    entry_price=market.price,
                    stop_price=stop_price,
                    reason="at_level_ready",
                )
            )
        if self.confirm_breakout(score=score, side=side, level_price=level_price, market=market):
            intents.append(
                self._intent(
                    mode=EntryMode.POST_BREAKOUT,
                    share=self.config.entries.post_breakout_share,
                    score=score,
                    side=side,
                    level_price=level_price,
                    base_quantity=base_quantity,
                    entry_price=market.close,
                    stop_price=stop_price,
                    reason="breakout_confirmed",
                )
            )

        return self._cap_total_quantity(intents, base_quantity)

    def confirm_breakout(
        self,
        *,
        score: BreakoutScore,
        side: Side,
        level_price: float,
        market: MarketSnapshot,
    ) -> bool:
        """Confirm breakout using side-symmetric level plus configured buffer logic."""

        if score.eligibility == "blocked":
            return False
        buffer = self.config.entries.breakout_buffer_atr
        if side is Side.LONG:
            return market.close > level_price + buffer
        return market.close < level_price - buffer

    def _intent(
        self,
        *,
        mode: EntryMode,
        share: float,
        score: BreakoutScore,
        side: Side,
        level_price: float,
        base_quantity: float,
        entry_price: float,
        stop_price: float,
        reason: str,
        entry_subtype: str | None = None,
    ) -> TradeIntent:
        metadata: dict[str, float | int | str | bool] = {
            "share": share,
            "level_price": level_price,
            "reason": reason,
        }
        if entry_subtype is not None:
            metadata["entry_subtype"] = entry_subtype
        return TradeIntent(
            intent_id=f"{score.symbol}:{mode.value}:{len(reason)}",
            symbol=score.symbol,
            side=side,
            mode=mode,
            entry_price=entry_price,
            stop_price=stop_price,
            quantity=base_quantity * share,
            score=score,
            metadata=metadata,
        )

    def _cap_total_quantity(self, intents: list[TradeIntent], base_quantity: float) -> list[TradeIntent]:
        capped: list[TradeIntent] = []
        remaining = base_quantity
        for intent in intents:
            quantity = min(intent.quantity, remaining)
            if quantity <= 0:
                break
            capped.append(intent.model_copy(update={"quantity": quantity}))
            remaining -= quantity
        return capped


class LifecycleEngine:
    """Required finite state machine with auditable transition reasons."""

    def __init__(self, config: BreakoutStrategyConfig | None = None) -> None:
        self.config = config or BreakoutStrategyConfig()
        self.state = FsmState.LEVEL_SEARCH
        self.history: list[LifecycleTransition] = []

    def setup_ready(self, reason: str) -> None:
        self._transition(FsmState.SETUP_READY, reason)

    def scenario_picked(self, reason: str) -> None:
        self._transition(FsmState.SCENARIO_PICK, reason)

    def entry_modes_picked(self, reason: str) -> None:
        self._transition(FsmState.ENTRY_MODE_PICK, reason)

    def position_opened(self, reason: str) -> None:
        self._transition(FsmState.POSITION_OPEN, reason)

    def breakout_confirmed(self, reason: str) -> None:
        self._transition(FsmState.BREAKOUT_CONFIRM, reason)

    def retest_monitor(self, reason: str) -> None:
        self._transition(FsmState.RETEST_MONITOR, reason)

    def addon_monitor(self, reason: str) -> None:
        self._transition(FsmState.ADDON_MONITOR, reason)

    def partial_exit(self, reason: str) -> None:
        self._transition(FsmState.PARTIAL_EXIT, reason)

    def false_breakout(self, reason: str) -> None:
        self._transition(FsmState.FALSE_BREAKOUT, reason)

    def complete(self, reason: str) -> None:
        self._transition(FsmState.COMPLETE, reason)

    def invalidate_setup(self, reason: str) -> None:
        self._transition(FsmState.LEVEL_SEARCH, reason)

    def evaluate_retest(self, market: MarketSnapshot, *, level_price: float, tolerance: float = 0.10) -> bool:
        """Return whether retest touches the zone, holds structure, and resumes impulse."""

        touches_zone = market.low <= level_price + tolerance and market.high >= level_price - tolerance
        holds_level = market.close >= level_price
        return touches_zone and holds_level and market.micro_impulse

    def detect_false_breakout(
        self,
        market: MarketSnapshot,
        *,
        side: Side,
        level_price: float,
        buffer: float = 0.05,
        max_bars: int = 3,
    ) -> bool:
        """Detect false breakout as a first-class lifecycle condition."""

        if market.bars_since_breakout > max_bars:
            return False
        if side is Side.LONG:
            return market.close < level_price - buffer
        return market.close > level_price + buffer

    def partial_exit_quantities(self, total_quantity: float) -> dict[str, float]:
        """Plan baseline 30/50/20 partial exits for a filled position."""

        if total_quantity <= 0:
            return {"first_fixation": 0.0, "second_fixation": 0.0, "runner": 0.0}
        return {
            "first_fixation": total_quantity * 0.30,
            "second_fixation": total_quantity * 0.50,
            "runner": total_quantity * 0.20,
        }

    def plan_exit_framework(
        self,
        *,
        total_quantity: float,
        side: Side,
        low_breakout: bool,
    ) -> ExitPlan:
        """Plan baseline or accelerated low-breakout exits without live side effects."""

        if (
            total_quantity > 0
            and self.config.fast_exit_for_low_breakouts
            and side is Side.SHORT
            and low_breakout
        ):
            return ExitPlan(
                fast_exit=True,
                reason="fast_exit_low_breakout",
                quantities={
                    "first_fixation": total_quantity * 0.50,
                    "second_fixation": total_quantity * 0.50,
                    "runner": 0.0,
                },
            )
        return ExitPlan(
            reason="baseline_exit_framework",
            quantities=self.partial_exit_quantities(total_quantity),
        )

    def move_stop_after_first_fixation(
        self,
        *,
        side: Side,
        entry_price: float,
        protected_plus: float = 0.0,
    ) -> float:
        """Move stop to breakeven/protected-plus after first fixation."""

        if side is Side.LONG:
            return entry_price + protected_plus
        return entry_price - protected_plus

    def _transition(self, to_state: FsmState, reason: str) -> None:
        self.history.append(
            LifecycleTransition(
                from_state=self.state,
                to_state=to_state,
                reason=reason,
                timestamp=datetime.now(tz=UTC),
            )
        )
        self.state = to_state
