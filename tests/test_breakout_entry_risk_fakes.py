from datetime import UTC, datetime, timedelta

import pytest

from src.app.breakout.entry_engine import EntryEngine, LifecycleEngine
from src.app.breakout.execution import FakeExecutionAdapter
from src.app.breakout.risk_manager import RiskManager
from src.core.enums import EntryMode, FsmState, RiskRejectionReason, ScenarioType, Side
from src.core.models import (
    BreakoutScore,
    BreakoutStrategyConfig,
    EntryConfig,
    ExecutionRequest,
    MarketSnapshot,
    PositionState,
    RiskLimits,
    RiskState,
    TradeIntent,
)


def score(total: int = 80) -> BreakoutScore:
    return BreakoutScore(
        symbol="XAUUSD",
        side=Side.LONG,
        scenario=ScenarioType.CONSOLIDATION_BREAKOUT,
        total=total,
        consolidation=20,
        slow_approach=20,
        trend=20,
        activity=20,
        density=0,
        eligibility="normal" if total >= 70 else "blocked",
        rejection_reasons=[] if total >= 70 else ["score_too_low"],
    )


def snapshot(
    *,
    price: float = 100.0,
    close: float | None = None,
    low: float | None = None,
    high: float | None = None,
    bars_since_breakout: int = 1,
    micro_impulse: bool = True,
) -> MarketSnapshot:
    value = close if close is not None else price
    return MarketSnapshot(
        symbol="XAUUSD",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(minutes=bars_since_breakout),
        price=price,
        close=value,
        high=high if high is not None else max(price, value),
        low=low if low is not None else min(price, value),
        bars_since_breakout=bars_since_breakout,
        micro_impulse=micro_impulse,
    )


def test_entry_intents_use_default_share_caps_and_never_exceed_base_position() -> None:
    engine = EntryEngine(BreakoutStrategyConfig())

    intents = engine.generate_intents(
        score=score(),
        side=Side.LONG,
        level_price=100.0,
        base_quantity=10.0,
        stop_price=98.0,
        market=snapshot(price=100.1, close=100.2),
        pre_entry_ready=True,
        at_level_ready=True,
    )

    assert [intent.mode for intent in intents] == [
        EntryMode.PRE_ENTRY,
        EntryMode.AT_LEVEL,
        EntryMode.POST_BREAKOUT,
    ]
    assert [intent.quantity for intent in intents] == pytest.approx([3.0, 3.0, 4.0])
    assert sum(intent.quantity for intent in intents) == pytest.approx(10.0)


def test_lower_protorgovka_entry_requires_explicit_flag_and_records_subtype() -> None:
    engine = EntryEngine(
        BreakoutStrategyConfig(
            entries=EntryConfig(lower_protorgovka_entry_enabled=True),
        )
    )

    intents = engine.generate_intents(
        score=score(),
        side=Side.LONG,
        level_price=100.0,
        base_quantity=10.0,
        stop_price=98.0,
        market=snapshot(price=99.4, close=99.5),
        lower_protorgovka_ready=True,
    )

    assert len(intents) == 1
    assert intents[0].mode is EntryMode.PRE_ENTRY
    assert intents[0].quantity == pytest.approx(3.0)
    assert intents[0].metadata["reason"] == "lower_protorgovka_ready"
    assert intents[0].metadata["entry_subtype"] == "lower_protorgovka_boundary"


def test_lower_protorgovka_entry_falls_back_when_disabled_not_ready_or_short() -> None:
    disabled = EntryEngine(BreakoutStrategyConfig())
    enabled = EntryEngine(
        BreakoutStrategyConfig(entries=EntryConfig(lower_protorgovka_entry_enabled=True))
    )

    disabled_intents = disabled.generate_intents(
        score=score(),
        side=Side.LONG,
        level_price=100.0,
        base_quantity=10.0,
        stop_price=98.0,
        market=snapshot(price=99.4, close=99.5),
        lower_protorgovka_ready=True,
    )
    not_ready_intents = enabled.generate_intents(
        score=score(),
        side=Side.LONG,
        level_price=100.0,
        base_quantity=10.0,
        stop_price=98.0,
        market=snapshot(price=99.4, close=99.5),
        lower_protorgovka_ready=False,
    )
    short_intents = enabled.generate_intents(
        score=score(),
        side=Side.SHORT,
        level_price=100.0,
        base_quantity=10.0,
        stop_price=102.0,
        market=snapshot(price=100.0, close=100.0),
        lower_protorgovka_ready=True,
    )
    blocked_intents = enabled.generate_intents(
        score=score(total=40),
        side=Side.LONG,
        level_price=100.0,
        base_quantity=10.0,
        stop_price=98.0,
        market=snapshot(price=99.4, close=99.5),
        lower_protorgovka_ready=True,
    )

    zero_quantity_intents = enabled.generate_intents(
        score=score(),
        side=Side.LONG,
        level_price=100.0,
        base_quantity=0.0,
        stop_price=98.0,
        market=snapshot(price=99.4, close=99.5),
        lower_protorgovka_ready=True,
    )

    assert disabled_intents == []
    assert not_ready_intents == []
    assert short_intents == []
    assert blocked_intents == []
    assert zero_quantity_intents == []


def test_lifecycle_records_ordered_transitions_false_breakout_and_partial_exit() -> None:
    lifecycle = LifecycleEngine()

    lifecycle.setup_ready("level_valid")
    lifecycle.scenario_picked("primary_scenario")
    lifecycle.entry_modes_picked("entry_intents_created")
    lifecycle.position_opened("fake_fill")
    lifecycle.breakout_confirmed("close_above_buffer")
    lifecycle.retest_monitor("watch_retest")
    lifecycle.false_breakout("failed_retest")
    lifecycle.complete("closed_false_breakout")

    assert [transition.to_state for transition in lifecycle.history] == [
        FsmState.SETUP_READY,
        FsmState.SCENARIO_PICK,
        FsmState.ENTRY_MODE_PICK,
        FsmState.POSITION_OPEN,
        FsmState.BREAKOUT_CONFIRM,
        FsmState.RETEST_MONITOR,
        FsmState.FALSE_BREAKOUT,
        FsmState.COMPLETE,
    ]
    assert lifecycle.history[-2].reason == "failed_retest"

    successful = LifecycleEngine()
    successful.setup_ready("level_valid")
    successful.scenario_picked("primary_scenario")
    successful.entry_modes_picked("entry_intents_created")
    successful.position_opened("fake_fill")
    successful.breakout_confirmed("close_above_buffer")
    successful.retest_monitor("watch_retest")
    assert successful.evaluate_retest(snapshot(low=99.95, close=100.35), level_price=100.0)
    successful.addon_monitor("valid_retest")
    successful.partial_exit("first_fixation")
    successful.complete("runner_closed")

    assert successful.state is FsmState.COMPLETE
    assert successful.history[-2].to_state is FsmState.PARTIAL_EXIT


def test_partial_exit_framework_and_stop_move_are_deterministic() -> None:
    lifecycle = LifecycleEngine()

    exits = lifecycle.partial_exit_quantities(10.0)
    protected_stop = lifecycle.move_stop_after_first_fixation(
        side=Side.LONG,
        entry_price=100.0,
        protected_plus=0.2,
    )

    assert exits == pytest.approx({"first_fixation": 3.0, "second_fixation": 5.0, "runner": 2.0})
    assert protected_stop == pytest.approx(100.2)


def test_setup_invalidation_resets_to_level_search_with_reason() -> None:
    lifecycle = LifecycleEngine()
    lifecycle.setup_ready("level_valid")

    lifecycle.invalidate_setup("recent_break")

    assert lifecycle.state is FsmState.LEVEL_SEARCH
    assert lifecycle.history[-1].reason == "recent_break"


def test_retest_evaluation_is_side_symmetric_for_short_setups() -> None:
    lifecycle = LifecycleEngine()

    short_holds = lifecycle.evaluate_retest(
        snapshot(low=99.95, high=100.05, close=99.80),
        level_price=100.0,
        side=Side.SHORT,
    )
    short_fails = lifecycle.evaluate_retest(
        snapshot(low=99.95, high=100.05, close=100.20),
        level_price=100.0,
        side=Side.SHORT,
    )

    assert short_holds is True
    assert short_fails is False


def test_retest_evaluation_keeps_long_hold_semantics_by_default() -> None:
    lifecycle = LifecycleEngine()

    long_holds = lifecycle.evaluate_retest(
        snapshot(low=99.95, high=100.05, close=100.20),
        level_price=100.0,
    )
    long_fails = lifecycle.evaluate_retest(
        snapshot(low=99.95, high=100.05, close=99.80),
        level_price=100.0,
    )

    assert long_holds is True
    assert long_fails is False


def test_fast_exit_low_breakout_short_uses_accelerated_no_runner_plan() -> None:
    lifecycle = LifecycleEngine(BreakoutStrategyConfig(fast_exit_for_low_breakouts=True))

    plan = lifecycle.plan_exit_framework(
        total_quantity=10.0,
        side=Side.SHORT,
        low_breakout=True,
    )

    assert plan.fast_exit is True
    assert plan.reason == "fast_exit_low_breakout"
    assert plan.quantities == pytest.approx(
        {"first_fixation": 5.0, "second_fixation": 5.0, "runner": 0.0}
    )


def test_fast_exit_falls_back_to_baseline_when_disabled_or_not_low_breakout_short() -> None:
    disabled = LifecycleEngine(BreakoutStrategyConfig(fast_exit_for_low_breakouts=False))
    enabled = LifecycleEngine(BreakoutStrategyConfig(fast_exit_for_low_breakouts=True))

    disabled_plan = disabled.plan_exit_framework(
        total_quantity=10.0,
        side=Side.SHORT,
        low_breakout=True,
    )
    long_plan = enabled.plan_exit_framework(
        total_quantity=10.0,
        side=Side.LONG,
        low_breakout=True,
    )
    non_low_plan = enabled.plan_exit_framework(
        total_quantity=10.0,
        side=Side.SHORT,
        low_breakout=False,
    )

    assert disabled_plan.fast_exit is False
    assert disabled_plan.reason == "baseline_exit_framework"
    assert disabled_plan.quantities == pytest.approx(
        {"first_fixation": 3.0, "second_fixation": 5.0, "runner": 2.0}
    )
    assert long_plan.fast_exit is False
    assert non_low_plan.fast_exit is False


def test_fast_exit_requires_positive_quantity() -> None:
    lifecycle = LifecycleEngine(BreakoutStrategyConfig(fast_exit_for_low_breakouts=True))

    plan = lifecycle.plan_exit_framework(
        total_quantity=0.0,
        side=Side.SHORT,
        low_breakout=True,
    )

    assert plan.fast_exit is False
    assert plan.reason == "baseline_exit_framework"
    assert plan.quantities == {"first_fixation": 0.0, "second_fixation": 0.0, "runner": 0.0}


def test_risk_manager_blocks_daily_loss_max_positions_feed_broker_and_invalid_stop() -> None:
    manager = RiskManager(RiskLimits(max_daily_loss=500.0, max_open_positions=1))
    intent = TradeIntent(
        intent_id="entry-1",
        symbol="XAUUSD",
        side=Side.LONG,
        mode=EntryMode.POST_BREAKOUT,
        entry_price=100.0,
        stop_price=98.0,
        quantity=1.0,
        score=score(),
    )

    assert manager.evaluate(intent, RiskState(realized_pnl=-500.0)).reason is RiskRejectionReason.DAILY_LOSS_LIMIT
    assert manager.evaluate(intent, RiskState(open_positions=1)).reason is RiskRejectionReason.MAX_POSITIONS
    assert manager.evaluate(intent, RiskState(feed_degraded=True)).reason is RiskRejectionReason.FEED_DEGRADED
    assert manager.evaluate(intent, RiskState(broker_state_mismatch=True)).reason is RiskRejectionReason.BROKER_STATE_MISMATCH
    assert manager.evaluate(intent.model_copy(update={"stop_price": 100.0}), RiskState()).reason is RiskRejectionReason.INVALID_STOP_DISTANCE


def test_risk_manager_sizes_entries_and_blocks_bad_addons() -> None:
    manager = RiskManager(
        RiskLimits(
            equity=10_000.0,
            risk_pct=0.01,
            contract_multiplier=1.0,
            max_addons=2,
            max_total_risk_pct=0.05,
            degrade_avg_price_limit_atr=1.0,
        )
    )
    entry = TradeIntent(
        intent_id="entry-1",
        symbol="XAUUSD",
        side=Side.LONG,
        mode=EntryMode.POST_BREAKOUT,
        entry_price=100.0,
        stop_price=98.0,
        quantity=100.0,
        score=score(),
    )
    addon = entry.model_copy(
        update={
            "intent_id": "addon-1",
            "mode": EntryMode.POST_BREAKOUT,
            "is_addon": True,
            "entry_price": 101.0,
            "quantity": 20.0,
        }
    )
    position = PositionState(symbol="XAUUSD", side=Side.LONG, quantity=100.0, average_price=100.0)

    approved_entry = manager.evaluate(entry, RiskState())
    approved_addon = manager.evaluate(addon, RiskState(open_risk=100.0), position=position, atr=1.0)
    too_many_addons = manager.evaluate(addon, RiskState(addon_count=2), position=position, atr=1.0)
    degrading_addon = manager.evaluate(
        addon.model_copy(update={"entry_price": 107.0}),
        RiskState(open_risk=100.0),
        position=position,
        atr=1.0,
    )

    assert approved_entry.approved is True
    assert approved_entry.quantity == pytest.approx(50.0)
    assert approved_addon.approved is True
    assert too_many_addons.reason is RiskRejectionReason.INSUFFICIENT_RISK_BUDGET
    assert degrading_addon.reason is RiskRejectionReason.ADDON_DEGRADES_AVERAGE


def test_risk_manager_reports_multiplier_aware_planned_risk_for_entries() -> None:
    manager = RiskManager(
        RiskLimits(
            equity=10_000.0,
            risk_pct=0.01,
            contract_multiplier=10.0,
        )
    )
    entry = TradeIntent(
        intent_id="entry-multiplier",
        symbol="XAUUSD",
        side=Side.LONG,
        mode=EntryMode.POST_BREAKOUT,
        entry_price=100.0,
        stop_price=98.0,
        quantity=100.0,
        score=score(),
    )

    approved_entry = manager.evaluate(entry, RiskState())

    assert approved_entry.approved is True
    assert approved_entry.quantity == pytest.approx(5.0)
    assert approved_entry.planned_risk == pytest.approx(100.0)


def test_density_support_plan_records_side_symmetric_stop_and_exit_policy() -> None:
    manager = RiskManager(RiskLimits(density_stop_buffer=0.25))
    position = PositionState(symbol="XAUUSD", side=Side.LONG, quantity=10.0, average_price=100.0)

    long_plan = manager.plan_density_support(
        symbol="XAUUSD",
        side=Side.LONG,
        density_reference=99.5,
        affected_quantity=3.0,
        base_position=position,
    )
    short_plan = manager.plan_density_support(
        symbol="XAUUSD",
        side=Side.SHORT,
        density_reference=100.5,
        affected_quantity=2.0,
        base_position=position.model_copy(update={"side": Side.SHORT}),
    )

    assert long_plan.stop_price == pytest.approx(99.25)
    assert short_plan.stop_price == pytest.approx(100.75)
    assert long_plan.stop_placement_rule == "behind_density"
    assert long_plan.exit_on_density_eating_rule == "reduce_affected_quantity"
    assert long_plan.remaining_base_quantity == pytest.approx(7.0)
    assert long_plan.metadata["density_reference"] == pytest.approx(99.5)


def test_density_eating_invalidation_records_reset_reason_and_remaining_base_state() -> None:
    manager = RiskManager(RiskLimits(density_stop_buffer=0.25))
    plan = manager.plan_density_support(
        symbol="XAUUSD",
        side=Side.LONG,
        density_reference=99.5,
        affected_quantity=3.0,
        base_position=PositionState(
            symbol="XAUUSD",
            side=Side.LONG,
            quantity=10.0,
            average_price=100.0,
        ),
    )

    still_valid = manager.evaluate_density_invalidation(plan, density_eaten=False)
    invalidated = manager.evaluate_density_invalidation(plan, density_eaten=True)

    assert still_valid.action == "hold"
    assert still_valid.reason == "density_still_valid"
    assert invalidated.action == "reduce_affected_quantity"
    assert invalidated.reason == "density_eaten"
    assert invalidated.affected_quantity == pytest.approx(3.0)
    assert invalidated.remaining_base_quantity == pytest.approx(7.0)
    assert invalidated.metadata["stop_price"] == pytest.approx(99.25)


def test_fake_execution_adapter_is_idempotent_and_reconciles_local_state() -> None:
    adapter = FakeExecutionAdapter()
    request = ExecutionRequest(
        request_id="req-1",
        intent_id="intent-1",
        symbol="XAUUSD",
        side=Side.LONG,
        quantity=2.0,
        price=100.0,
    )

    first = adapter.submit_order(request)
    duplicate = adapter.submit_order(request)
    adapter.simulate_fill(first.order_id, fill_price=100.2, quantity=2.0)
    snapshot_state = adapter.reconcile()

    assert duplicate.order_id == first.order_id
    assert len(adapter.orders) == 1
    assert snapshot_state.positions["XAUUSD"].quantity == pytest.approx(2.0)
    assert adapter.cancel_order(first.order_id).status == "cancel_rejected_filled"
