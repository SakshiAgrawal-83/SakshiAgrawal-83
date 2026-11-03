
import os
import re
import urllib.request
from datetime import date, timedelta
from PIL import Image, ImageDraw

USERNAME = os.environ["GITHUB_USER"]

url = f"https://github.com/users/{USERNAME}/contributions"

request = urllib.request.Request(
    url,
    headers={"User-Agent": "GitHub-Pixel-Cat"}
)

with urllib.request.urlopen(request) as response:
    svg = response.read().decode("utf-8")

contributions = {}

for tag in re.findall(r"<rect\b[^>]*>", svg):
    d = re.search(r'data-date="([^"]+)"', tag)
    level = re.search(r'data-level="([^"]+)"', tag)

    if d and level:
        contributions[d.group(1)] = int(level.group(1))

if not contributions:
    raise RuntimeError("No contribution data found.")

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

            if row >= 9 and frame % 2:
                if row == 9:
                    col += 1
                elif row == 10:
                    col -= 1

            draw.rectangle(
                (
                    x + col * scale,
                    y + row * scale,
                    x + (col + 1) * scale - 1,
                    y + (row + 1) * scale - 1
                ),
                fill=COLORS[pixel]
            )

frames = []

cat_width = 14 * 3
total_frames = 53

for frame_no in range(total_frames):

    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # Draw actual contribution calendar
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

    # Cat walking above contribution calendar
    travel = max(1, WIDTH - cat_width - 40)
    cat_x = 20 + int(
        travel * frame_no / (total_frames - 1)
    )

    cat_y = 8 + (frame_no % 2) * 2

    draw_cat(draw, cat_x, cat_y, frame_no)

    # Paw prints behind the cat
    for paw in range(3):
        px = cat_x - 12 - paw * 15
        py = 43 + (paw % 2) * 3

        draw.ellipse(
            (px, py, px + 4, py + 4),
            fill=(147, 112, 190)
        )

    frames.append(image)

os.makedirs("dist", exist_ok=True)

frames[0].save(
    "dist/cat-contributions.gif",
    save_all=True,
    append_images=frames[1:],
    duration=120,
    loop=0,
    optimize=True
)

print("Pixel cat contribution animation generated!")

