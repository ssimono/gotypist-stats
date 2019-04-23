#! /usr/bin/env python3

import sys
from datetime import date, datetime, timedelta
from calendar import day_abbr
from collections import defaultdict, namedtuple
from json import loads
from os import getenv, path
from re import sub
from statistics import median


def render(calendar):
    for weekday_hit in calendar["hits"]:
        print("".join(["░" for hit in weekday_hit]))


def _to_datetime(iso):
    parsable = sub(r"([\d\-T:]{19}\.\d{6})\d+([+\-]\d{2}):(\d{2})", "\\1|\\2\\3", iso)

    return datetime.strptime(parsable, "%Y-%m-%dT%H:%M:%S.%f|%z")


def read_stats(stats_file):
    with open(stats_file) as f:
        for line in f:
            stat = loads(line)
            yield {
                **stat,
                "started_at": _to_datetime(stat["started_at"]),
                "finished_at": _to_datetime(stat["finished_at"]),
            }


def year_hitmap(day, stats):
    begin = day - timedelta(days=182)
    last_monday = day - timedelta(day.weekday())
    first_monday = begin - timedelta(begin.weekday())
    hitmap = defaultdict(set)

    for stat in stats:
        if begin <= stat["started_at"].date() <= day:
            hitmap[stat["started_at"].isocalendar()].add(stat["text"])

    return {
        "data": hitmap,
        "median": median(map(len, hitmap.values())),
        "nb_weeks": (last_monday - first_monday).days // 7,
        "start": first_monday,
    }

def render_hitmap(hitmap):
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

if __name__ == "__main__":
    stats_file = (
        path.join(getenv("HOME"), ".gotypist.stats")
        if len(sys.argv) < 2
        else sys.argv[1]
    )
    today = date.today()
    stats = read_stats(stats_file)

    render_hitmap(year_hitmap(today, stats))
