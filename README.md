# Advent of Code CLI for private leaderboard

Displays a detailed leaderboard for challenges of [Advent of Code](https://www.adventofcode.com).

## Requirements

- python (>3.9)
- python libraries:
  - click
  - requests

## "Installation"

This is a simple script. Just download it and run it.

```bash
git clone git@github.com:DayerYannick/aoc-leaderboard.git
cd aoc-leaderboard
```

## Usage

Run the script via python:

```bash
python leaderboard.py
```

More info with:

```bash
python leaderboard.py -h
```

### Session cookie and leaderboard ID

To access your private leaderboard, you need two things:

- **The leaderboard ID:** you can find it at the end of the leaderboard URL (`1234567` in
  `https://adventofcode.com/2021/leaderboard/private/view/1234567`).
  You need to be part of a private leaderboard on Advent of Code to use this script.
- **Your session cookie:** you can find it by logging into advent of code, and while on
  that page, looking at the developer tool of your browser (generally accessed with
  F12).
  Search for the cookie named `session` in either the *storage* tab in Firefox, or the
  *Application* tab in Chrome. This session key is a string of characters and numbers.

  Session cookies last about a month and need to be updated from time to time.
  The script saves the last used key in a `session_cookie.txt` file. If you have trouble
  retrieving the leaderboard, try actualizing the key in the file (or deleting the file)
  and running again.

You can either give these two parameters as options (`--private-key` and `--session`),
or run the script and wait for the prompt requesting it.

## Caching

To prevent too many requests on the Advent of Code website, a system of cache of the
leaderboard is in place, actualizing every 15 minutes. If you want up-to-date results,
give the `--update` option.
