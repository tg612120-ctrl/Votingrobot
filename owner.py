import asyncio
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
import config, db, utils
from handlers import giveaway

router = Router()
router.message.filter(F.from_user.id == config.OWNER_ID)  # sirf owner


@router.message(Command("botstats"))
async def stats(m: Message):
    await m.answer(f"📊 <b>Bot Stats</b>\n\n👥 Users: {await db.users.count_documents({})}\n"
                   f"🚫 Banned: {await db.users.count_documents({'banned': True})}\n"
                   f"📢 Channels: {await db.channels.count_documents({})}\n"
                   f"🎁 Giveaways: {await db.giveaways.count_documents({})}\n"
                   f"🙋 Entries: {await db.parts.count_documents({})}\n"
                   f"🗳️ Votes: {await db.votes.count_documents({})}")


@router.message(Command("allgiveaways"))
async def allgw(m: Message):
    lines = []
    async for g in db.giveaways.find().limit(40):
        n = await db.parts.count_documents({"gw": g["_id"]})
        lines.append(f"• <code>{g['_id']}</code> | {utils.esc(g['title'][:30])} | owner <code>{g['owner_id']}</code> | {n} entries")
    await m.answer("🎁 <b>All Giveaways</b>\n\n" + ("\n".join(lines) or "None running."))


@router.message(Command("forceend"))
async def forceend(m: Message, command: CommandObject):
    g = await db.giveaways.find_one({"_id": (command.args or "").strip()})
    if not g:
        return await m.answer("Usage: /forceend <giveaway_id> (not found)")
    await giveaway.finish(m.bot, g)
    await m.answer("✅ Giveaway ended and data deleted.")


@router.message(Command("ban"))
async def ban(m: Message, command: CommandObject):
    if not (command.args or "").isdigit():
        return await m.answer("Usage: /ban <user_id>")
    await db.users.update_one({"_id": int(command.args)}, {"$set": {"banned": True}}, upsert=True)
    await m.answer("🚫 Banned.")


@router.message(Command("unban"))
async def unban(m: Message, command: CommandObject):
    if not (command.args or "").isdigit():
        return await m.answer("Usage: /unban <user_id>")
    await db.users.update_one({"_id": int(command.args)}, {"$set": {"banned": False}})
    await m.answer("✅ Unbanned.")


@router.message(Command("broadcast"))
async def broadcast(m: Message, command: CommandObject):
    src, text = m.reply_to_message, command.args
    if not src and not text:
        return await m.answer("Usage: /broadcast <text> or reply to a message with /broadcast")
    ok = bad = 0
    async for u in db.users.find({"banned": {"$ne": True}}):
        try:
            if src:
                await src.copy_to(u["_id"])
            else:
                await m.bot.send_message(u["_id"], text)
            ok += 1
        except Exception:
            bad += 1
        await asyncio.sleep(0.05)
    await m.answer(f"📢 Done. Sent: {ok} | Failed: {bad}")


@router.message(Command("addforce"))
async def addforce(m: Message, command: CommandObject):
    arg = (command.args or "").strip()
    if not arg:
        return await m.answer("Usage: /addforce @channel (bot must be admin there)")
    try:
        chat = await m.bot.get_chat(int(arg) if arg.lstrip("-").isdigit() else arg)
        link = f"https://t.me/{chat.username}" if chat.username else await m.bot.export_chat_invite_link(chat.id)
    except Exception as e:
        return await m.answer(f"❌ Failed: {utils.esc(str(e))}")
    await db.settings.update_one({"_id": "force"}, {"$pull": {"items": {"chat_id": chat.id}}}, upsert=True)
    await db.settings.update_one({"_id": "force"}, {"$push": {"items": {"chat_id": chat.id, "title": chat.title, "link": link}}})
    await m.answer(f"✅ Force join added: {utils.esc(chat.title)}")


@router.message(Command("delforce"))
async def delforce(m: Message, command: CommandObject):
    arg = (command.args or "").strip()
    try:
        chat = await m.bot.get_chat(int(arg) if arg.lstrip("-").isdigit() else arg)
    except Exception:
        return await m.answer("Usage: /delforce @channel")
    await db.settings.update_one({"_id": "force"}, {"$pull": {"items": {"chat_id": chat.id}}})
    await m.answer("✅ Removed.")


@router.message(Command("forcelist"))
async def forcelist(m: Message):
    items = await db.force_list()
    await m.answer("🔒 <b>Force Join</b>\n\n" + ("\n".join(f"• {utils.esc(c['title'])} ({c['chat_id']})" for c in items) or "None set."))
