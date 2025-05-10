import os
import re
import random
import aiofiles
import aiohttp

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps
from unidecode import unidecode
from youtubesearchpython.__future__ import VideosSearch

from EsproMusic import app
from config import YOUTUBE_IMG_URL


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


def clear(text):
    words = text.split(" ")
    title = ""
    for word in words:
        if len(title) + len(word) < 60:
            title += " " + word
    return title.strip()


async def get_thumb(videoid):
    if not os.path.exists("cache"):
        os.makedirs("cache")

    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            try:
                title = result["title"]
                title = re.sub("\W+", " ", title).title()
            except:
                title = "Unsupported Title"
            try:
                duration = result["duration"]
            except:
                duration = "Unknown Mins"
            try:
                channel = result["channel"]["name"]
            except:
                channel = "Unknown Artist"
            try:
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            except:
                thumbnail = None

        # Optional: fetch YouTube thumbnail for other use if needed
        if thumbnail:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumbnail) as resp:
                    if resp.status == 200:
                        f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                        await f.write(await resp.read())
                        await f.close()
            try:
                os.remove(f"cache/thumb{videoid}.png")
            except:
                pass

        # Load background image
        background = Image.open("EsproMusic/assets/Anand.png").convert("RGBA")
        draw = ImageDraw.Draw(background)

        # Load fonts
        try:
            title_font = ImageFont.truetype("EsproMusic/assets/font.ttf", 50)
            artist_font = ImageFont.truetype("EsproMusic/assets/font2.ttf", 40)
            time_font = ImageFont.truetype("EsproMusic/assets/font2.ttf", 35)
        except:
            title_font = ImageFont.load_default()
            artist_font = ImageFont.load_default()
            time_font = ImageFont.load_default()

        # Draw text
        draw.text((570, 160), clear(title), fill="white", font=title_font)     # Title
        draw.text((570, 230), channel, fill="white", font=artist_font)         # Artist
        draw.text((60, 620), "00:00", fill="white", font=time_font)            # Start time
        draw.text((1170, 620), duration[:7], fill="white", font=time_font)     # End time

        background.save(f"cache/{videoid}.png")
        return f"cache/{videoid}.png"

    except Exception as e:
        print(e)
        return YOUTUBE_IMG_URL
