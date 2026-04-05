# commands/giveaway_create.py
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime, timedelta
from utils import parse_duration, format_time, get_end_time
from config import (
    GIVEAWAY_THUMBNAIL_URL, GIVEAWAY_BANNER_URL,
    EMOJI_GIVEAWAY, EMOJI_TROPHY, EMOJI_PARTICIPANTS, EMOJI_TIME,
    EMOJI_HOSTED, EMOJI_ENDS, EMOJI_LINE, EMOJI_JOIN, EMOJI_WINNER,
    ALLOWED_COMMAND_ROLES
)
from storage import load_daily_giveaways, save_daily_giveaways, DailyGiveawayData
from winner_image import get_winner_image
import giveaway_state

class JoinButton(discord.ui.Button):
    def __init__(self, giveaway_view):
        super().__init__(label="", style=discord.ButtonStyle.success, emoji=EMOJI_JOIN, custom_id="join_button")
        self.giveaway_view = giveaway_view
    
    async def callback(self, interaction: discord.Interaction):
        if self.giveaway_view.ended:
            await interaction.response.send_message("This giveaway has ended!", ephemeral=True)
            return
        
        user_id = interaction.user.id
        
        if user_id in self.giveaway_view.participants:
            await interaction.response.send_message(f"⚠️ You are already participating in **{self.giveaway_view.prize}**!", ephemeral=True)
        else:
            self.giveaway_view.participants.append(user_id)
            await self.giveaway_view.update_embed()
            await interaction.response.send_message(f"✅ You joined the giveaway for **{self.giveaway_view.prize}**! Good luck!", ephemeral=True)

class GiveawayView(discord.ui.View):
    def __init__(self, bot, channel_id: int, message_id: int, title: str, description: str, prize: str, 
                 winners_count: int, duration_seconds: int, is_daily: bool = False, repeat_hours: int = 24):
        super().__init__(timeout=None)
        self.bot = bot
        self.channel_id = channel_id
        self.message_id = message_id
        self.title = title
        self.description = description
        self.prize = prize
        self.winners_count = winners_count
        self.duration_seconds = duration_seconds
        self.is_daily = is_daily
        self.repeat_hours = repeat_hours
        self.participants = []
        self.ended = False
        self.end_time = get_end_time(duration_seconds)
        
        self.add_item(JoinButton(self))
        
        if message_id != 0:
            giveaway_state.register_giveaway(message_id, self)
    
    def set_message_id(self, message_id: int):
        self.message_id = message_id
        giveaway_state.register_giveaway(message_id, self)
    
    async def update_embed(self):
        if self.ended:
            return
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(self.message_id)
        except:
            return
        embed = self.get_embed()
        await message.edit(embed=embed)
    
    async def end_giveaway(self):
        if self.ended:
            return
        self.ended = True
        
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
        
        try:
            message = await channel.fetch_message(self.message_id)
        except:
            return
        
        if not self.participants:
            embed = discord.Embed(
                title=f"{self.title} Ended", 
                description=f"**Prize:** {EMOJI_TROPHY} {self.prize}\n\n❌ No participants joined!",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL_URL)
            embed.set_image(url=GIVEAWAY_BANNER_URL)
            await message.edit(embed=embed, view=None)
            giveaway_state.unregister_giveaway(self.message_id)
            return
        
        winners_count = min(self.winners_count, len(self.participants))
        winners = random.sample(self.participants, winners_count)
        winner_mentions = " ".join([f"<@{w}>" for w in winners])
        
        winner_image = get_winner_image()
        send_mode = winner_image.get("send_mode", "private")
        
        for winner_id in winners:
            try:
                winner_user = await self.bot.fetch_user(winner_id)
                winner_embed = discord.Embed(
                    title=f"{EMOJI_WINNER} **WINNER!** {EMOJI_WINNER}",
                    description=f"## 🎉 Congratulations! 🎉\n\nYou have won the giveaway for:\n{EMOJI_TROPHY} **{self.prize}**\n\n📩 Please contact the staff to claim your gift!",
                    color=discord.Color.gold()
                )
                if winner_image["url"] and send_mode in ["private", "all"]:
                    winner_embed.set_image(url=winner_image["url"])
                else:
                    winner_embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL_URL)
                
                try:
                    await winner_user.send(embed=winner_embed)
                except:
                    pass
            except:
                pass
        
        embed = discord.Embed(
            title=f"**{self.title} ENDED**",
            description=f"{EMOJI_LINE*10}\n**Prize:** {EMOJI_TROPHY} {self.prize}\n\n{EMOJI_PARTICIPANTS} **Total Participants:** `{len(self.participants)}`\n{EMOJI_TROPHY} **Winner(s):** {winner_mentions}\n{EMOJI_LINE*10}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL_URL)
        embed.set_image(url=GIVEAWAY_BANNER_URL)
        await message.edit(embed=embed, view=None)
        
        if send_mode in ["server", "all"] and winner_image["url"]:
            server_embed = discord.Embed(
                title=f"{EMOJI_WINNER} **GIVEAWAY WINNERS!** {EMOJI_WINNER}",
                description=f"🎊 **Congratulations** {winner_mentions}! 🎊\n\n✨ You won {EMOJI_TROPHY} **{self.prize}**!\n\n📩 Please contact the staff to claim your gift.",
                color=discord.Color.gold()
            )
            server_embed.set_image(url=winner_image["url"])
            await channel.send(embed=server_embed)
        else:
            await channel.send(f"{EMOJI_WINNER} **GIVEAWAY WINNERS!** {EMOJI_WINNER}\n\n🎊 Congratulations {winner_mentions}! 🎊\n✨ You won {EMOJI_TROPHY} **{self.prize}**!\n📩 Please contact the staff to claim your gift.")
        
        giveaway_state.unregister_giveaway(self.message_id)
    
    def get_embed(self):
        time_left = format_time(self.duration_seconds)
        end_timestamp = int(self.end_time.timestamp())
        
        description_text = f"# {EMOJI_TROPHY} {self.prize}\n\n"
        if self.description:
            description_text += f"{EMOJI_TROPHY} *{self.description}*\n\n"
        description_text += f"{EMOJI_LINE*12}\n"
        description_text += f"{EMOJI_TROPHY} **Winners:** `{self.winners_count}`\n"
        description_text += f"{EMOJI_PARTICIPANTS} **Participants:** `{len(self.participants)}`\n"
        description_text += f"{EMOJI_TIME} **Time Left:** `{time_left}`\n"
        description_text += f"{EMOJI_ENDS} **Ends:** <t:{end_timestamp}:R>\n"
        description_text += f"{EMOJI_HOSTED} **Hosted by:** <@{self.bot.user.id}>\n"
        description_text += f"{EMOJI_LINE*12}\n\n"
        description_text += f"**Click {EMOJI_JOIN} to join!**"
        
        embed = discord.Embed(
            title=f"**{self.title}**",
            description=description_text,
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL_URL)
        embed.set_image(url=GIVEAWAY_BANNER_URL)
        embed.set_footer(text=f"Giveaway • {time_left} remaining")
        return embed

async def create_repeat_giveaway(bot, channel, title, description, prize, winners_count, duration_seconds, repeat_hours):
    view = GiveawayView(
        bot=bot, channel_id=channel.id, message_id=0,
        title=title, description=description, prize=prize,
        winners_count=winners_count, duration_seconds=duration_seconds,
        is_daily=True, repeat_hours=repeat_hours
    )
    embed = view.get_embed()
    message = await channel.send(embed=embed, view=view)
    view.set_message_id(message.id)
    
    async def end_task():
        await asyncio.sleep(duration_seconds)
        await view.end_giveaway()
        await asyncio.sleep(repeat_hours * 3600)
        await create_repeat_giveaway(bot, channel, title, description, prize, winners_count, duration_seconds, repeat_hours)
    
    asyncio.create_task(end_task())

def setup_giveaway_create(bot):
    
    @bot.tree.command(name="giveaway-create", description="Create a new giveaway")
    @app_commands.describe(
        title="Giveaway title",
        description="Giveaway description",
        prize="Prize",
        duration="Duration: 30s, 5m, 2h, 1d, 1h30m",
        winners="Number of winners (1-10)",
        channel="Channel to send giveaway",
        everyday="Repeat automatically? true/false",
        every_giveaway="Time between repeats: 30m, 2h, 1d, 12h (default: 24h)"
    )
    @app_commands.choices(everyday=[
        app_commands.Choice(name="true", value="true"),
        app_commands.Choice(name="false", value="false")
    ])
    async def giveaway_create(
        interaction: discord.Interaction, title: str, description: str, prize: str,
        duration: str, winners: app_commands.Range[int, 1, 10], channel: discord.TextChannel,
        everyday: str = "false", every_giveaway: str = "24h"
    ):
        user_role_ids = [role.id for role in interaction.user.roles]
        has_permission = any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids)
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (has_permission or is_admin):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        everyday_bool = everyday.lower() == "true"
        duration_seconds = parse_duration(duration)
        repeat_seconds = parse_duration(every_giveaway) if every_giveaway else 86400
        repeat_hours = max(1, repeat_seconds // 3600)
        
        if duration_seconds < 60:
            await interaction.response.send_message("❌ Duration must be at least 60 seconds!", ephemeral=True)
            return
        
        repeat_time_str = format_time(repeat_seconds)
        
        view = GiveawayView(
            bot=bot, channel_id=channel.id, message_id=0,
            title=title, description=description, prize=prize,
            winners_count=winners, duration_seconds=duration_seconds,
            is_daily=everyday_bool, repeat_hours=repeat_hours
        )
        
        embed = view.get_embed()
        confirm_msg = f"✅ Creating giveaway in {channel.mention}..."
        if everyday_bool:
            confirm_msg += f"\n🔄 This giveaway will repeat **every {repeat_time_str}** automatically!"
        
        await interaction.response.send_message(confirm_msg, ephemeral=True)
        message = await channel.send(embed=embed, view=view)
        view.set_message_id(message.id)
        
        async def end_task():
            await asyncio.sleep(duration_seconds)
            await view.end_giveaway()
            if everyday_bool:
                await asyncio.sleep(repeat_seconds)
                await create_repeat_giveaway(bot, channel, title, description, prize, winners, duration_seconds, repeat_hours)
        
        asyncio.create_task(end_task())
        
        if everyday_bool:
            daily_giveaways = load_daily_giveaways()
            g_id = f"daily_{channel.id}_{prize}_{datetime.now().timestamp()}"
            daily_giveaways[g_id] = DailyGiveawayData(
                prize=prize, duration_seconds=duration_seconds,
                winners_count=winners, channel_id=channel.id,
                next_run=(datetime.now() + timedelta(seconds=repeat_seconds)).isoformat()
            )
            save_daily_giveaways(daily_giveaways)