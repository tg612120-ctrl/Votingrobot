# Vote Giveaway Bot (aiogram + MongoDB)

## Files
| File | Kaam |
|---|---|
| `main.py` | Bot start, middleware (ban check) |
| `commands.py` | **Commands menu** - yahin se sab commands/menu/help badlo |
| `keyboards.py` | Saare buttons / menus |
| `handlers/user.py` | /start, force join, welcome, channels |
| `handlers/giveaway.py` | Create flow, Management Panel, End giveaway |
| `handlers/participate.py` | Participation link flow, vote |
| `handlers/owner.py` | Owner commands |
| `db.py`, `utils.py`, `states.py`, `config.py` | Helpers |

## Commands
**Users:** /start /newgiveaway /mygiveaways /mychannels /addchannel /cancel /help
**Owner:** /botstats /allgiveaways /forceend /ban /unban /broadcast /addforce /delforce /forcelist

## Railway deploy
1. Is folder ko GitHub repo me push karo -> Railway me "Deploy from GitHub".
2. Variables: `BOT_TOKEN`, `MONGO_URI` (MongoDB Atlas), `OWNER_ID`. Optional: `BANNER`, `DB_NAME`.
3. Procfile se worker chalega. Bot ko kabhi 2 jagah mat chalana (ek hi instance).

## Setup
- Force join: bot ko us channel me admin banao, phir owner se `/addforce @channel`.
  (Join auto-detect ke liye bot ka us channel me admin hona zaroori hai.)
- Users apne channel me bot ko admin (post permission) bana ke Add Channel karte hain.
- Voting rule badalna ho: `handlers/participate.py` me `ONE_VOTE_PER_GIVEAWAY`.
