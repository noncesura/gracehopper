import bz2
import csv
import re
from datetime import datetime, timedelta
from collections import defaultdict

filename = "pagecounts-2013-12-views-ge-5.bz2"

hourly = defaultdict(int)
found = False

print("searching English Wikipedia...", flush=True)

with bz2.open(filename, "rt", encoding="utf-8", errors="replace") as f:
    for line in f:
        parts = line.strip().split(maxsplit=3)

        if len(parts) != 4:
            continue

        wiki, title, monthly_total, encoded = parts

        # ENGLISH WIKIPEDIA ONLY
        if wiki != "en.z" or title != "Grace_Hopper":
            continue

        found = True
        monthly_total = int(monthly_total)

        print("FOUND Grace_Hopper!")
        print("monthly views:", f"{monthly_total:,}")

        # Each comma-separated group represents one day.
        for group in encoded.split(","):
            if not group:
                continue

            day = ord(group[0]) - ord("A") + 1
            hour_data = group[1:]

            if not (1 <= day <= 31):
                raise ValueError("invalid day")

            # Extract every hour/count pair within that day.
            matches = list(
                re.finditer(r"([A-X])(\d+)", hour_data)
            )

            # Verify nothing was silently skipped.
            reconstructed = "".join(
                m.group(0) for m in matches
            )
            if reconstructed != hour_data:
                raise ValueError(
                    f"invalid hourly data: {group[:80]}"
                )

            for match in matches:
                hour = ord(match.group(1)) - ord("A")
                views = int(match.group(2))

                timestamp = datetime(
                    2013, 12, day, hour
                )

                # Align EZ hour labels to actual UTC hours.
                timestamp -= timedelta(hours=1)

                hourly[timestamp] += views

        break

if not found:
    raise SystemExit("article not found")

# VALIDATE THE DECODED MONTH
decoded_total = sum(hourly.values())

print("decoded views:", f"{decoded_total:,}")

if decoded_total != monthly_total:
    raise SystemExit(
        "ERROR: monthly total does not match! "
        "No report generated."
    )

print("validation passed!")

# DECEMBER 8 THROUGH DECEMBER 16 INCLUSIVE
start = datetime(2013, 12, 8)
end = datetime(2013, 12, 17)

daily = defaultdict(int)
total = 0

with open(
    "grace_hopper_hourly.csv",
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.writer(file)
    writer.writerow(["date", "hour_utc", "views"])

    current = start

    while current < end:
        views = hourly[current]

        writer.writerow([
            current.strftime("%Y-%m-%d"),
            current.strftime("%H:00"),
            views
        ])

        daily[current.date()] += views
        total += views

        current += timedelta(hours=1)

with open(
    "grace_hopper_daily.csv",
    "w", newline="", encoding="utf-8"
) as file:

    writer = csv.writer(file)
    writer.writerow(["date", "views"])

    for day, views in sorted(daily.items()):
        writer.writerow([day.isoformat(), views])

print("\nDAILY VIEWS")
print("-" * 35)

for day, views in sorted(daily.items()):
    print(day, f"{views:,}")

print("-" * 35)
print("TOTAL DEC 8-16:", f"{total:,}")

print("\nSAVED:")
print("grace_hopper_hourly.csv")
print("grace_hopper_daily.csv")
