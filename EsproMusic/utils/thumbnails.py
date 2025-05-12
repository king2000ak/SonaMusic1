import asyncio
import os
import re
import random
from io import BytesIO

import aiofiles
import aiohttp
import httpx
from PIL import (
    Image, ImageDraw, ImageEnhance, ImageFilter,
    ImageFont, ImageOps
)
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL


FONTS = {
    "cfont": ImageFont.truetype("EsproMusic/assets/cfont.ttf", 15),
    "dfont": ImageFont.truetype("EsproMusic/assets/font2.ttf", 12),
    "nfont": ImageFont.truetype("EsproMusic/assets/font.ttf", 10),
    "tfont": ImageFont.truetype("EsproMusic/assets/font.ttf", 20),
}


def resize_youtube_thumbnail(img: Image.Image) -> Image.Image:
    target_size = 640
    aspect_ratio = img.width / img.height
    if aspect_ratio > 1:
        new_width = int(target_size * aspect_ratio)
        new_height = target_size
    else:
        new_width = target_size
        new_height = int(target_size / aspect_ratio)

    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    left = (img.width - target_size) // 2
    top = (img.height - target_size) // 2
    return img.crop((left, top, left + target_size, top + target_size))


def make_sq(image: Image.Image, size: int = 125) -> Image.Image:
    side = min(image.size)
    cropped = image.crop((
        (image.width - side) // 2,
        (image.height - side) // 2,
        (image.width + side) // 2,
        (image.height + side) // 2
    ))
    resized = cropped.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size, size), 30, fill=255)
    rounded = ImageOps.fit(resized, (size, size))
    rounded.putalpha(mask)
    return rounded


def clean_text(text: str, limit: int = 17) -> str:
    text = text.strip()
    return f"{text[:limit - 3]}..." if len(text) > limit else text


def add_controls(img: Image.Image) -> Image.Image:
    img = img.filter(ImageFilter.GaussianBlur(25))
    box = (120, 120, 520, 480)
    region = img.crop(box)
    dark_region = ImageEnhance.Brightness(region).enhance(0.5)

    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, box[2] - box[0], box[3] - box[1]), 40, fill=255)
    controls = Image.open("EsproMusic/assets/controls.png").convert("RGBA")

    img.paste(dark_region, box, mask)
    img.paste(controls, (135, 305), controls)
    return img


def get_duration(duration: int, time: str = "0:24") -> str:
    try:
        total = duration
        current = sum(int(x) * 60**i for i, x in enumerate(reversed(time.split(":"))))
        remaining = max(total - current, 0)
        return f"{remaining // 60}:{remaining % 60:02}"
    except:
        return "0:00"


async def fetch_image(url: str) -> Image.Image | None:
    if not url:
        return None
    try:
        async with httpx.AsyncClient() as client:
            if "mzstatic.com" in url:
                url = url.replace("500x500bb.jpg", "600x600bb.jpg")
            response = await client.get(url, timeout=5)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGBA")
            if "ytimg.com" in url:
                img = resize_youtube_thumbnail(img)
            return img
    except Exception as e:
        print(f"Image error: {e}")
        return None


async def gen_thumb(track_id: str, title: str, artist: str, thumbnail_url: str, duration: int) -> str:
    save_path = f"cache/{track_id}.png"
    if os.path.exists(save_path):
        return save_path

    title = clean_text(title)
    artist = clean_text(artist or "Unknown")
    thumb = await fetch_image(thumbnail_url)
    if not thumb:
        return YOUTUBE_IMG_URL

    bg = add_controls(thumb)
    image = make_sq(thumb)
    bg.paste(image, (145, 155), image)

    draw = ImageDraw.Draw(bg)
    draw.text((285, 180), "EsproMusic", (192, 192, 192), font=FONTS["nfont"])
    draw.text((285, 200), title, (255, 255, 255), font=FONTS["tfont"])
    draw.text((287, 235), artist, (255, 255, 255), font=FONTS["cfont"])
    draw.text((478, 321), get_duration(duration), (192, 192, 192), font=FONTS["dfont"])

    await asyncio.to_thread(bg.save, save_path)
    return save_path if os.path.exists(save_path) else YOUTUBE_IMG_URL


async def get_thumb(videoid: str) -> str:
    if os.path.isfile(f"cache/{videoid}.png"):
        return f"cache/{videoid}.png"

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        result = (await results.next())["result"][0]
        title = re.sub(r"\W+", " ", result.get("title", "Unknown Title")).title()
        duration_str = result.get("duration", "0:00")
        duration_sec = sum(int(x) * 60 ** i for i, x in enumerate(reversed(duration_str.split(":"))))
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        channel = result.get("channel", {}).get("name", "Unknown")

        return await gen_thumb(videoid, title, channel, thumbnail, duration_sec)
    except Exception as e:
        print(f"Thumbnail error: {e}")
        return YOUTUBE_IMG_URL
