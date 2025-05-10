from pyrogram.types import InlineKeyboardButton

import config
from EsproMusic import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],  
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            
            InlineKeyboardButton(text="「 ✦ 𝐂𝐋𝐈𝐂𝐊 ✦ 」", url=f"https://t.me/Anand_Feelings"),
        ],
        
    ]
    return buttons
