"""Approved public crypto research symbols for local breakout experiments."""

from __future__ import annotations

DEFAULT_CRYPTO_RESEARCH_SYMBOL = "BTCUSDT"
FIXED_ALTCOIN_RESEARCH_UNIVERSE = (
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "TRXUSDT",
    "TONUSDT",
    "DOTUSDT",
    "NEARUSDT",
    "LTCUSDT",
    "BCHUSDT",
    "UNIUSDT",
    "AAVEUSDT",
    "APTUSDT",
    "ARBUSDT",
    "OPUSDT",
    "INJUSDT",
    "SUIUSDT",
    "SEIUSDT",
    "ATOMUSDT",
    "ETCUSDT",
    "FILUSDT",
    "ICPUSDT",
    "IMXUSDT",
    "RUNEUSDT",
    "HBARUSDT",
    "ALGOUSDT",
    "VETUSDT",
    "THETAUSDT",
    "FETUSDT",
    "GRTUSDT",
    "MKRUSDT",
    "LDOUSDT",
    "STXUSDT",
    "JUPUSDT",
    "WIFUSDT",
    "PEPEUSDT",
    "SHIBUSDT",
    "FLOKIUSDT",
    "BONKUSDT",
    "ENAUSDT",
    "PENDLEUSDT",
    "TIAUSDT",
    "TAOUSDT",
    "WLDUSDT",
    "ONDOUSDT",
    "JASMYUSDT",
)
APPROVED_CRYPTO_RESEARCH_SYMBOLS = (
    DEFAULT_CRYPTO_RESEARCH_SYMBOL,
    *FIXED_ALTCOIN_RESEARCH_UNIVERSE,
)
APPROVED_CRYPTO_RESEARCH_SYMBOL_SET = frozenset(APPROVED_CRYPTO_RESEARCH_SYMBOLS)
FIXED_CRYPTO_RESEARCH_UNIVERSES = {
    "fixed-50-altcoins": FIXED_ALTCOIN_RESEARCH_UNIVERSE,
    "ethusdt-only": ("ETHUSDT",),
}


def normalize_crypto_research_symbol(symbol: str) -> str:
    """Normalize an approved public research symbol or fail closed."""

    normalized = symbol.strip().upper()
    if normalized not in APPROVED_CRYPTO_RESEARCH_SYMBOL_SET:
        allowed_preview = ", ".join(APPROVED_CRYPTO_RESEARCH_SYMBOLS[:8])
        msg = (
            f"unsupported public crypto research symbol: {symbol}; "
            f"expected one of approved allowlist values such as {allowed_preview}"
        )
        raise ValueError(msg)
    return normalized


def resolve_crypto_research_universe(name: str) -> tuple[str, ...]:
    """Resolve a deterministic fixed research universe name."""

    try:
        return FIXED_CRYPTO_RESEARCH_UNIVERSES[name]
    except KeyError as exc:
        msg = f"unsupported crypto research universe: {name}"
        raise ValueError(msg) from exc
