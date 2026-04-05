# main.py
import discord
from discord.ext import commands
from config import BOT_TOKEN

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load commands
from commands.giveaway_create import setup_giveaway_create
from commands.giveaway_winner import setup_giveaway_winner
from commands.image_winner import setup_image_winner
from commands.admin_commands import setup_admin_commands

setup_giveaway_create(bot)
setup_giveaway_winner(bot)
setup_image_winner(bot)
setup_admin_commands(bot)

@bot.event
async def on_ready():
    print("="*50)
    print(f"✅ Bot is ready as {bot.user}")
    print(f"✅ Slash Commands (/):")
    print(f"   • /giveaway-create")
    print(f"   • /giveaway-winners")
    print(f"   • /image-winner")
    print(f"✅ Prefix Commands (!):")
    print(f"   • !next")
    print(f"   • !edit_time")
    print(f"   • !ulimit")
    print(f"   • !bothelp")
    print(f"   • !active")
    print("="*50)
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")

if __name__ == "__main__":
    bot.run(BOT_TOKEN)