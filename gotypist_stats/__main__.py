#! /usr/bin/env python3

from argparse import ArgumentParser
from datetime import date, datetime
from json import loads
from os import getenv, path
from re import sub

from .report import (
    Mode,
    Typo,
    Stat,
    hitmap,
    training_time,
    common_typos,
    typo_record,
    cps_progress,
)


def _to_datetime(iso: str) -> datetime:
    parsable = sub(r"([\d\-T:]{19}\.\d{6})\d*([+\-]\d{2}):(\d{2})", "\\1|\\2\\3", iso)

    return datetime.strptime(parsable, "%Y-%m-%dT%H:%M:%S.%f|%z")


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


def main():
    parser = ArgumentParser(description="Analyze the logs of your gotypist sessions.")
    parser.add_argument(
        "--stats-file",
        default=path.join(getenv("HOME", ""), ".gotypist.stats"),
        help="Stats file generated by gotypist. Default $HOME/.gotypist.stats",
    )
    parser.add_argument("--version", action="version", version="1.1.4")

    args = parser.parse_args()

    today = date.today()
    stats = list(read_stats(args.stats_file))

    for report in [
        hitmap(today, stats),
        training_time(stats),
        typo_record(stats),
        common_typos(stats),
        cps_progress(stats),
    ]:
        print(f"\n🟄 {report.title} 🟄\n")
        print(report.content)


if __name__ == "__main__":
    main()
