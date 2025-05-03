import requests
import tweepy
import schedule
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

NWS_ENDPOINT = "https://api.weather.gov/alerts/active?office=FFC"
POSTED_ALERTS_FILE = "posted_alerts.txt"

# Twitter API credentials
TWITTER_API_KEY = 'LezDMtw4MjNX96X2lTMQk4a57'
TWITTER_API_SECRET = 'tlL9TihgjkqaWTLA6hz3nvXnVtttoF1coWIrMXQKYkdmz9ePC0'
TWITTER_ACCESS_TOKEN = '1874272473732325376-80cunmDCB8ykmajxt0npoHztHlKW3s'
TWITTER_ACCESS_SECRET = 'Rowk4vksfc64VKWrmA9Ao9alUnLM171IBg3BITnaBJDoA'

# Facebook API endpoint and token
#FB_PAGE_TOKEN = "YOUR_FB_PAGE_TOKEN"
#FB_PAGE_ID = "YOUR_FB_PAGE_ID"
#FB_API_URL = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"

# Twitter client
auth = tweepy.OAuth1UserHandler(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
twitter = tweepy.API(auth)

def load_posted_alerts():
    try:
        with open(POSTED_ALERTS_FILE, 'r') as f:
            return set(f.read().splitlines())
    except FileNotFoundError:
        return set()

def save_posted_alert(alert_id):
    with open(POSTED_ALERTS_FILE, 'a') as f:
        f.write(alert_id + '\n')

def generate_image(alert):
    image = Image.new('RGB', (800, 400), color=(30, 30, 70))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    draw.text((10, 10), f"{alert['event']} Issued", fill="white", font=font)
    draw.text((10, 40), alert['headline'], fill="white", font=font)
    draw.text((10, 80), alert['description'][:500], fill="white", font=font)

    image_path = f"alert_{alert['id']}.png"
    image.save(image_path)
    return image_path

def post_to_twitter(image_path, alert):
    twitter.update_with_media(image_path, status=f"{alert['event']} - {alert['headline']}")

def post_to_facebook(image_path, alert):
    with open(image_path, 'rb') as img:
        payload = {
            'access_token': FB_PAGE_TOKEN,
            'caption': f"{alert['event']} - {alert['headline']}",
        }
        files = {'source': img}
        requests.post(FB_API_URL, data=payload, files=files)

def check_for_new_alerts():
    posted_alerts = load_posted_alerts()
    response = requests.get(NWS_ENDPOINT).json()

    for alert in response['features']:
        alert_id = alert['id']
        alert_data = alert['properties']
        event = alert_data['event']

        if alert_id not in posted_alerts and "Warning" in event:
            print(f"New alert found: {event}")
            image_path = generate_image(alert_data)
            post_to_twitter(image_path, alert_data)
            post_to_facebook(image_path, alert_data)
            save_posted_alert(alert_id)

# Run every 60 seconds
schedule.every(60).seconds.do(check_for_new_alerts)

print("🚨 Weather alert bot is now running...")
while True:
    schedule.run_pending()
    time.sleep(1)
