from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
import config, db, utils, commands
import keyboards as kb
from states import AddCh
import participate

router = Router()

HOWTO = ("📖 <b>How to Use</b>\n\n1️⃣ Add this bot as <b>admin</b> in your channel\n"
         "2️⃣ Tap <b>Add Channel</b> and connect it\n3️⃣ Tap <b>New Giveaway</b> and follow the steps\n"
         "4️⃣ Share the participation link - every participant gets a post with a Vote button\n"
         "5️⃣ Tap <b>End Giveaway</b> in My Giveaways when you want to finish")


async def welcome(bot, chat_id, u):
    ce, A = utils.ce, utils.ce(utils.E_ARROW, "▸")
    text = (f"{ce(utils.E_WAVE, '👋')} <b>Welcome, {utils.esc(u.full_name)}!</b>\n\n"
            f"{A} <b>Name:</b> {utils.esc(u.full_name)}\n"
            f"{A} <b>User ID:</b> <code>{u.id}</code>\n"
            f"{A} <b>Username:</b> {utils.esc('@' + u.username if u.username else 'None')}\n\n"
            f"{ce(utils.E_GIFT, '🎁')} Create and manage vote giveaways in your channels.")
    if config.BANNER:
        try:
            await bot.send_photo(chat_id, config.BANNER, caption=text, reply_markup=kb.main_menu())
            return
        except Exception:
            pass
    await bot.send_message(chat_id, text, reply_markup=kb.main_menu())


async def verify(bot, u, auto=False):
    doc = await db.users.find_one({"_id": u.id}) or {}
    if auto and not doc.get("prompt"):
        return []
    missing = await utils.missing_force(bot, u.id)
    if missing:
        return missing
    await db.users.update_one({"_id": u.id}, {"$unset": {"prompt": "", "pending": ""}})
    if doc.get("prompt"):
        try:
            await bot.delete_message(u.id, doc["prompt"])
        except Exception:
            pass
    if doc.get("pending"):
        await bot.send_message(u.id, "✅ <b>Verified!</b> Tap below to continue.",
                               reply_markup=kb.link_btn("🎉 Continue", utils.gw_link(doc["pending"])))
    else:
        await welcome(bot, u.id, u)
    return []


@router.message(CommandStart())
async def start(m: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    u = m.from_user
    await db.users.update_one({"_id": u.id}, {"$set": {"name": u.full_name, "username": u.username},
                                              "$setOnInsert": {"joined": datetime.utcnow()}}, upsert=True)
    missing = await utils.missing_force(m.bot, u.id)
    if missing:
        sent = await m.answer("🔒 <b>Join our channel(s) to use this bot</b>\n\nJoin below - you'll be verified automatically.",
                              reply_markup=kb.force_kb(missing))
        await db.users.update_one({"_id": u.id}, {"$set": {"prompt": sent.message_id, "pending": command.args}})
        return
    if command.args:
        return await participate.begin(m, state, command.args)
    await welcome(m.bot, m.chat.id, u)


@router.callback_query(F.data == "fj")
async def fj(c: CallbackQuery):
    if await verify(c.bot, c.from_user):
        await c.answer("❌ Join all channels first", show_alert=True)
    else:
        await c.answer()


@router.chat_member()
async def auto_detect(ev: ChatMemberUpdated):
    if ev.new_chat_member.status in utils.OK:
        await verify(ev.bot, ev.new_chat_member.user, auto=True)


@router.message(Command("cancel"))
async def cancel_m(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("❌ Cancelled.", reply_markup=kb.main_menu())


@router.callback_query(F.data == "cancel")
async def cancel_c(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.answer("Cancelled")
    await c.message.answer("❌ Cancelled.", reply_markup=kb.main_menu())


@router.message(Command("help"))
async def help_cmd(m: Message):
    await m.answer(commands.help_text(m.from_user.id == config.OWNER_ID))


@router.callback_query(F.data == "menu")
async def menu(c: CallbackQuery):
    await c.answer()
    try:
        await c.message.delete()
    except Exception:
        pass
    await welcome(c.bot, c.message.chat.id, c.from_user)


@router.callback_query(F.data == "howto")
async def howto(c: CallbackQuery):
    await utils.reply(c, HOWTO, kb.back())


# ---------- channels ----------
@router.message(Command("addchannel"))
@router.callback_query(F.data == "addch")
async def addch(e, state: FSMContext):
    await state.set_state(AddCh.wait)
    await utils.reply(e, "➕ <b>Add Channel</b>\n\n1. Add this bot as <b>admin</b> (with post permission) in your channel\n"
                         "2. Send the channel <b>@username</b>, its ID, or <b>forward any message</b> from it here.", kb.cancel())


@router.message(AddCh.wait)
async def addch_save(m: Message, state: FSMContext):
    ref = None
    fo = m.forward_origin
    if fo and fo.type == "channel":
        ref = fo.chat.id
    elif m.text:
        ref = m.text.strip()
        if ref.lstrip("-").isdigit():
            ref = int(ref)
    try:
        chat = await m.bot.get_chat(ref)
        if chat.type != "channel":
            raise ValueError
        me = await m.bot.get_chat_member(chat.id, utils.BOT_ID)
        you = await m.bot.get_chat_member(chat.id, m.from_user.id)
        if me.status != "administrator" or you.status not in ("creator", "administrator"):
            raise ValueError
    except Exception:
        return await m.answer("❌ Couldn't verify. Make sure the bot is <b>admin</b> in that channel and you are an admin too, then try again.",
                              reply_markup=kb.cancel())
    link = f"https://t.me/{chat.username}" if chat.username else None
    if not link:
        try:
            link = await m.bot.export_chat_invite_link(chat.id)
        except Exception:
            link = None
    await db.channels.update_one({"owner_id": m.from_user.id, "chat_id": chat.id},
                                 {"$set": {"title": chat.title, "link": link}}, upsert=True)
    await state.clear()
    await m.answer(f"✅ <b>{utils.esc(chat.title)}</b> connected!", reply_markup=kb.main_menu())


@router.message(Command("mychannels"))
@router.callback_query(F.data == "mych")
async def mych(e):
    chs = await db.channels.find({"owner_id": e.from_user.id}).to_list(50)
    if not chs:
        return await utils.reply(e, "📊 You have no channels yet. Tap <b>Add Channel</b>.", kb.back())
    from aiogram.types import InlineKeyboardMarkup as M, InlineKeyboardButton as B
    rows = [[B(text=f"❌ {c['title']}", callback_data=f"rmch:{c['chat_id']}")] for c in chs]
    rows.append([B(text="⬅️ Back", callback_data="menu")])
    await utils.reply(e, "📊 <b>My Channels</b>\nTap a channel to remove it:", M(inline_keyboard=rows))


@router.callback_query(F.data.startswith("rmch:"))
async def rmch(c: CallbackQuery):
    await db.channels.delete_one({"owner_id": c.from_user.id, "chat_id": int(c.data.split(":")[1])})
    await c.answer("Removed")
    await mych(c)
