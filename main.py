from PIL import Image, ImageDraw, ImageFont
import os
import tweepy
from dotenv import load_dotenv

# Load secrets
load_dotenv()

# Dummy alert info (used for test)
alert_type = "Tornado Warning"
affected_area = "Fulton, DeKalb, Gwinnett"
expires = "Expires: 5:15 PM EDT"

# Create canvas
canvas = Image.new("RGB", (800, 700), (30, 30, 30))
draw = ImageDraw.Draw(canvas)

# Fonts
from PIL import ImageFont

try:
    font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
    font_med = ImageFont.truetype("DejaVuSans.ttf", 22)
    font_small = ImageFont.truetype("DejaVuSans.ttf", 18)
except:
    font_large = ImageFont.load_default()
    font_med = ImageFont.load_default()
    font_small = ImageFont.load_default()


# Top Banner
draw.rectangle([0, 0, 800, 80], fill=(200, 0, 0))
bbox = draw.textbbox((0, 0), alert_type, font=font_large)
title_w = bbox[2] - bbox[0]
draw.text(((800 - title_w) / 2, 20), alert_type, fill="white", font=font_large)

# Fake map image block
draw.rectangle([0, 100, 800, 500], fill=(50, 50, 70))
draw.text((300, 300), "Radar Placeholder", fill="white", font=font_med)

# Alert info
draw.text((20, 520), f"Affected Area: {affected_area}", fill="white", font=font_med)
draw.text((20, 550), expires, fill="white", font=font_med)

# Dummy badge
badge_text = "💨 70 MPH Winds"
badge_w = 200
badge_h = 40
badge = Image.new("RGB", (badge_w, badge_h), (255, 200, 0))
badge_draw = ImageDraw.Draw(badge)
badge_draw.rectangle([0, 0, badge_w, badge_h], fill=(255, 215, 0))
badge_draw.text((10, 10), badge_text, fill="black", font=font_small)
canvas.paste(badge, (20, 590))

# Footer
footer = "NORTH GEORGIA WEATHER COMMAND"
bbox = draw.textbbox((0, 0), footer, font=font_small)
footer_w = bbox[2] - bbox[0]
draw.text(((800 - footer_w) / 2, 660), footer, fill="white", font=font_small)

# Save
filename = "test_tornado_warning.png"
canvas.save(filename)
print(f"✅ Test graphic saved: {filename}")

# --- Twitter Post Test ---
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
api = tweepy.API(auth)

tweet = f"[TEST] {alert_type} for {affected_area.split(',')[0]}... {expires}"

try:
    media = api.media_upload(filename)
api.update_status(status=tweet, media_ids=[media.media_id])
    print("✅ Posted test graphic to Twitter.")
except Exception as e:
    print(f"❌ Twitter post failed: {e}")
