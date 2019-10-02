#! /usr/bin/env python3

from argparse import ArgumentParser
from datetime import date, datetime, timedelta
from calendar import day_abbr
from collections import defaultdict
from enum import Enum
from functools import reduce
from typing import NamedTuple, List, Sequence as Seq, Dict
from json import loads
from os import getenv, path
from re import sub
from statistics import median

from tabulate import tabulate

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


def _to_datetime(iso: str) -> datetime:
    parsable = sub(r"([\d\-T:]{19}\.\d{6})\d+([+\-]\d{2}):(\d{2})", "\\1|\\2\\3", iso)

    return datetime.strptime(parsable, "%Y-%m-%dT%H:%M:%S.%f|%z")


def _human_duration(delta: timedelta) -> str:
    secs = delta.total_seconds()
    if secs <= 120:
        return f"{secs} seconds"
    elif secs <= 3600 * 2:
        return f"{secs // 60:.0f} minutes {secs % 60:0.0f}s"
    else:
        return f"{secs // 3600:.0f} hours {(secs % 3600)//60:0.0f}min"


def read_stats(stats_file):
    with open(stats_file) as f:
        for line in f:
            stat = loads(line)
            if stat.get("version", 0) != 1:
                continue

            stat.update(
                {
                    "started_at": _to_datetime(stat["started_at"]),
                    "finished_at": _to_datetime(stat["finished_at"]),
                    "mode": Mode(stat["mode"] + 1),
                    "typos": [Typo(**t) for t in stat["typos"]],
                }
            )
            yield Stat(**stat)


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
            [("Total training time:", _human_duration(duration))], tablefmt="fancy_grid"
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
            tablefmt="fancy_grid",
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
        content=tabulate(
            values, headers=("Typo", "Mistakes", "% of mistakes"), tablefmt="fancy_grid"
        ),
    )


def main(stats_file):
    today = date.today()
    stats = list(read_stats(stats_file))

    for report in [
        hitmap(today, stats),
        training_time(stats),
        common_typos(stats),
        typo_record(stats),
    ]:
        print(f"\n🟄 {report.title} 🟄\n")
        print(report.content)


if __name__ == "__main__":

    parser = ArgumentParser(description="Analyze the logs of your gotypyst sessions.")
    parser.add_argument(
        "--stats-file",
        default=path.join(getenv("HOME", ""), ".gotypist.stats"),
        help="Stats file generated by gotypist. Default $HOME/.gotypist.stats",
    )
    parser.add_argument("--version", action="version", version="1.0.0")

    args = parser.parse_args()

    main(args.stats_file)
