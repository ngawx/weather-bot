import tweepy
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import datetime
from dotenv import load_dotenv
import os
import re

load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

# Allowed alert types
ALLOWED_ALERTS = [
    "Tornado Warning", "Tornado Watch",
    "Severe Thunderstorm Warning", "Severe Thunderstorm Watch",
    "Flood Warning", "Flood Watch",
    "Heat Advisory", "Excessive Heat Warning", "Excessive Heat Watch",
    "Winter Storm Warning", "Winter Storm Watch", "Winter Weather Advisory",
    "Wind Chill Warning", "Wind Chill Advisory",
    "Freeze Warning", "Freeze Watch",
    "Ice Storm Warning"
]

# Get active alerts from NWS Peachtree City
url = "https://api.weather.gov/alerts/active?office=FFC"
resp = requests.get(url).json()
alerts = [a for a in resp.get("features", []) if a["properties"]["event"] in ALLOWED_ALERTS]

if not alerts:
    print("🚫 No relevant active alerts from NWS Peachtree City.")
    exit()

# Use most recent relevant alert
alert = alerts[0]
props = alert["properties"]
alert_type = props["event"]
description = props.get("description", "")
instruction = props.get("instruction", "")
text_block = f"{description}\n{instruction}"

affected_area = props["areaDesc"]
expires_raw = props["expires"]
expires = datetime.datetime.strptime(expires_raw, "%Y-%m-%dT%H:%M:%S%z").astimezone().strftime("Expires: %I:%M %p %Z")

# Get polygon
polygon = alert.get("geometry", {}).get("coordinates")
if not polygon:
    print("⚠️ No polygon available.")
    exit()

flat_coords = polygon[0]
path_coords = ",".join([f"{lon},{lat}" for lon, lat in flat_coords])
lons, lats = zip(*flat_coords)
center_lon = sum(lons) / len(lons)
center_lat = sum(lats) / len(lats)

# Build Mapbox URL
path_overlay = f"path-5+ff0000-0.8({path_coords})"
mapbox_url = (
    f"https://api.mapbox.com/styles/v1/mapbox/light-v10/static/"
    f"{path_overlay}/{center_lon},{center_lat},8/800x400?access_token={MAPBOX_TOKEN}"
)

# Download radar map image
map_img = Image.open(BytesIO(requests.get(mapbox_url).content))

# Create canvas
canvas = Image.new("RGB", (800, 700), (20, 20, 20))
canvas.paste(map_img, (0, 100))
draw = ImageDraw.Draw(canvas)

# Fonts
font_large = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", 36)
font_med = ImageFont.truetype("/Library/Fonts/Arial.ttf", 22)
font_small = ImageFont.truetype("/Library/Fonts/Arial.ttf", 18)

# Banner
banner_color = (200, 0, 0) if "Tornado" in alert_type else (255, 204, 0)
draw.rectangle([0, 0, 800, 80], fill=banner_color)
title_w, _ = draw.textsize(alert_type, font=font_large)
draw.text(((800 - title_w) / 2, 20), alert_type, fill="white", font=font_large)

# Alert info
draw.text((20, 520), f"Affected Area: {affected_area}", fill="white", font=font_med)
draw.text((20, 550), expires, fill="white", font=font_med)

# --- Threat Parser ---
def parse_threats(text):
    threats = []

    if "tornado possible" in text.lower():
        threats.append(("🚩 Tornado Possible", (255, 0, 0), (255, 100, 100)))

    wind = re.search(r"(\d{2,3})\s?mph", text)
    if wind:
        mph = wind.group(1)
        threats.append((f"💨 {mph} MPH Winds", (255, 215, 0), (255, 240, 180)))

    hail = re.search(r"hail.*?(\d+\.\d+|\d+)\"?", text.lower())
    if hail:
        hail_size = hail.group(1)
        threats.append((f"🧊 {hail_size}\" Hail", (135, 206, 250), (185, 235, 255)))

    motion = re.search(r"moving (.*?)(\d+)\s?mph", text.lower())
    if motion:
        direction = motion.group(1).strip().upper()
        speed = motion.group(2)
        threats.append((f"➡️ Moving {direction} @ {speed} MPH", (144, 238, 144), (200, 255, 200)))

    heat = re.search(r"heat index.*?(\d+)", text.lower())
    if heat:
        index = heat.group(1)
        threats.append((f"🔥 Heat Index {index}°", (255, 102, 0), (255, 178, 102)))

    chill = re.search(r"wind chill.*?(\d+)", text.lower())
    if chill:
        wc = chill.group(1)
        threats.append((f"❄️ Wind Chill {wc}°", (100, 149, 237), (173, 216, 230)))

    ice = re.search(r"ice accumulation.*?(\d+\.\d+|\d+)", text.lower())
    if ice:
        ice_amt = ice.group(1)
        threats.append((f"🧊 Ice {ice_amt}\"", (190, 190, 255), (220, 220, 255)))

    return threats

threat_badges = parse_threats(text_block)

# --- Draw Gradient Badges ---
def draw_badge(x, y, w, h, start_color, end_color, text):
    badge = Image.new("RGB", (w, h))
    bdraw = ImageDraw.Draw(badge)
    for i in range(w):
        r = int(start_color[0] + (end_color[0] - start_color[0]) * i / w)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * i / w)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * i / w)
        bdraw.line([(i, 0), (i, h)], fill=(r, g, b))
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, w, h], radius=15, fill=255)
    canvas.paste(badge, (x, y), mask)
    text_w, _ = draw.textsize(text, font=font_small)
    draw.text((x + (w - text_w) / 2, y + 8), text, fill="black", font=font_small)

# --- Draw All Threat Badges ---
badge_x = 20
badge_y = 590
badge_w = 180
badge_h = 40
gap = 20

for i, (text, c1, c2) in enumerate(threat_badges):
    draw_badge(badge_x + i * (badge_w + gap), badge_y, badge_w, badge_h, c1, c2, text)

# Footer
footer_text = "NORTH GEORGIA WEATHER COMMAND"
footer_w, _ = draw.textsize(footer_text, font=font_small)
draw.text(((800 - footer_w) / 2, 660), footer_text, fill="white", font=font_small)

# Save image
filename = f"nws_alert_{alert_type.replace(' ', '_')}.png"
canvas.save(filename)
print(f"✅ Alert graphic saved: {filename}")

# --- Post to Twitter ---
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

auth = tweepy.OAuth1UserHandler(
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_SECRET
)
twitter_api = tweepy.API(auth)

# Shorten affected area in case it's too long for a tweet
short_area = affected_area.split(",")[0] + " and nearby areas"
tweet_text = f"{alert_type} issued for {short_area}. {expires}"

try:
    twitter_api.update_with_media(filename, status=tweet_text)
    print("✅ Posted to Twitter.")
except Exception as e:
    print(f"❌ Twitter post failed: {e}")
