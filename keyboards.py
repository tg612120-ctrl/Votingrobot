from aiogram.types import InlineKeyboardMarkup as M, InlineKeyboardButton as B
import utils


def main_menu():
    return M(inline_keyboard=[
        [B(text="🎁 New Giveaway", callback_data="new"), B(text="📋 My Giveaways", callback_data="mg")],
        [B(text="📖 How to Use", callback_data="howto")],
        [B(text="📊 My Channels", callback_data="mych"), B(text="➕ Add Channel", callback_data="addch")],
    ])


def back(cb="menu"):
    return M(inline_keyboard=[[B(text="⬅️ Back", callback_data=cb)]])


def cancel():
    return M(inline_keyboard=[[B(text="❌ Cancel", callback_data="cancel")]])


def link_btn(text, url):
    return M(inline_keyboard=[[B(text=text, url=url)]])


def yes_no(yes, no):
    return M(inline_keyboard=[[B(text="✅ Yes", callback_data=yes), B(text="❌ No", callback_data=no)]])


def force_kb(items):
    rows = [[B(text=f"📢 {c['title']}", url=c["link"])] for c in items]
    rows.append([B(text="✅ I've Joined", callback_data="fj")])
    return M(inline_keyboard=rows)


def post_kb(g, p):
    rows = []
    if g.get("ch_link"):
        rows.append([B(text="📢 Join", url=g["ch_link"])])
    rows.append([B(text=f"🗳️ Vote ({p['votes']})", callback_data=f"v:{g['_id']}:{p['user_id']}")])
    if g.get("pbtn"):
        rows.append([B(text="🎉 Participate Now", url=utils.gw_link(g["_id"]))])
    return M(inline_keyboard=rows)


def panel_kb(g):
    gw = g["_id"]
    return M(inline_keyboard=[
        [B(text="🏆 Leaderboard", callback_data=f"lb:{gw}")],
        [B(text="⛔ Stop Participation" if g["open"] else "▶️ Resume Participation", callback_data=f"tp:{gw}")],
        [B(text="🏁 End Giveaway", callback_data=f"end:{gw}")],
        [B(text="🗑️ Clear Channel Posts", callback_data=f"clr:{gw}")],
        [B(text="⬅️ Back", callback_data="mg")],
    ])
