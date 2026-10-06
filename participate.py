from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from pymongo.errors import DuplicateKeyError
from pymongo import ReturnDocument
import db, utils
import keyboards as kb
from states import Join

router = Router()
ONE_VOTE_PER_GIVEAWAY = True  # False = ek user har participant ko 1 vote de sakta hai


async def begin(m: Message, state: FSMContext, gw):
    g = await db.giveaways.find_one({"_id": gw})
    if not g:
        return await m.answer("❌ This giveaway has ended or doesn't exist.")
    if not g["open"]:
        return await m.answer("🚫 Participation is closed for this giveaway.")
    uid = m.from_user.id
    if await db.parts.find_one({"gw": gw, "user_id": uid}):
        return await m.answer("✅ You're already participating in this giveaway.")
    if not await utils.is_member(m.bot, g["chat_id"], uid):
        return await m.answer("📢 Join the giveaway channel first, then open this link again.",
                              reply_markup=kb.link_btn("📢 Join Channel", g["ch_link"]) if g.get("ch_link") else None)
    await state.set_state(Join.name)
    await state.update_data(gw=gw)
    await m.answer("✍️ <b>Enter your name</b>\n\nThis name will appear on the channel post.", reply_markup=kb.cancel())


@router.message(Join.name, F.text)
async def get_name(m: Message, state: FSMContext):
    await state.update_data(name=m.text.strip()[:60])
    await state.set_state(Join.photo)
    await m.answer("🖼️ Send your <b>photo</b> for the post.\n\nType /skip to continue without one.", reply_markup=kb.cancel())


@router.message(Join.photo, Command("skip"))
@router.message(Join.photo, F.photo)
async def publish(m: Message, state: FSMContext):
    photo = m.photo[-1].file_id if m.photo else None
    d = await state.get_data()
    await state.clear()
    g = await db.giveaways.find_one({"_id": d["gw"]})
    if not g or not g["open"]:
        return await m.answer("❌ This giveaway is no longer accepting entries.")
    u = m.from_user
    p = {"gw": g["_id"], "user_id": u.id, "name": d["name"], "username": u.username, "photo": photo, "votes": 0}
    try:
        await db.parts.insert_one(p)
    except DuplicateKeyError:
        return await m.answer("✅ You're already participating.")
    img = photo or g.get("thumb")
    try:
        if img:
            sent = await m.bot.send_photo(g["chat_id"], img, caption=utils.caption(g, p), reply_markup=kb.post_kb(g, p))
        else:
            sent = await m.bot.send_message(g["chat_id"], utils.caption(g, p), reply_markup=kb.post_kb(g, p))
    except Exception:
        await db.parts.delete_one({"gw": g["_id"], "user_id": u.id})
        return await m.answer("❌ Couldn't post to the channel. Ask the giveaway owner to check the bot's permissions.")
    await db.parts.update_one({"gw": g["_id"], "user_id": u.id}, {"$set": {"msg_id": sent.message_id}})
    await m.answer("🎉 <b>You're in!</b> Your entry is live on the channel. Share it to get votes!")


@router.callback_query(F.data.startswith("v:"))
async def vote(c: CallbackQuery):
    _, gw, pid = c.data.split(":")
    pid = int(pid)
    g = await db.giveaways.find_one({"_id": gw})
    if not g:
        return await c.answer("This giveaway has ended.", show_alert=True)
    voter = c.from_user.id
    if voter == pid:
        return await c.answer("❌ You can't vote for yourself.", show_alert=True)
    if not await utils.is_member(c.bot, g["chat_id"], voter):
        return await c.answer("⚠️ Only channel subscribers can vote. Join the channel first.", show_alert=True)
    key = {"gw": gw, "voter": voter} if ONE_VOTE_PER_GIVEAWAY else {"gw": gw, "voter": voter, "pid": pid}
    try:
        await db.votes.insert_one({**key, "pid": pid})
    except DuplicateKeyError:
        return await c.answer("❌ You have already voted.", show_alert=True)
    p = await db.parts.find_one_and_update({"gw": gw, "user_id": pid}, {"$inc": {"votes": 1}},
                                           return_document=ReturnDocument.AFTER)
    if not p:
        return await c.answer("Participant not found.", show_alert=True)
    try:
        await c.message.edit_reply_markup(reply_markup=kb.post_kb(g, p))
    except Exception:
        pass
    await c.answer("✅ Vote counted!")
