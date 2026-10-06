import asyncio
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup as M, InlineKeyboardButton as B
import config, db, utils
import keyboards as kb
from states import Create

router = Router()
esc = utils.esc


# ---------- create flow ----------
@router.message(Command("newgiveaway"))
@router.callback_query(F.data == "new")
async def new(e, state: FSMContext):
    chs = await db.channels.find({"owner_id": e.from_user.id}).to_list(50)
    if not chs:
        return await utils.reply(e, "📢 First connect a channel. Tap <b>Add Channel</b>.", kb.main_menu())
    rows = [[B(text=c["title"], callback_data=f"cc:{c['chat_id']}")] for c in chs]
    rows.append([B(text="❌ Cancel", callback_data="cancel")])
    await state.set_state(Create.channel)
    await utils.reply(e, "📢 <b>Select the channel for this giveaway:</b>", M(inline_keyboard=rows))


@router.callback_query(Create.channel, F.data.startswith("cc:"))
async def pick_channel(c: CallbackQuery, state: FSMContext):
    ch = await db.channels.find_one({"owner_id": c.from_user.id, "chat_id": int(c.data.split(":")[1])})
    if not ch:
        return await c.answer("Channel not found", show_alert=True)
    await state.update_data(chat_id=ch["chat_id"], ch_link=ch.get("link"))
    await state.set_state(Create.title)
    await utils.reply(c, "📝 <b>Create New Giveaway: Step 1</b>\n\n<b>Enter Giveaway Description</b>\n"
                         "Send a short, catchy title for your event.\n<i>(e.g., 'iPhone 15 Contest')</i>\n\n"
                         f"💡 Type /skip to use default: '{config.DEFAULT_TITLE}'", kb.cancel())


@router.message(Create.title, Command("skip"))
@router.message(Create.title, F.text)
async def get_title(m: Message, state: FSMContext):
    title = config.DEFAULT_TITLE if m.text.startswith("/skip") else m.text.strip()[:200]
    await state.update_data(title=title)
    await state.set_state(Create.thumb)
    await m.answer("🖼️ <b>Custom Thumbnail</b>\n\nSend an image to use as the banner for this giveaway.\n\n"
                   "Type /skip to use no banner.", reply_markup=kb.cancel())


@router.message(Create.thumb, Command("skip"))
@router.message(Create.thumb, F.photo)
async def get_thumb(m: Message, state: FSMContext):
    await state.update_data(thumb=m.photo[-1].file_id if m.photo else None)
    await state.set_state(Create.pbtn)
    await m.answer("🔘 <b>\"Participate Now\" Button</b>\n\nAdd a button below each vote post so viewers can join with one tap?",
                   reply_markup=M(inline_keyboard=[[B(text="✅ Add Button", callback_data="pb:1"), B(text="⏭️ Skip", callback_data="pb:0")]]))


@router.callback_query(Create.pbtn, F.data.startswith("pb:"))
async def get_pbtn(c: CallbackQuery, state: FSMContext):
    await state.update_data(pbtn=c.data.endswith("1"))
    await state.set_state(Create.support)
    await utils.reply(c, "📞 <b>Support Contact</b>\n\nSend a Telegram @username participants can contact for help.\n\n"
                         "Type /skip if you don't want to add one.", kb.cancel())


@router.message(Create.support, Command("skip"))
@router.message(Create.support, F.text)
async def get_support(m: Message, state: FSMContext):
    d = await state.get_data()
    await state.clear()
    sup = None if m.text.startswith("/skip") else m.text.strip()
    g = {"_id": utils.new_id(), "owner_id": m.from_user.id, "chat_id": d["chat_id"], "ch_link": d.get("ch_link"),
         "title": d["title"], "thumb": d.get("thumb"), "pbtn": d.get("pbtn", False), "support": sup,
         "open": True, "created": datetime.utcnow()}
    await db.giveaways.insert_one(g)
    await m.answer("✅ <b>Saved!</b> Your giveaway is live. Share the link below.")
    await m.answer(await panel_text(g), reply_markup=kb.panel_kb(g))


# ---------- manage ----------
async def panel_text(g):
    n = await db.parts.count_documents({"gw": g["_id"]})
    return (f"⚙️ <b>Management Panel</b>\n<b>Title:</b> {esc(g['title'])}\n<b>ID:</b> <code>{g['_id']}</code>\n"
            f"<b>Status:</b> {'active' if g['open'] else 'participation stopped'}\n<b>Participants:</b> {n}\n"
            f"<b>Link:</b> {utils.gw_link(g['_id'])}")


async def own(c: CallbackQuery, gw):
    g = await db.giveaways.find_one({"_id": gw})
    if not g or (g["owner_id"] != c.from_user.id and c.from_user.id != config.OWNER_ID):
        await c.answer("Giveaway not found", show_alert=True)
        return None
    return g


@router.message(Command("mygiveaways"))
@router.callback_query(F.data == "mg")
async def mg(e, state: FSMContext = None):
    gs = await db.giveaways.find({"owner_id": e.from_user.id}).to_list(50)
    if not gs:
        return await utils.reply(e, "📋 You have no running giveaways.", kb.back())
    rows = [[B(text=f"🎁 {g['title'][:40]}", callback_data=f"gw:{g['_id']}")] for g in gs]
    rows.append([B(text="⬅️ Back", callback_data="menu")])
    await utils.reply(e, "📋 <b>My Giveaways</b>", M(inline_keyboard=rows))


@router.callback_query(F.data.startswith("gw:"))
async def open_panel(c: CallbackQuery):
    g = await own(c, c.data.split(":")[1])
    if g:
        await c.answer()
        await c.message.edit_text(await panel_text(g), reply_markup=kb.panel_kb(g))


@router.callback_query(F.data.startswith("lb:"))
async def leaderboard(c: CallbackQuery):
    g = await own(c, c.data.split(":")[1])
    if not g:
        return
    ps = await db.parts.find({"gw": g["_id"]}).sort("votes", -1).to_list(10)
    lines = [f"{i + 1}. {esc(p['name'])} - <b>{p['votes']}</b> votes" for i, p in enumerate(ps)]
    await c.answer()
    await c.message.edit_text("🏆 <b>Leaderboard (Top 10)</b>\n\n" + ("\n".join(lines) or "No participants yet."),
                              reply_markup=kb.back(f"gw:{g['_id']}"))


@router.callback_query(F.data.startswith("tp:"))
async def toggle(c: CallbackQuery):
    g = await own(c, c.data.split(":")[1])
    if not g:
        return
    g["open"] = not g["open"]
    await db.giveaways.update_one({"_id": g["_id"]}, {"$set": {"open": g["open"]}})
    await c.answer("Participation " + ("resumed" if g["open"] else "stopped"))
    await c.message.edit_text(await panel_text(g), reply_markup=kb.panel_kb(g))


@router.callback_query(F.data.startswith("end:"))
async def end_ask(c: CallbackQuery):
    g = await own(c, c.data.split(":")[1])
    if g:
        await c.answer()
        await c.message.edit_text("🏁 <b>End this giveaway?</b>\nWinners will be announced and all data deleted.",
                                  reply_markup=kb.yes_no(f"endy:{g['_id']}", f"gw:{g['_id']}"))


@router.callback_query(F.data.startswith("endy:"))
async def end_do(c: CallbackQuery):
    g = await own(c, c.data.split(":")[1])
    if g:
        await c.answer("Ending...")
        text = await finish(c.bot, g)
        await c.message.edit_text(text, reply_markup=kb.back())


@router.callback_query(F.data.startswith("clr:"))
async def clr_ask(c: CallbackQuery):
    g = await own(c, c.data.split(":")[1])
    if g:
        await c.answer()
        await c.message.edit_text("🗑️ <b>Clear all participant posts from the channel?</b>\nThis also resets participants and votes.",
                                  reply_markup=kb.yes_no(f"clry:{g['_id']}", f"gw:{g['_id']}"))


@router.callback_query(F.data.startswith("clry:"))
async def clr_do(c: CallbackQuery):
    g = await own(c, c.data.split(":")[1])
    if not g:
        return
    await c.answer("Clearing...")
    async for p in db.parts.find({"gw": g["_id"]}):
        if p.get("msg_id"):
            try:
                await c.bot.delete_message(g["chat_id"], p["msg_id"])
            except Exception:
                pass
            await asyncio.sleep(0.05)
    await db.parts.delete_many({"gw": g["_id"]})
    await db.votes.delete_many({"gw": g["_id"]})
    await c.message.edit_text(await panel_text(g), reply_markup=kb.panel_kb(g))


# ---------- end giveaway (also used by owner /forceend) ----------
async def finish(bot, g):
    gw = g["_id"]
    ps = await db.parts.find({"gw": gw}).sort("votes", -1).to_list(None)
    medals = ["🥇", "🥈", "🥉"]
    lines = [f"{medals[i]} {esc(p['name'])} - {p['votes']} votes" for i, p in enumerate(ps[:3])]
    text = (f"🏁 <b>GIVEAWAY ENDED</b>\n\n<b>{esc(g['title'])}</b>\n\n"
            + ("\n".join(lines) or "No participants.") + "\n\n🎉 Congratulations!")
    try:
        await bot.send_message(g["chat_id"], text)
    except Exception:
        pass
    for p in ps:
        if p.get("msg_id"):
            try:
                await bot.edit_message_reply_markup(chat_id=g["chat_id"], message_id=p["msg_id"], reply_markup=None)
            except Exception:
                pass
            await asyncio.sleep(0.05)
    await db.parts.delete_many({"gw": gw})
    await db.votes.delete_many({"gw": gw})
    await db.giveaways.delete_one({"_id": gw})
    return text
