
import os
import re
import urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser

from PIL import Image, ImageDraw


# Get GitHub username
USERNAME = os.environ["GITHUB_USER"]

# Fetch GitHub contribution page
url = f"https://github.com/users/{USERNAME}/contributions"

request = urllib.request.Request(
    url,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(request) as response:
    html = response.read().decode("utf-8")


# Extract contribution dates and levels from HTML
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
    raise RuntimeError(
        "No contribution data found. GitHub may have changed its page format "
        "or blocked the request."
    )

print(f"Found {len(contributions)} contribution days.")


# Calculate contribution graph dimensions
dates = sorted(date.fromisoformat(d) for d in contributions)

start = dates[0] - timedelta(days=dates[0].weekday())
weeks = ((dates[-1] - start).days // 7) + 1

CELL = 13
GAP = 5
STEP = CELL + GAP

LEFT = 30
TOP = 65

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


# Pixel cat design
CAT = [
    "....LLL.......",
    "...LWWLWL......",
    "...LWLWLL......",
    "..LLLLLLLLL....",
    ".LWWWWWWWWWL...",
    ".LWWKWWKWWWL...",
    ".LWWWWWWWWWL...",
    "..LWWWPWWWL....",
    "...LLLLLLL.....",
    "...L..L..L.....",
    "..LL..LL..LL...",
    "..............."
]

COLORS = {
    "L": (177, 143, 224),
    "W": (255, 239, 250),
    "K": (43, 31, 60),
    "P": (235, 139, 190)
}


def draw_cat(draw, x, y, frame):
    scale = 3

    for row, line in enumerate(CAT):
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
                fill=COLORS[pixel]
            )


# Generate animation frames
frames = []

cat_width = 14 * 3
total_frames = 53

for frame_no in range(total_frames):

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # Draw contribution graph
    for day, level in contributions.items():

        current = date.fromisoformat(day)

        week = (current - start).days // 7
        weekday = current.weekday()

        x = LEFT + week * STEP
        y = TOP + weekday * STEP

        draw.rounded_rectangle(
            (x, y, x + CELL, y + CELL),
            radius=3,
            fill=PURPLE[min(level, 4)]
        )

    # Move cat across the graph
    travel = max(1, WIDTH - cat_width - 40)

    cat_x = 20 + int(
        travel * frame_no / (total_frames - 1)
    )

    cat_y = 8 + (frame_no % 2) * 2

    draw_cat(draw, cat_x, cat_y, frame_no)

    # Paw prints
    for paw in range(3):
        px = cat_x - 12 - paw * 15
        py = 43 + (paw % 2) * 3

        draw.ellipse(
            (px, py, px + 4, py + 4),
            fill=(147, 112, 190)
        )

    frames.append(image)


# Save GIF
os.makedirs("dist", exist_ok=True)

frames[0].save(
    "dist/cat-contributions.gif",
    save_all=True,
    append_images=frames[1:],
    duration=120,
    loop=0,
    optimize=True
)

print("Pixel cat contribution animation generated successfully!")
