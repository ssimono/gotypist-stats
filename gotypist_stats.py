#! /usr/bin/env python3

import sys
from datetime import date, datetime, timedelta
from calendar import day_abbr
from collections import defaultdict
from enum import Enum
from typing import NamedTuple, List
from json import loads
from os import getenv, path
from re import sub
from statistics import median

Mode = Enum("Mode", "FAST SLOW NORMAL", start=0)


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


def _to_datetime(iso):
    parsable = sub(r"([\d\-T:]{19}\.\d{6})\d+([+\-]\d{2}):(\d{2})", "\\1|\\2\\3", iso)

    return datetime.strptime(parsable, "%Y-%m-%dT%H:%M:%S.%f|%z")


def _human_duration(start, end):
    secs = int((end - start).total_seconds())
    if secs <= 120:
        return f"{secs} seconds"
    elif secs <= 3600 * 2:
        return f"~{secs // 60} minutes"
    else:
        return f"~{secs // 3600} hours"


def read_stats(stats_file):
    with open(stats_file) as f:
        for line in f:
            stat = loads(line)
            stat.update(
                {
                    "started_at": _to_datetime(stat["started_at"]),
                    "finished_at": _to_datetime(stat["finished_at"]),
                    "mode": Mode(stat["mode"]),
                    "typos": [Typo(**t) for t in stat["typos"]],
                }
            )
            yield Stat(**stat)


def hitmap(day, stats):
    begin = day - timedelta(days=182)
    last_monday = day - timedelta(day.weekday())
    first_monday = begin - timedelta(begin.weekday())
    hitmap = defaultdict(set)

    for stat in stats:
        if begin <= stat.started_at.date() <= day:
            hitmap[stat.started_at.isocalendar()].add(stat.text)

    return {
        "data": hitmap,
        "median": median(map(len, hitmap.values())),
        "nb_weeks": (last_monday - first_monday).days // 7,
        "start": first_monday,
    }


def render_hitmap(hitmap):
    print("🟄 6 months hitmap 🟄")
    (y1, w1, _) = hitmap["start"].isocalendar()
    coords = lambda day, week: (y1 + (w1 + week) // 52, (w1 + week) % 52, day + 1)
    char = lambda treshold, v: "▓▓" if v >= treshold else "▒▒" if v > 0 else "░░"

    for day in range(7):
        practice = [
            len(hitmap["data"][coords(day, week)])
            for week in range(hitmap["nb_weeks"] + 1)
        ]
        line = "".join(map(lambda p: char(hitmap["median"], p), practice))
        print(f"{day_abbr[day]} {line}")


def typo_record(day, stats):
    return sorted(stats, key=lambda s: s.errors, reverse=True)[0]


def render_typo_record(worse):
    print("\n🟄 Highest number of typos 🟄")
    print(
        f"""{worse.errors} errors\
 when typing ʺ{worse.text}ʺ\
 in {worse.mode.name.lower()} mode\
 on {worse.started_at.strftime("%b %m %Y")}. It took {_human_duration(worse.started_at, worse.finished_at)}"""
    )


def common_typos(day, stats):
    typos = defaultdict(int)
    total = 0
    for stat in stats:
        if stat.errors > 0:
            for typo in stat.typos:
                typos[typo] += 1
            total += len(stat.typos)

    return (sorted(typos.items(), key=lambda i: i[1], reverse=True)[:6], total)


def render_common_typos(typos, total):
    print("\n🟄 Most common errors 🟄")
    for idx, (spec, count) in enumerate(typos):
        explanation = idx == 0 and " of all mistakes" or ""
        print(
            f"{spec.actual} instead of {spec.expected}: {count} errors ({100*count/total:.1f}%{explanation})"
        )


if __name__ == "__main__":
    stats_file = (
        path.join(getenv("HOME"), ".gotypist.stats")
        if len(sys.argv) < 2
        else sys.argv[1]
    )
    today = date.today()
    stats = list(read_stats(stats_file))

    render_hitmap(hitmap(today, stats))
    render_typo_record(typo_record(today, stats))
    render_common_typos(*common_typos(today, stats))
