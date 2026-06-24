"""Stable machine-readable enums for the breakout strategy foundation."""

from enum import StrEnum


class OperationMode(StrEnum):
    """Runtime operation mode."""

    ADVISORY_ONLY = "advisory_only"
    SEMI_AUTO = "semi_auto"
    FULL_AUTO = "full_auto"


class LevelType(StrEnum):
    """Supported breakout level types."""

    PIVOT_HIGH = "pivot_high"
    PIVOT_LOW = "pivot_low"
    ROUND_NUMBER = "round_number"
    DAILY_HIGH = "daily_high"
    DAILY_LOW = "daily_low"
    CASCADE = "cascade"
    TRENDLINE = "trendline"


class ScenarioType(StrEnum):
    """Primary breakout scenario types."""

    CONSOLIDATION_BREAKOUT = "consolidation_breakout"
    CASCADE_BREAKOUT = "cascade_breakout"
    LOCAL_EXTREMUM_BREAKOUT = "local_extremum_breakout"
    TRENDLINE_BREAKOUT = "trendline_breakout"
    DENSITY_SUPPORTED_BREAKOUT = "density_supported_breakout"


class EntryMode(StrEnum):
    """Position entry modes from the source methodology."""

    PRE_ENTRY = "pre_entry"
    AT_LEVEL = "at_level"
    POST_BREAKOUT = "post_breakout"


class FsmState(StrEnum):
    """Required logical trade-lifecycle states."""

    LEVEL_SEARCH = "LEVEL_SEARCH"
    SETUP_READY = "SETUP_READY"
    SCENARIO_PICK = "SCENARIO_PICK"
    ENTRY_MODE_PICK = "ENTRY_MODE_PICK"
    POSITION_OPEN = "POSITION_OPEN"
    BREAKOUT_CONFIRM = "BREAKOUT_CONFIRM"
    RETEST_MONITOR = "RETEST_MONITOR"
    ADDON_MONITOR = "ADDON_MONITOR"
    PARTIAL_EXIT = "PARTIAL_EXIT"
    FALSE_BREAKOUT = "FALSE_BREAKOUT"
    COMPLETE = "COMPLETE"


class RiskRejectionReason(StrEnum):
    """Stable risk rejection reasons used by traces and storage."""

    SCORE_TOO_LOW = "score_too_low"
    CONTEXT_FILTER_BLOCKED = "context_filter_blocked"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    MAX_POSITIONS = "max_positions"
    INVALID_STOP_DISTANCE = "invalid_stop_distance"
    INSUFFICIENT_RISK_BUDGET = "insufficient_risk_budget"
    ADDON_DEGRADES_AVERAGE = "addon_degrades_average"
    FEED_DEGRADED = "feed_degraded"
    BROKER_STATE_MISMATCH = "broker_state_mismatch"


class TimeFrame(StrEnum):
    """Baseline strategy timeframes."""

    M15 = "M15"
    H1 = "H1"
    H4 = "H4"
    D1 = "D1"


class Side(StrEnum):
    """Trade direction side."""

    LONG = "long"
    SHORT = "short"
