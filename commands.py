"""COMMANDS MENU - sabhi commands yahin se control hote hain.
Naya command add/remove karna ho to sirf yahan list badlo (aur handler likho).
Ye list Telegram ke command menu aur /help dono me dikhti hai."""
from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
import config

USER_COMMANDS = [
    ("start", "Start the bot"),
    ("newgiveaway", "Create a new giveaway"),
    ("mygiveaways", "Manage your giveaways"),
    ("mychannels", "View / remove your channels"),
    ("addchannel", "Connect a channel"),
    ("cancel", "Cancel current action"),
    ("help", "Show all commands"),
]

OWNER_COMMANDS = [
    ("botstats", "Total users, giveaways, entries"),
    ("allgiveaways", "List all running giveaways"),
    ("forceend", "/forceend <id> - end any giveaway"),
    ("ban", "/ban <user_id>"),
    ("unban", "/unban <user_id>"),
    ("broadcast", "/broadcast <text> or reply to a message"),
    ("addforce", "/addforce @channel - add force-join channel"),
    ("delforce", "/delforce @channel - remove force-join channel"),
    ("forcelist", "Show force-join channels"),
]


async def setup(bot: Bot):
    await bot.set_my_commands([BotCommand(command=c, description=d) for c, d in USER_COMMANDS], BotCommandScopeDefault())
    allc = USER_COMMANDS + OWNER_COMMANDS
    await bot.set_my_commands([BotCommand(command=c, description=d[:256]) for c, d in allc],
                              BotCommandScopeChat(chat_id=config.OWNER_ID))


def help_text(is_owner=False):
    t = "📖 <b>Commands</b>\n\n" + "\n".join(f"/{c} - {d}" for c, d in USER_COMMANDS)
    if is_owner:
        t += "\n\n👑 <b>Owner</b>\n\n" + "\n".join(f"/{c} - {d}" for c, d in OWNER_COMMANDS)
    return t
