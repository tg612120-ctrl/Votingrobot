import html
import secrets
import db

BOT_USERNAME = ""
BOT_ID = 0
esc = html.escape
OK = ("member", "administrator", "creator")


def new_id():
    return secrets.token_urlsafe(6)


def gw_link(gw):
    return f"https://t.me/{BOT_USERNAME}?start={gw}"


async def is_member(bot, chat_id, uid):
    try:
        m = await bot.get_chat_member(chat_id, uid)
        return m.status in OK
    except Exception:
        return False


async def missing_force(bot, uid):
    return [c for c in await db.force_list() if not await is_member(bot, c["chat_id"], uid)]


async def reply(e, text, kb=None):
    """Works for both Message and CallbackQuery."""
    if hasattr(e, "message"):
        await e.answer()
        e = e.message
    return await e.answer(text, reply_markup=kb)


def caption(g, p):
    un = f"@{p['username']}" if p.get("username") else "None"
    t = (f"🥂 <b><u>PARTICIPANT DETAILS</u></b>\n"
         f"<blockquote>▸ <b>USER</b>: {esc(p['name'])}\n"
         f"▸ <b>USER-ID</b>: <code>{p['user_id']}</code>\n"
         f"▸ <b>USERNAME</b>: {esc(un)}</blockquote>\n"
         f"⚠️ <b>NOTE</b>: <i>ONLY CHANNEL SUBSCRIBERS CAN VOTE</i>\n\n"
         f"🎁 <b>{esc(g['title'])}</b>\n")
    if g.get("support"):
        t += f"📞 Support: {esc(g['support'])}\n"
    return t + f"💎 @{BOT_USERNAME}"
