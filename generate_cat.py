import os
import sys
import urllib.request
from datetime import date, timedelta
from html.parser import HTMLParser
from math import ceil, hypot

from PIL import Image, ImageDraw


# --------------------------------------------------
# 1. GET YOUR REAL GITHUB CONTRIBUTION DATA
# --------------------------------------------------
# MY_GITHUB_USERNAME = "SakshiAgrawal-83"  
USERNAME = os.environ.get("GITHUB_USER") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not USERNAME:
    raise SystemExit("Set GITHUB_USER or pass your username: python cat_contributions.py yourname")

url = f"https://github.com/users/{USERNAME}/contributions"
request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

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
    raise RuntimeError("No GitHub contribution data found. Check the username.")

print(f"Loaded {len(contributions)} contribution days for {USERNAME}.")


# --------------------------------------------------
# 2. CONTRIBUTION GRAPH LAYOUT (GitHub style: weeks start on Sunday)
# --------------------------------------------------

def row_of(d):
    """Row in the graph: Sunday = 0 ... Saturday = 6."""
    return (d.weekday() + 1) % 7


dates = sorted(date.fromisoformat(d) for d in contributions)

start = dates[0] - timedelta(days=row_of(dates[0]))
weeks = ((dates[-1] - start).days // 7) + 1

CELL = 13
GAP = 5
STEP = CELL + GAP

LEFT = 55
TOP = 50

WIDTH = LEFT + weeks * STEP + 55
HEIGHT = TOP + 7 * STEP + 35

BACKGROUND = (25, 22, 42)

PURPLE = [
    (43, 35, 65),
    (85, 62, 120),
    (133, 89, 175),
    (184, 119, 220),
    (226, 163, 255),
]


def get_position(day):
    current = date.fromisoformat(day)
    week = (current - start).days // 7
    row = row_of(current)
    x = LEFT + week * STEP + CELL // 2
    y = TOP + row * STEP + CELL // 2
    return x, y


# Only days that actually have contributions get eaten
active_days = [day for day, level in contributions.items() if level > 0]

if not active_days:
    raise RuntimeError("There are no contribution days for the cat to eat.")


# --------------------------------------------------
# 3. THE CUTE PIXEL CAT
# --------------------------------------------------

CAT_COLORS = {
    "L": (177, 143, 224),   # lavender outline
    "W": (255, 244, 250),   # fluffy white fur
    "P": (255, 170, 205),   # inner ears
    "K": (43, 31, 60),      # eyes / happy eyes
    "S": (255, 255, 255),   # eye sparkle
    "B": (255, 150, 190),   # rosy blush
    "N": (235, 110, 160),   # nose
    "M": (150, 40, 90),     # inside of mouth
    "T": (255, 120, 150),   # tongue
    "H": (200, 180, 230),   # whiskers
}
HEART_COLOR = (255, 130, 175)

S = 2          # pixel scale
OX = 2         # left margin in the grid (room for whiskers)
GRID_W, GRID_H = 19, 14

# 15 x 12 head (ears, face, chin)
HEAD = [
    "..LL.......LL..",
    ".LPPL.....LPPL.",
    ".LPPWLLLLLWPPL.",
    ".LWWWWWWWWWWWL.",
    "LWWWWWWWWWWWWWL",
    "LWWWWWWWWWWWWWL",
    "LWWWWWWWWWWWWWL",
    "LWWWWWWWWWWWWWL",
    "LWWWWWWWWWWWWWL",
    ".LWWWWWWWWWWWL.",
    "..LLWWWWWWWLL..",
    "....LLLLLLL....",
]


def make_cat_grid(eyes, mouth, paws):
    grid = [["." for _ in range(GRID_W)] for _ in range(GRID_H)]

    def put(r, c, ch):
        grid[r][c + OX] = ch

    for r, line in enumerate(HEAD):
        for c, ch in enumerate(line):
            if ch != ".":
                put(r, c, ch)

    # eyes
    if eyes == "open":
        for c in (3, 4, 10, 11):
            for r in (4, 5, 6):
                put(r, c, "K")
        put(4, 3, "S")      # sparkle in the eyes
        put(4, 10, "S")
    else:  # happy ^ ^
        for c0 in (2, 10):
            put(6, c0, "K")
            put(5, c0 + 1, "K")
            put(6, c0 + 2, "K")

    # blush + nose
    for c in (1, 2, 12, 13):
        put(7, c, "B")
    put(7, 7, "N")

    # whiskers
    for r in (7, 9):
        for c in (-2, -1, 15, 16):
            put(r, c, "H")

    # mouth
    if mouth == "closed":
        put(8, 6, "M")
        put(9, 7, "M")
        put(8, 8, "M")
    elif mouth == "open":
        for c in (6, 7, 8):
            put(8, c, "M")
            put(9, c, "M")
    elif mouth == "wide":
        for c in range(5, 10):
            put(8, c, "M")
            put(9, c, "M")
        for c in (6, 7, 8):
            put(10, c, "M")
            put(9, c, "T")   # little tongue

    # paws
    for c0 in (2, 9):
        lifted = (paws == 1 and c0 == 2)   # left paw lifted while walking
        for i in range(4):
            if lifted:
                put(12, c0 + i, "L")
            else:
                put(12, c0 + i, "W" if i in (1, 2) else "L")
                put(13, c0 + i, "L")

    return grid


_sprite_cache = {}


def get_sprite(eyes, mouth, paws, facing):
    key = (eyes, mouth, paws, facing)
    if key in _sprite_cache:
        return _sprite_cache[key]

    grid = make_cat_grid(eyes, mouth, paws)
    sprite = Image.new("RGBA", (GRID_W * S, GRID_H * S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(sprite)
    for r, row in enumerate(grid):
        for c, ch in enumerate(row):
            if ch == ".":
                continue
            draw.rectangle(
                (c * S, r * S, c * S + S - 1, r * S + S - 1),
                fill=CAT_COLORS[ch] + (255,),
            )
    if facing < 0:
        sprite = sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

    _sprite_cache[key] = sprite
    return sprite


# The cat's (cx, cy) is the centre of its MOUTH.
MOUTH_X = (OX + 7.5) * S   # 19
MOUTH_Y = 8.5 * S          # 17


def draw_cat(image, cx, cy, eyes, mouth, facing, paws, bob):
    sprite = get_sprite(eyes, mouth, paws, facing)
    image.paste(sprite, (int(cx - MOUTH_X), int(cy - MOUTH_Y + bob)), sprite)


HEART = [
    ".X.X.",
    "XXXXX",
    ".XXX.",
    "..X..",
]


def draw_heart(draw, cx, cy, rise):
    x0 = int(cx - 5)
    y0 = int(cy - MOUTH_Y - 10 - rise * 3)
    for r, line in enumerate(HEART):
        for c, ch in enumerate(line):
            if ch == "X":
                draw.rectangle(
                    (x0 + c * 2, y0 + r * 2, x0 + c * 2 + 1, y0 + r * 2 + 1),
                    fill=HEART_COLOR,
                )


def draw_cell(draw, x, y, color, size):
    half = size / 2
    draw.rounded_rectangle(
        (x - half, y - half, x + half, y + half),
        radius=min(3, size // 3),
        fill=color,
    )


# --------------------------------------------------
# 4. ANIMATION FRAMES
# --------------------------------------------------

# One fixed palette so every frame has identical, exact colours
_all_colors = [BACKGROUND] + PURPLE + list(CAT_COLORS.values()) + [HEART_COLOR]
_flat = [v for color in _all_colors for v in color]
_flat += [0] * (768 - len(_flat))
PALETTE_IMG = Image.new("P", (1, 1))
PALETTE_IMG.putpalette(_flat)

frames = []


def add_frame(eaten, cat, eyes="open", mouth="closed", facing=1,
              paws=0, bob=0, bite=None, heart=0):
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    flying = bite[0] if bite else None

    # every commit that has not been eaten yet
    for day, level in contributions.items():
        if day in eaten or day == flying:
            continue
        x, y = get_position(day)
        draw_cell(draw, x, y, PURPLE[min(level, 4)], CELL)

    draw_cat(image, cat[0], cat[1], eyes, mouth, facing, paws, bob)

    if heart:
        draw_heart(draw, cat[0], cat[1], heart)

    # the commit being swallowed: slides into the mouth and shrinks
    if bite:
        day, p = bite
        if p < 1:
            tx, ty = get_position(day)
            x = tx + (cat[0] - tx) * p
            y = ty + (cat[1] - ty) * p
            size = max(3, round(CELL * (1 - 0.75 * p)))
            draw_cell(draw, x, y, PURPLE[min(contributions[day], 4)], size)

    frames.append(image.quantize(palette=PALETTE_IMG, dither=Image.Dither.NONE))


# --------------------------------------------------
# 5. WALK ROW BY ROW AND EAT EVERY COMMIT
# --------------------------------------------------

DISTANCE = 24        # how far in front of the commit the cat stops
WALK_SPEED = 10      # pixels per walking frame
MAX_WALK = 10

# (eyes, mouth, how far the commit has travelled into the mouth)
EAT_STEPS = [
    ("open", "open", 0.0),    # mouth opens
    ("open", "wide", 0.4),    # commit floats in
    ("open", "wide", 0.75),
    ("happy", "open", 1.0),   # gulp!
    ("happy", "closed", None),  # mouth closes, nom nom
    ("happy", "closed", None),
]

# Snake pattern: left->right on one row, right->left on the next
order = []
for r in range(7):
    row_days = sorted(d for d in active_days if row_of(date.fromisoformat(d)) == r)
    if r % 2:
        row_days.reverse()
    order.extend(row_days)

eaten = set()

first = order[0]
fx, fy = get_position(first)
prev = (fx - DISTANCE, fy)

# short intro: full graph + waiting cat
for _ in range(6):
    add_frame(eaten, prev, "open", "closed", 1)

facing = 1
for index, day in enumerate(order):
    tx, ty = get_position(day)
    facing = 1 if row_of(date.fromisoformat(day)) % 2 == 0 else -1
    dest = (tx - facing * DISTANCE, ty)

    # walk (little bounce + paw wiggle)
    dist = hypot(dest[0] - prev[0], dest[1] - prev[1])
    n = min(MAX_WALK, max(2, ceil(dist / WALK_SPEED)))
    for s in range(1, n + 1):
        p = s / n
        pos = (prev[0] + (dest[0] - prev[0]) * p,
               prev[1] + (dest[1] - prev[1]) * p)
        add_frame(eaten, pos, "open", "closed", facing,
                  paws=s % 2, bob=-1 if s % 2 else 0)

    # open mouth -> eat the commit -> close mouth
    for step, (eyes, mouth, p) in enumerate(EAT_STEPS):
        bite = (day, p) if p is not None else None
        heart = 0
        if p is None:
            heart = step - 3          # little heart while chewing
        add_frame(eaten, dest, eyes, mouth, facing,
                  bob=-1 if step == 5 else 0, bite=bite, heart=heart)
        if p == 1.0:
            eaten.add(day)

    prev = dest

    if index % 25 == 0:
        print(f"Cat has eaten {index + 1}/{len(order)} contributions.")


# --------------------------------------------------
# 6. HAPPY ENDING, THEN LOOP
# --------------------------------------------------

for k in range(12):
    add_frame(eaten, prev, "happy", "closed", facing,
              bob=-1 if k % 2 else 0, heart=(k % 4) + 1)


# --------------------------------------------------
# 7. SAVE THE GIF
# --------------------------------------------------

os.makedirs("dist", exist_ok=True)

frames[0].save(
    "dist/cat-contributions.gif",
    save_all=True,
    append_images=frames[1:],
    duration=70,
    loop=0,
    disposal=1,   # keep frames so Pillow can store only the changed pixels
)

size_mb = os.path.getsize("dist/cat-contributions.gif") / 1_000_000
print("Pixel cat finished eating!")
print(f"Total contribution days eaten: {len(order)}")
print(f"GIF saved to dist/cat-contributions.gif ({size_mb:.1f} MB)")
