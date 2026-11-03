
import os
import urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser

from PIL import Image, ImageDraw


# GitHub username
USERNAME = os.environ["GITHUB_USER"]

url = f"https://github.com/users/{USERNAME}/contributions"

request = urllib.request.Request(
    url,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(request) as response:
    html = response.read().decode("utf-8")


# Extract contribution dates and levels
class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.contributions = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)

        day = attributes.get("data-date")
        level = attributes.get("data-level")

        if day and level is not None:
            try:
                self.contributions[day] = int(level)
            except ValueError:
                pass


parser = ContributionParser()
parser.feed(html)

contributions = parser.contributions

if not contributions:
    raise RuntimeError("No contribution data found.")

print(f"Found {len(contributions)} contribution days.")


# Graph dimensions
dates = sorted(date.fromisoformat(d) for d in contributions)

start = dates[0] - timedelta(days=dates[0].weekday())
weeks = ((dates[-1] - start).days // 7) + 1

CELL = 13
GAP = 5
STEP = CELL + GAP

LEFT = 30
TOP = 45

WIDTH = LEFT + weeks * STEP + 30
HEIGHT = TOP + 7 * STEP + 25

BG = (25, 22, 42)

PURPLE = [
    (43, 35, 65),
    (85, 62, 120),
    (133, 89, 175),
    (184, 119, 220),
    (226, 163, 255)
]


# Tiny pixel cat
CAT_CLOSED = [
    "..L.L..",
    ".LLLLL.",
    "LWK.WKL",
    "LWWWWWL",
    "LW.P.WL",
    ".L...L.",
    "..LLL.."
]

CAT_OPEN = [
    "..L.L..",
    ".LLLLL.",
    "LWK.WKL",
    "LWWWWWL",
    "LW.O.WL",
    ".L...L.",
    "..LLL.."
]

CAT_COLORS = {
    "L": (177, 143, 224),
    "W": (255, 239, 250),
    "K": (43, 31, 60),
    "P": (235, 139, 190),
    "O": (235, 100, 170)
}


def draw_cat(draw, center_x, center_y, frame_no):
    # Alternate between closed and open mouth
    cat = CAT_OPEN if frame_no % 2 == 0 else CAT_CLOSED

    scale = 2
    cat_width = 7 * scale
    cat_height = 7 * scale

    x = center_x - cat_width // 2
    y = center_y - cat_height // 2

    for row, line in enumerate(cat):
        for col, pixel in enumerate(line):
            if pixel == ".":
                continue

            draw.rectangle(
                (
                    x + col * scale,
                    y + row * scale,
                    x + (col + 1) * scale - 1,
                    y + (row + 1) * scale - 1
                ),
                fill=CAT_COLORS[pixel]
            )


# Keep only days with actual contributions
active_dates = sorted(
    date.fromisoformat(day)
    for day, level in contributions.items()
    if level > 0
)

if not active_dates:
    raise RuntimeError("No contribution days found to eat!")


# Limit frames to keep the GIF reasonably small
MAX_FRAMES = 120

if len(active_dates) > MAX_FRAMES:
    target_dates = [
        active_dates[
            round(i * (len(active_dates) - 1) / (MAX_FRAMES - 1))
        ]
        for i in range(MAX_FRAMES)
    ]
else:
    target_dates = active_dates


frames = []

for frame_no, target_day in enumerate(target_dates):

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # All contributions up to the current target are eaten
    eaten_dates = set(
        day for day in active_dates if day < target_day
    )

    # Draw contribution graph, excluding eaten squares
    for day, level in contributions.items():

        current = date.fromisoformat(day)

        if current in eaten_dates:
            continue

        week = (current - start).days // 7
        weekday = current.weekday()

        x = LEFT + week * STEP
        y = TOP + weekday * STEP

        draw.rounded_rectangle(
            (x, y, x + CELL, y + CELL),
            radius=3,
            fill=PURPLE[min(level, 4)]
        )

    # Position cat on the current contribution
    week = (target_day - start).days // 7
    weekday = target_day.weekday()

    center_x = LEFT + week * STEP + CELL // 2
    center_y = TOP + weekday * STEP + CELL // 2

    draw_cat(draw, center_x, center_y, frame_no)

    frames.append(image)


# Add a final empty-graph frame before the loop restarts
final_image = Image.new("RGB", (WIDTH, HEIGHT), BG)
frames.append(final_image)


# Save animated GIF
os.makedirs("dist", exist_ok=True)

frames[0].save(
    "dist/cat-contributions.gif",
    save_all=True,
    append_images=frames[1:],
    duration=100,
    loop=0,
    optimize=True
)

print("Pixel cat finished eating the contribution graph!")
