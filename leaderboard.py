#!/usr/bin/env python

import click
import json
import requests
import time

from typing import Union
from pathlib import Path

@click.command("leaderboard", context_settings=dict(help_option_names=['-h', '--help']))
@click.option("-d", "--display-day", type=int, default=None, help="Challenge day to display in the table. (not passing this argument will try to display all the days)")
@click.option("--sorting-day", type=int, default=None, help="Challenge day to use to sort the multi-day table.")
@click.option("-s", "--sorting-star", type=click.Choice(["1", "2"]), default="1", help="Challenge star of the day to use to sort the table.")
@click.option("-f", "--from-file", type=str, default=None, help="Use that file instead of the default loadint method (from url).")
@click.option("-t", "--timestamps", is_flag=True, default=False, help="WIP display timestamps instead of completion times.")
@click.option("-y", "--year", type=int, default=2021, help="WIP Retrieve a different challenge year.")
@click.option("-u", "--update", "ignore_cache", is_flag=True, default=False, help="Force updating the local cache from the AOC website. (use parsimoniously)")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Make the program more talkative.")
@click.option("-p", "--private-key", type=str, default=None, help="Key of the private leaderboard to fetch. If not provided and not available in 'leaderboard_key.txt', you will be prompted for it.")
@click.option("-c", "--cookie-key", "session_cookie", type=str, default=None, help="Your session cookie. If not provided and not available in 'session_cookie.txt', you will be prompted for it.")
def leaderboard(display_day: int, sorting_day: int, sorting_star: int, from_file: Union[str, None], year: int, timestamps: bool, ignore_cache: bool, private_key: str, session_cookie: Union[str, None], verbose: bool):
    """Displays an Advent of Code leaderboard in CLI.

    Tries to load a previously saved cache file of the leaderboard (valid 15 minutes),
    Then, if needed, tries to get the leaderboard from the website.

    If a file is specified, uses that instead.
    """
    sorting_star = int(sorting_star)
    session_cookie_file = "session_cookie.txt"
    private_key_file = "leaderboard_key.txt"
    cache_timeout_s = 60 * 15

    if not session_cookie:
        try:
            with open(session_cookie_file) as f:
                session_cookie = f.readline().strip("\t\n ")
        except OSError as e:
            if verbose:
                print(e)
            print(
                "WARNING: Could not read your session cookie.\nPlease retrieve it:\n"
                "- Open the developer tools in your browser (F12),\n- Navigate to the "
                "cookies section while logged on a page of the AOC website.\n- Find the "
                "cookie named 'session' (look for the 'storage' tab in Firefox, or "
                "'Application' -> 'Cookies' in Chrome) and copy it (it should be a long "
                "string of characters and numbers).\n"
            )
            session_cookie = input("Paste your session cookie here:")
            if not session_cookie or len(session_cookie) < 80:
                raise ValueError(f"Invalid cookie input? {session_cookie}")
    try:
        with open(session_cookie_file, "w") as f:
            f.write(session_cookie)
    except OSError as e:
        if verbose:
            print(e)
        print(f"Could not write the '{session_cookie_file}' file. (-v) for more.")

    if not private_key:
        try:
            with open(private_key_file) as f:
                private_key = f.readline().strip("\t\n ")
        except OSError as e:
            if verbose:
                print(e)
            private_key = input(
                "Paste your leaderboard key here (should be 7 characters long):"
            )
            if not private_key or len(private_key) != 7:
                print(f"Invalid key input? {private_key}")
    try:
        with open(private_key_file, "w") as f:
            f.write(private_key)
    except OSError as e:
        if verbose:
            print(e)
        print(f"Could not write the '{private_key_file}' file. (-v) for more.")

    leaderboard = None
    if not from_file and not ignore_cache:
        if verbose:
            print("Loading from cache...")
        try:
            latest_cache_t = 0
            sorted_cache_files = sorted(Path().glob(f"leaderboard_{year}_{private_key}_cache_*.json"))
            for cache_file in sorted_cache_files:
                cache_t = int(cache_file.stem.split("_")[-1])
                if int(time.time()) - cache_t > cache_timeout_s:
                    if verbose:
                        print(f"Removing old cache file {int(time.time() - latest_cache_t)}s")
                    cache_file.unlink(missing_ok=True)
                    continue
                else:
                    if cache_t > latest_cache_t:
                        if verbose:
                            print(f"Found a cache file {int(time.time() - cache_t)}s")
                        if latest_cache_t != 0:
                            from_file.unlink(missing_ok=True)
                        from_file = cache_file
                        latest_cache_t = cache_t
        except Exception as e:
            if verbose:
                print(f"WARNING: unable to retrieve the scores from cache.")
                print(e)
        if verbose and from_file:
            cache_age = int(time.time() - latest_cache_t)
            print(
                f"Cache is up to date. ({cache_age}/{cache_timeout_s} seconds old)"
            )

    leaderboard_url = f"https://adventofcode.com/{year}/leaderboard/private/view/{private_key}.json"
    if not from_file:
        if verbose:
            print(f"Requesting leaderboard from {leaderboard_url}...")
        try:
            if leaderboard is None:
                with requests.Session() as s:
                    s.cookies.set("session", session_cookie)
                    resp = s.get(leaderboard_url)
                    leaderboard = resp.json()
                    with open(f"leaderboard_{year}_{private_key}_cache_{int(time.time())}.json", "w") as f:
                        json.dump(leaderboard, f)
        except Exception as e:
            print(
                f"ERROR: unable to retrieve the scores from {leaderboard_url}. "
                "(-v) for more."
            )
            print(
                "    Maybe your session cookie is outdated (should last about a month) "
                "or invalid? Workaround: delete the 'session-cookie.txt' file."
            )  # TODO detect that (if response is the unlogged-in AOC leaderboard page) and ask for new cookie
            if verbose:
                print(e)
    else:
        with open(from_file) as f:
            leaderboard = json.load(f)

    if not leaderboard:
        print(
            "ERROR: No leaderboard found in cache, url, or file. Exiting. "
            "(-v) for more."
        )
        exit(-1)

    day1 = 1638334800 # TODO adaptive to year
    days_timestamps = {d+1:day1+d*24*3600 for d in range(25)}

    timestamps_struct = {}
    names = []
    anonymous = []
    seen_days = []

    for member_id, member in leaderboard["members"].items():
        name = member["name"]
        if name is None:
            name = f"User {member_id}"
            anonymous.append(name)
        else:
            names.append(name)
        timestamps_struct[name] = {}
        for day, stars in member["completion_day_level"].items():
            day = int(day)
            if day not in seen_days:
                seen_days.append(day)
            timestamps_struct[name][day] = {}
            for i,s in stars.items():
                timestamps_struct[name][day][int(i)] = (
                    s["get_star_ts"] - (
                        days_timestamps[day] if not timestamps else 0
                    )
                )

    names = sorted(names, key=lambda x: x.lower()) + sorted(anonymous)

    sorting_day = display_day or sorting_day or max(seen_days)

    if verbose:
        print(f"Sorting by time of day {sorting_day} and star {sorting_star}.")


    name_str_length = max(len(n) for n in names)
    time_length = 11 if timestamps else 9

    # Titles
    if display_day:
        day_title = f"day {display_day}"
        print(" "*(name_str_length+1+(time_length*2-len(day_title))//2+1) + day_title)
        print(" "*(name_str_length+1+(time_length-len("star x"))//2+1) + "star 1" + " "*((time_length-len("star x"))) + "star 2")
    else:
        day_title_str = " "*(name_str_length+1+(time_length*2-len("day 1"))//2+1) + "day 1"
        stars_title_str = " "*(name_str_length+1+(time_length-len("star 1"))//2+1) + "star 1" + " "*((time_length-len("star 2"))) + "star 2"
        for d in sorted(seen_days)[1:]:
            day_title_str += " "*(time_length*2-len(f"day {d}")) + f"day {d}"
            stars_title_str += " "*((time_length-len("star 1"))) + "star 1" + " "*((time_length-len("star 2"))) + "star 2"
        print(day_title_str)
        print(stars_title_str)


    BIG = 2**33 # Number over what epoch/2 can go

    def sorting(val: tuple[str, dict]):
        if val[1] is None or sorting_day not in val[1]:
            return BIG + names.index(val[0])
        if sorting_star not in val[1][sorting_day]:
            return BIG/2 + val[1][sorting_day][3-sorting_star]
        return val[1][sorting_day][sorting_star]

    # Table
    for user, days in sorted(timestamps_struct.items(), key=sorting):
        print(f"{user:{name_str_length}s}:", end="")
        for day,stars in sorted(days.items()):
            if display_day and day != display_day:
                continue
            for s in sorted(stars.values(), key=lambda x:x):
                if timestamps:
                    print(f" {s}", end="")
                else:
                    if s//3600:
                        print(f" {s//3600:2d}:", end="")
                    else:
                        print("    ", end="")
                    if (s%3600)//60 or s//3600:
                        print(f"{(s%3600)//60:02d}:", end="")
                    else:
                        print("    ", end="")
                    print(f"{(s%3600)%60:02d}", end="")
        print()


if __name__ == "__main__":
    leaderboard()
