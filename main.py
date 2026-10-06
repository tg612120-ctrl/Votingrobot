import asyncio
import logging
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import config, db, utils, commands
import owner, user, giveaway, participate


class BanMW(BaseMiddleware):
    async def __call__(self, handler, event, data):
        u = data.get("event_from_user")
        if u and u.id != config.OWNER_ID:
            d = await db.users.find_one({"_id": u.id}, {"banned": 1})
            if d and d.get("banned"):
                return
        return await handler(event, data)


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(config.BOT_TOKEN, default=DefaultBotProperties(
        parse_mode=ParseMode.HTML, link_preview_is_disabled=True))
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.outer_middleware(BanMW())
    dp.callback_query.outer_middleware(BanMW())
    dp.include_routers(owner.router, user.router, giveaway.router, participate.router)

    await db.init()
    me = await bot.get_me()
    utils.BOT_USERNAME, utils.BOT_ID = me.username, me.id
    await commands.setup(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
