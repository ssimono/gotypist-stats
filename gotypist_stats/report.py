from datetime import date, datetime, timedelta
from calendar import day_abbr
from collections import defaultdict
from enum import Enum
from functools import reduce
from typing import NamedTuple, List, Sequence as Seq, Dict, Tuple
from statistics import median

import tabulate as tb
from tabulate import tabulate

tb.PRESERVE_WHITESPACE = True

from .helper import quantiles_38

Mode = Enum("Mode", "FAST SLOW NORMAL")


class Typo(NamedTuple):
    expected: str
    actual: str


class Stat(NamedTuple):
    text: str
    started_at: datetime
    finished_at: datetime
    errors: int
    typos: List[Typo]
    mode: Mode
    seconds: float
    cps: float
    wpm: float
    version: int


class Report(NamedTuple):
    title: str
    content: str


def _human_duration(delta: timedelta) -> str:
    secs = delta.total_seconds()
    if secs <= 120:
        return f"{secs} seconds"
    elif secs <= 3600 * 2:
        return f"{secs // 60:.0f} minutes {secs % 60:0.0f}s"
    else:
        return f"{secs // 3600:.0f} hours {(secs % 3600)//60:0.0f}min"


def _box_plot(start: int, q25: int, med: int, q75: int, end: int) -> str:
    conditions = (
        (lambda i: i < start, " "),
        (lambda i: i == med, "▣"),
        (lambda i: i == start, "├"),
        (lambda i: i == end, "┤"),
        (lambda i: i >= q25 and i < med, "□"),
        (lambda i: i > med and i <= q75, "□"),
        (lambda i: i > start and i < q25, "─"),
        (lambda i: i > q75 and i < end, "─"),
    )

    plot = ""
    for i in range(end + 1):
        for cond, char in conditions:
            if cond(i):
                plot += char
                break

    return plot


def hitmap(today: date, stats: Seq[Stat]) -> Report:
    begin = today - timedelta(days=182)
    first_monday = begin - timedelta(begin.weekday())
    last_monday = today - timedelta(today.weekday())
    nb_weeks = 1 + (last_monday - first_monday).days // 7

    hitmap: Dict[date, int] = defaultdict(int)

    for stat in stats:
        if stat.started_at.date() < begin:
            continue
        hitmap[stat.started_at.date()] += 1

    med = median(hitmap.values())
    session_count = lambda week, day: hitmap[
        first_monday + timedelta(days=7 * week + day)
    ]
    char = lambda treshold, v: "▓▓" if v >= treshold else "▒▒" if v > 0 else "░░"

    lines = []
    for weekday in range(7):
        line = "".join(
            char(med, session_count(week, weekday)) for week in range(nb_weeks)
        )
        lines.append(f"{day_abbr[weekday]} {line}")

    return Report(title="6 months hitmap", content="\n".join(lines))


def training_time(stats: Seq[Stat]) -> Report:
    duration = reduce(
        lambda total, diff: total + diff,
        [s.finished_at - s.started_at for s in stats],
        timedelta(),
    )

    return Report(
        title="Overall stats",
        content=tabulate(
            [("Total training time:", _human_duration(duration))], tablefmt="grid"
        ),
    )


def typo_record(stats: Seq[Stat]) -> Report:
    worse = sorted(stats, key=lambda s: s.errors, reverse=True)[0]
    return Report(
        title="Biggest failure",
        content=tabulate(
            (
                ("was typing", worse.text),
                ("mode", worse.mode.name.lower()),
                ("failed", f"{worse.errors} times"),
                ("happened on", worse.started_at.strftime("%b %m %Y")),
                (
                    "struggled for",
                    _human_duration(worse.finished_at - worse.started_at),
                ),
            ),
            tablefmt="grid",
        ),
    )


def common_typos(stats: Seq[Stat]) -> Report:
    typos: Dict[Typo, int] = defaultdict(int)
    total = 0
    for stat in stats:
        if stat.errors > 0:
            for typo in stat.typos:
                typos[typo] += 1
            total += len(stat.typos)

    sorted_typos = sorted(typos.items(), key=lambda i: i[1], reverse=True)

    values = [
        (f"{spec.actual} instead of {spec.expected}", count, f"{count / total:.2%}")
        for (spec, count) in sorted_typos[:6]
    ]

    return Report(
        title="Most common typos",
        content=tabulate(  # type: ignore
            values,
            headers=("Typo", "Mistakes", "% of mistakes"),
            tablefmt="simple",
            showindex=range(1, len(values) + 1),  # default value confuses type checker
        ),
    )


def cps_progress(stats: Seq[Stat]) -> Report:
    cps: Dict[Tuple, List[float]] = defaultdict(list)
    for s in stats:
        if s.mode == Mode.SLOW:
            cps[(s.started_at.year, s.started_at.month)].append(s.cps)

    plot_input = [
        {
            "year": year,
            "month": month,
            "points": [min(cps), *quantiles_38(cps, n=4), max(cps)],
            "count": len(cps),
        }
        for ((year, month), cps) in cps.items()
    ]

    global_max = max(v["points"][-1] for v in plot_input)
    screen_width = 30
    scale = lambda min, max, width, value: width * float(value) / abs(max - min)
    screen_pos = lambda value: int(scale(0, global_max, screen_width, value))

    data = [
        (
            f"{datetime(input['year'], input['month'], 1).strftime('%b %Y')}",
            f"{input['points'][2]:.2}",
            _box_plot(*map(screen_pos, input["points"])),
            input["count"],
        )
        for input in plot_input
    ]

    return Report(
        "Characters per second (slow mode)",
        tabulate(
            data,
            headers=("Month", "Median cps", "Plot", "Sessions..."),
            tablefmt="simple",
        ),
    )
