
import os
import urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser

from PIL import Image, ImageDraw


# --------------------------------------------------
# 1. GET YOUR REAL GITHUB CONTRIBUTION DATA
# --------------------------------------------------

USERNAME = os.environ["GITHUB_USER"]

url = f"https://github.com/users/{USERNAME}/contributions"

request = urllib.request.Request(
    url,
    headers={"User-Agent": "Mozilla/5.0"}
)

with urllib.request.urlopen(request) as response:
    html = response.read().decode("utf-8")


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
    raise RuntimeError("No GitHub contribution data found.")

print(f"Loaded {len(contributions)} contribution days.")


# --------------------------------------------------
# 2. CONTRIBUTION GRAPH DESIGN
# --------------------------------------------------

dates = sorted(date.fromisoformat(d) for d in contributions)

start = dates[0] - timedelta(days=dates[0].weekday())
weeks = ((dates[-1] - start).days // 7) + 1

CELL = 13
GAP = 5
STEP = CELL + GAP

LEFT = 35
TOP = 45

WIDTH = LEFT + weeks * STEP + 35
HEIGHT = TOP + 7 * STEP + 30

BACKGROUND = (25, 22, 42)

PURPLE = [
    (43, 35, 65),
    (85, 62, 120),
    (133, 89, 175),
    (184, 119, 220),
    (226, 163, 255)
]


def get_position(day):
    current = date.fromisoformat(day)

    week = (current - start).days // 7
    weekday = current.weekday()

    x = LEFT + week * STEP + CELL // 2
    y = TOP + weekday * STEP + CELL // 2

    return x, y


# Only actual contribution days
active_dates = sorted(
    day for day, level in contributions.items()
    if level > 0
)

if not active_dates:
    raise RuntimeError("There are no contribution days for the cat to eat.")


# --------------------------------------------------
# 3. PIXEL CAT
# --------------------------------------------------

CAT_COLORS = {
    "L": (177, 143, 224),   # Lavender outline
    "W": (255, 239, 250),   # White fur
    "K": (43, 31, 60),      # Eyes
    "P": (235, 139, 190),   # Nose
    "O": (235, 100, 170),   # Open mouth
}

CAT_CLOSED = [
    "..L.....L..",
    ".LLL...LLL.",
    "LWWLLLLLWWL",
    "LWKWWWWKWLL",
    "LWWWWWWWWLL",
    ".LWWPWWWWL.",
    "..LWWWWLL..",
    "...LLLLL...",
    "..L.....L.."
]

CAT_OPEN = [
    "..L.....L..",
    ".LLL...LLL.",
    "LWWLLLLLWWL",
    "LWKWWWWKWLL",
    "LWWWWWWWWLL",
    ".LWWPOWWWL.",
    "..LWWWWLL..",
    "...LLLLL...",
    "..L.....L.."
]

CAT_WIDE = [
    "..L.....L..",
    ".LLL...LLL.",
    "LWWLLLLLWWL",
    "LWKWWWWKWLL",
    "LWWWWWWWWLL",
    ".LWWPOOWWL.",
    "..LWWWWLL..",
    "...LLLLL...",
    "..L.....L.."
]


def draw_cat(image, center_x, center_y, state, facing, walk_frame=0):
    sprite = Image.new("RGBA", (22, 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)

    patterns = {
        "walk": CAT_CLOSED,
        "closed": CAT_CLOSED,
        "open": CAT_OPEN,
        "wide": CAT_WIDE
    }

    pattern = patterns[state]

    scale = 2
    start_x = (22 - 11 * scale) // 2
    start_y = 0

    for row, line in enumerate(pattern):
        for col, pixel in enumerate(line):
            if pixel == ".":
                continue

            x = start_x + col * scale
            y = start_y + row * scale

            draw.rectangle(
                (x, y, x + scale - 1, y + scale - 1),
                fill=CAT_COLORS[pixel]
            )

    # Moving paws while walking
    if state == "walk":
        paw_shift = 1 if walk_frame % 2 else 0

        draw.rectangle(
            (6, 17 - paw_shift, 8, 19 - paw_shift),
            fill=CAT_COLORS["L"]
        )
        draw.rectangle(
            (14, 17 + paw_shift, 16, 19 + paw_shift),
            fill=CAT_COLORS["L"]
        )

    if facing < 0:
        sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    image.paste(
        sprite,
        (int(center_x - 11), int(center_y - 10)),
        sprite
    )


# --------------------------------------------------
# 4. DRAW THE GRAPH AND ANIMATION FRAME
# --------------------------------------------------

frames = []
palette = None


def add_frame(eaten, cat_position, state, facing=1, walk_frame=0,
              target_position=None, particle_frame=0):

    global palette

    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    # Draw every contribution that has not been eaten
    for day, level in contributions.items():

        if day in eaten:
            continue

        x, y = get_position(day)

        draw.rounded_rectangle(
            (
                x - CELL // 2,
                y - CELL // 2,
                x + CELL // 2,
                y + CELL // 2
            ),
            radius=3,
            fill=PURPLE[min(level, 4)]
        )

    # Small bite particles
    if target_position and particle_frame > 0:
        tx, ty = target_position

        particles = [
            (-9, -8),
            (8, -10),
            (10, 5),
            (-8, 9)
        ]

        for index, (dx, dy) in enumerate(particles):
            if index < particle_frame:
                draw.rectangle(
                    (
                        tx + dx,
                        ty + dy,
                        tx + dx + 3,
                        ty + dy + 3
                    ),
                    fill=(255, 190, 235)
                )

    # Draw the cat on top of the graph
    cx, cy = cat_position

    draw_cat(
        image,
        cx,
        cy,
        state,
        facing,
        walk_frame
    )

    # Use one shared palette to keep the GIF consistent
    if palette is None:
        palette = image.convert(
            "P",
            palette=Image.Palette.ADAPTIVE,
            colors=128
        )
        frames.append(palette)
    else:
        frames.append(image.quantize(palette=palette))


# --------------------------------------------------
# 5. WALK SMOOTHLY AND EAT CONTRIBUTIONS
# --------------------------------------------------

eaten = set()

first_x, first_y = get_position(active_dates[0])

# Cat starts just before the first contribution
previous_position = (first_x - 24, first_y)

for index, day in enumerate(active_dates):

    target_position = get_position(day)
    tx, ty = target_position

    px, py = previous_position

    facing = 1 if tx >= px else -1

    # Smooth movement between contribution squares
    movement_frames = 3

    for step in range(1, movement_frames + 1):

        progress = step / movement_frames

        x = px + (tx - px) * progress
        y = py + (ty - py) * progress

        add_frame(
            eaten,
            (x, y),
            "walk",
            facing,
            walk_frame=step
        )

    # Pause and chew the contribution
    for bite in ["closed", "open", "wide", "open"]:

        add_frame(
            eaten,
            target_position,
            bite,
            facing,
            target_position=target_position,
            particle_frame=1 if bite == "open" else 0
        )

    # Remove this contribution after the bite
    eaten.add(day)

    # Update cat position for next contribution
    previous_position = target_position

    if index % 25 == 0:
        print(f"Cat has eaten {index + 1}/{len(active_dates)} contributions.")


# --------------------------------------------------
# 6. FINISH AND RESTART THE LOOP
# --------------------------------------------------

last_position = get_position(active_dates[-1])

# Short pause after the final contribution is eaten
for _ in range(5):
    add_frame(
        eaten,
        last_position,
        "closed"
    )


# --------------------------------------------------
# 7. SAVE THE ANIMATED GIF
# --------------------------------------------------

os.makedirs("dist", exist_ok=True)

frames[0].save(
    "dist/cat-contributions.gif",
    save_all=True,
    append_images=frames[1:],
    duration=90,
    loop=0,
    optimize=True,
    disposal=2
)

print("Pixel cat finished eating!")
print(f"Total contribution days eaten: {len(active_dates)}")
print("GIF saved to dist/cat-contributions.gif")
