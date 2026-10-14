"""Altair chart builders for the dashboard.

Colors are taken directly from the validated reference palette (categorical
slot 1 = blue, slot 8 = red, muted ink = gray) rather than invented, so no
extra contrast/CVD validation is needed beyond what the palette already
guarantees for the blue<->red diverging pair and the muted-ink role.
"""

import altair as alt
import pandas as pd

PRICE_COLOR = "#2a78d6"  # categorical slot 1 (blue)
EMA_COLOR = "#898781"  # muted ink - EMA is context/baseline, not the subject
ABOVE_COLOR = "#2a78d6"  # diverging pole: blue
BELOW_COLOR = "#e34948"  # diverging pole: red (categorical slot 8)
BALANCE_COLOR = "#2a78d6"  # categorical slot 1
EQUITY_COLOR = "#eb6834"  # categorical slot 2
MUTED = "#898781"
GRIDLINE = "#e1e0d9"

_HOVER_POINT_SIZE = 50  # ~8px diameter


def _themed(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeWidth=0)
        .configure_axis(
            domainColor=GRIDLINE,
            tickColor=GRIDLINE,
            gridColor=GRIDLINE,
            labelColor=MUTED,
            titleColor=MUTED,
            labelFontSize=11,
            titleFontSize=11,
        )
        .configure_legend(labelColor=MUTED, titleColor=MUTED, labelFontSize=11)
        .properties(background="transparent")
    )


def price_ema_chart(df: pd.DataFrame) -> alt.Chart:
    """df columns: timestamp, close, ema200. Price is the subject (blue,
    solid); EMA200 is the reference baseline (muted gray, dashed) - an
    emphasis treatment, not a categorical pair, since EMA is context.
    """
    hover = alt.selection_point(fields=["timestamp"], nearest=True, on="pointerover", empty=False, clear="pointerout")
    base = alt.Chart(df)

    line_price = base.mark_line(color=PRICE_COLOR, strokeWidth=2).encode(
        x=alt.X("timestamp:T", title=None),
        y=alt.Y("close:Q", title="Price", scale=alt.Scale(zero=False)),
    )
    line_ema = base.mark_line(color=EMA_COLOR, strokeWidth=2, strokeDash=[5, 4]).encode(
        x="timestamp:T",
        y=alt.Y("ema200:Q", title="Price", scale=alt.Scale(zero=False)),
    )
    selectors = base.mark_point(opacity=0).encode(
        x="timestamp:T",
        tooltip=[
            alt.Tooltip("timestamp:T", title="Time", format="%b %d, %H:%M"),
            alt.Tooltip("close:Q", title="Price", format=",.5f"),
            alt.Tooltip("ema200:Q", title="EMA200", format=",.5f"),
        ],
    ).add_params(hover)
    points_price = line_price.mark_point(size=_HOVER_POINT_SIZE, color=PRICE_COLOR).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )
    points_ema = line_ema.mark_point(size=_HOVER_POINT_SIZE, color=EMA_COLOR).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )
    rule = base.mark_rule(color=MUTED, strokeWidth=1).encode(x="timestamp:T").transform_filter(hover)

    chart = alt.layer(line_price, line_ema, selectors, points_price, points_ema, rule).properties(height=280)
    return _themed(chart)


def distance_bar_chart(df: pd.DataFrame) -> alt.Chart:
    """df columns: timestamp, distance_pct. Diverging bar: above/below the
    EMA200 baseline, the recommended default form for this job.
    """
    df = df.copy()
    df["direction"] = df["distance_pct"].apply(lambda v: "Above EMA200" if v >= 0 else "Below EMA200")

    bars = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("timestamp:T", title=None),
            y=alt.Y("distance_pct:Q", title="Distance from EMA200 (%)"),
            color=alt.Color(
                "direction:N",
                scale=alt.Scale(domain=["Above EMA200", "Below EMA200"], range=[ABOVE_COLOR, BELOW_COLOR]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("timestamp:T", title="Time", format="%b %d, %H:%M"),
                alt.Tooltip("distance_pct:Q", title="Distance %", format="+.3f"),
            ],
        )
        .properties(height=140)
    )
    zero_rule = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=MUTED, strokeWidth=1).encode(y="y:Q")
    return _themed(bars + zero_rule)


def equity_chart(df: pd.DataFrame) -> alt.Chart:
    """df columns: timestamp, balance, equity - two real, equally-weighted
    series (categorical), sharing one axis since both are the same currency unit.
    """
    hover = alt.selection_point(fields=["timestamp"], nearest=True, on="pointerover", empty=False, clear="pointerout")
    base = alt.Chart(df)

    line_balance = base.mark_line(color=BALANCE_COLOR, strokeWidth=2).encode(
        x=alt.X("timestamp:T", title=None),
        y=alt.Y("balance:Q", title="Amount", scale=alt.Scale(zero=False)),
    )
    line_equity = base.mark_line(color=EQUITY_COLOR, strokeWidth=2).encode(
        x="timestamp:T",
        y=alt.Y("equity:Q", title="Amount", scale=alt.Scale(zero=False)),
    )
    selectors = base.mark_point(opacity=0).encode(
        x="timestamp:T",
        tooltip=[
            alt.Tooltip("timestamp:T", title="Time", format="%b %d, %H:%M"),
            alt.Tooltip("balance:Q", title="Balance", format=",.2f"),
            alt.Tooltip("equity:Q", title="Equity", format=",.2f"),
        ],
    ).add_params(hover)
    points_balance = line_balance.mark_point(size=_HOVER_POINT_SIZE, color=BALANCE_COLOR).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )
    points_equity = line_equity.mark_point(size=_HOVER_POINT_SIZE, color=EQUITY_COLOR).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )
    rule = base.mark_rule(color=MUTED, strokeWidth=1).encode(x="timestamp:T").transform_filter(hover)

    chart = alt.layer(line_balance, line_equity, selectors, points_balance, points_equity, rule).properties(height=280)
    return _themed(chart)
