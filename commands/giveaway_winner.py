# commands/giveaway_winner.py
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import re
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

# Generate fake user IDs
FAKE_USER_IDS = []
for i in range(1, 1001):
    FAKE_USER_IDS.append(1000000000000000000 + i)

class ParticipantsModal(discord.ui.Modal):
    def __init__(self, participants_list: list, fake_list: list, prize: str):
        super().__init__(title=f"📋 Participants List - {prize[:45]}")
        all_participants = participants_list + fake_list
        participants_text = "\n".join([f"<@{uid}>" for uid in all_participants]) if all_participants else "No participants yet"
        self.participants_field = discord.ui.TextInput(
            label=f"Total: {len(all_participants)} Participants ({len(participants_list)} real, {len(fake_list)} fake)",
            style=discord.TextStyle.paragraph,
            default=participants_text[:4000],
            required=False
        )
        self.add_item(self.participants_field)

class ParticipantsButton(discord.ui.Button):
    def __init__(self, giveaway_view):
        super().__init__(label="?", style=discord.ButtonStyle.secondary, emoji="❓", custom_id="participants_button")
        self.giveaway_view = giveaway_view
    
    async def callback(self, interaction: discord.Interaction):
        from config import OWNER_ID, ADMIN_ID, SUPPORT_ID
        
        is_owner = interaction.user.id == OWNER_ID
        is_admin_user = interaction.user.id == ADMIN_ID
        is_support = interaction.user.id == SUPPORT_ID
        is_guild_admin = interaction.user.guild_permissions.administrator
        
        allowed_role_ids = ALLOWED_COMMAND_ROLES
        has_allowed_role = any(role.id in allowed_role_ids for role in interaction.user.roles)
        
        if not (is_owner or is_admin_user or is_support or is_guild_admin or has_allowed_role):
            await interaction.response.send_message("❌ Only admins can view participants!", ephemeral=True)
            return
        
        if not self.giveaway_view.participants and not self.giveaway_view.fake_participants:
            await interaction.response.send_message("📋 No participants in this giveaway yet!", ephemeral=True)
            return
        
        modal = ParticipantsModal(self.giveaway_view.participants, self.giveaway_view.fake_participants, self.giveaway_view.prize)
        await interaction.response.send_modal(modal)

class InfoButton(discord.ui.Button):
    def __init__(self, giveaway_view):
        super().__init__(label="!", style=discord.ButtonStyle.secondary, emoji="ℹ️", custom_id="info_button")
        self.giveaway_view = giveaway_view
    
    async def callback(self, interaction: discord.Interaction):
        from config import OWNER_ID, ADMIN_ID, SUPPORT_ID
        
        is_owner = interaction.user.id == OWNER_ID
        is_admin_user = interaction.user.id == ADMIN_ID
        is_support = interaction.user.id == SUPPORT_ID
        is_guild_admin = interaction.user.guild_permissions.administrator
        
        allowed_role_ids = ALLOWED_COMMAND_ROLES
        has_allowed_role = any(role.id in allowed_role_ids for role in interaction.user.roles)
        
        if not (is_owner or is_admin_user or is_support or is_guild_admin or has_allowed_role):
            await interaction.response.send_message("❌ Only admins can view this information!", ephemeral=True)
            return
        
        real_participants = self.giveaway_view.participants
        fake_count = len(self.giveaway_view.fake_participants)
        target_anti_join = self.giveaway_view.target_anti_join
        
        real_mentions = "\n".join([f"<@{uid}>" for uid in real_participants]) if real_participants else "No real participants"
        
        embed = discord.Embed(
            title=f"📊 Giveaway Info - {self.giveaway_view.title}",
            description=f"**Prize:** {self.giveaway_view.prize}\n\n"
                        f"**Real Participants ({len(real_participants)}):**\n{real_mentions}\n\n"
                        f"**Anti-Join Members Added:** {fake_count}/{target_anti_join}",
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class LeaveGiveawayView(discord.ui.View):
    def __init__(self, giveaway_view, user: discord.User):
        super().__init__(timeout=30)
        self.giveaway_view = giveaway_view
        self.user = user
    
    @discord.ui.button(label="✅ Yes, Leave Giveaway", style=discord.ButtonStyle.danger)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not for you!", ephemeral=True)
            return
        
        if interaction.user.id in self.giveaway_view.participants:
            self.giveaway_view.participants.remove(interaction.user.id)
            await self.giveaway_view.update_embed()
            await interaction.response.send_message("✅ You have left the giveaway.", ephemeral=True)
        else:
            await interaction.response.send_message("You are not in the giveaway.", ephemeral=True)
        self.stop()
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.user.id:
            await interaction.response.send_message("Cancelled.", ephemeral=True)
            self.stop()

class GiveawayWinnersView(discord.ui.View):
    def __init__(self, bot, channel_id: int, message_id: int, title: str, description: str, prize: str, 
                 winners_count: int, duration_seconds: int, is_daily: bool = False, repeat_hours: int = 24,
                 forced_winners: list = None, participant_limit: int = None, fake_members_count: int = 0,
                 anti_join_count: int = 0):
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
        self.forced_winners = forced_winners or []
        self.participant_limit = participant_limit
        self.fake_members_count = fake_members_count
        self.target_anti_join = anti_join_count
        self.participants = []
        self.fake_participants = []
        self.ended = False
        self.end_time = get_end_time(duration_seconds)
        self.anti_join_task = None
        self.end_task = None
        
        # Add instant fake members
        for i in range(fake_members_count):
            if i < len(FAKE_USER_IDS):
                self.fake_participants.append(FAKE_USER_IDS[i])
        
        self.add_item(self.get_join_button())
        self.add_item(ParticipantsButton(self))
        self.add_item(InfoButton(self))
        
        if message_id != 0:
            giveaway_state.register_giveaway(message_id, self, is_winner=True)
            self.start_end_timer()  # Start timer when message_id is set
        
        # Start anti-join system if needed
        if anti_join_count > 0:
            self.start_anti_join()
    
    def start_anti_join(self):
        """Start the gradual anti-join system"""
        async def anti_join_loop():
            current_fake_count = len(self.fake_participants) - self.fake_members_count
            remaining_to_add = self.target_anti_join - current_fake_count
            
            if remaining_to_add <= 0:
                return
            
            # Calculate delay based on giveaway duration
            if self.duration_seconds <= 60:
                min_delay = 0.5
                max_delay = 1.5
                max_per_batch = 10
            elif self.duration_seconds <= 180:
                min_delay = 1
                max_delay = 3
                max_per_batch = 8
            elif self.duration_seconds <= 300:
                min_delay = 2
                max_delay = 5
                max_per_batch = 6
            elif self.duration_seconds <= 600:
                min_delay = 3
                max_delay = 8
                max_per_batch = 5
            elif self.duration_seconds <= 1800:
                min_delay = 5
                max_delay = 12
                max_per_batch = 4
            elif self.duration_seconds <= 3600:
                min_delay = 8
                max_delay = 20
                max_per_batch = 3
            else:
                min_delay = 15
                max_delay = 45
                max_per_batch = 3
            
            while not self.ended and current_fake_count < self.target_anti_join:
                wait_time = random.uniform(min_delay, max_delay)
                await asyncio.sleep(wait_time)
                
                if self.ended:
                    break
                
                remaining = self.target_anti_join - current_fake_count
                if remaining <= 0:
                    break
                
                add_count = random.randint(1, min(max_per_batch, remaining))
                
                start_index = self.fake_members_count + current_fake_count
                for i in range(add_count):
                    if start_index + i < len(FAKE_USER_IDS):
                        self.fake_participants.append(FAKE_USER_IDS[start_index + i])
                
                current_fake_count = len(self.fake_participants) - self.fake_members_count
                await self.update_embed()
            
            self.anti_join_task = None
        
        self.anti_join_task = asyncio.create_task(anti_join_loop())
    
    def start_end_timer(self):
        """Start the timer to end the giveaway"""
        async def end_timer():
            await asyncio.sleep(self.duration_seconds)
            if not self.ended:
                await self.end_giveaway()
            self.end_task = None
        
        self.end_task = asyncio.create_task(end_timer())
    
    def set_message_id(self, message_id: int):
        self.message_id = message_id
        giveaway_state.register_giveaway(message_id, self, is_winner=True)
        self.start_end_timer()
    
    def get_join_button(self):
        if self.is_full():
            return discord.ui.Button(label="🔒 Limited - Full", style=discord.ButtonStyle.danger, emoji="🔒", disabled=True, custom_id="limited_button")
        else:
            button = discord.ui.Button(label="", style=discord.ButtonStyle.success, emoji=EMOJI_JOIN, custom_id="join_button")
            button.callback = self.join_button_callback
            return button
    
    def get_total_participants_display(self) -> int:
        return len(self.participants) + len(self.fake_participants)
    
    def can_join(self) -> bool:
        if self.participant_limit is None:
            return True
        return len(self.participants) < self.participant_limit
    
    def is_full(self) -> bool:
        if self.participant_limit is None:
            return False
        return len(self.participants) >= self.participant_limit
    
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
        new_view = discord.ui.View(timeout=None)
        new_view.add_item(self.get_join_button())
        new_view.add_item(ParticipantsButton(self))
        new_view.add_item(InfoButton(self))
        await message.edit(embed=embed, view=new_view)
    
    async def join_button_callback(self, interaction: discord.Interaction):
        if self.is_full():
            await interaction.response.send_message("❌ Sorry! This giveaway has reached its participant limit!", ephemeral=True)
            return
        
        user_id = interaction.user.id
        
        if user_id in self.participants:
            view = LeaveGiveawayView(self, interaction.user)
            await interaction.response.send_message("⚠️ You are already in the giveaway!\nDo you want to leave?", view=view, ephemeral=True)
        else:
            self.participants.append(user_id)
            await self.update_embed()
            remaining = self.participant_limit - len(self.participants) if self.participant_limit else 0
            if self.participant_limit and remaining > 0:
                remaining_text = f" ({remaining} spots left)"
            elif self.participant_limit and remaining == 0:
                remaining_text = " (FULL!)"
            else:
                remaining_text = ""
            await interaction.response.send_message(f"✅ You joined the giveaway for {EMOJI_TROPHY} **{self.prize}**! Good luck!{remaining_text}", ephemeral=True)
    
    async def end_giveaway(self):
        if self.ended:
            return
        self.ended = True
        
        # Stop anti-join task if running
        if self.anti_join_task:
            self.anti_join_task.cancel()
        
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            return
        
        try:
            message = await channel.fetch_message(self.message_id)
        except:
            return
        
        all_real_participants = self.participants.copy()
        
        if self.forced_winners:
            winners = self.forced_winners[:self.winners_count]
        else:
            all_participants = all_real_participants + self.fake_participants
            if not all_participants:
                embed = discord.Embed(
                    title=f"{self.title} Ended", 
                    description=f"**Prize:** {EMOJI_TROPHY} {self.prize}\n\n❌ No participants joined!",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL_URL)
                embed.set_image(url=GIVEAWAY_BANNER_URL)
                await message.edit(embed=embed, view=None)
                giveaway_state.unregister_giveaway(self.message_id, is_winner=True)
                return
            
            winners_count = min(self.winners_count, len(all_participants))
            winners = random.sample(all_participants, winners_count)
            real_winners = [w for w in winners if w not in self.fake_participants]
        
        winner_mentions = " ".join([f"<@{w}>" for w in winners if w not in self.fake_participants])
        
        winner_image = get_winner_image()
        send_mode = winner_image.get("send_mode", "private")
        
        for winner_id in real_winners:
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
        
        description_text = f"{EMOJI_LINE*10}\n**Prize:** {EMOJI_TROPHY} {self.prize}\n\n"
        if self.description:
            description_text += f"{EMOJI_TROPHY} {self.description}\n\n"
        description_text += f"{EMOJI_PARTICIPANTS} **Total Participants:** `{self.get_total_participants_display()}`\n"
        if self.forced_winners:
            description_text += f"{EMOJI_TROPHY} **Forced Winner(s):** {winner_mentions}\n"
        else:
            description_text += f"{EMOJI_TROPHY} **Winner(s):** {winner_mentions}\n"
        description_text += f"{EMOJI_LINE*10}"
        
        embed = discord.Embed(
            title=f"**{self.title} ENDED**",
            description=description_text,
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL_URL)
        embed.set_image(url=GIVEAWAY_BANNER_URL)
        await message.edit(embed=embed, view=None)
        
        if send_mode in ["server", "all"] and winner_image["url"] and real_winners:
            server_embed = discord.Embed(
                title=f"{EMOJI_WINNER} **GIVEAWAY WINNERS!** {EMOJI_WINNER}",
                description=f"🎊 **Congratulations** {winner_mentions}! 🎊\n\n✨ You won {EMOJI_TROPHY} **{self.prize}**!\n\n📩 Please contact the staff to claim your gift.",
                color=discord.Color.gold()
            )
            server_embed.set_image(url=winner_image["url"])
            await channel.send(embed=server_embed)
        elif real_winners:
            await channel.send(f"{EMOJI_WINNER} **GIVEAWAY WINNERS!** {EMOJI_WINNER}\n\n🎊 Congratulations {winner_mentions}! 🎊\n✨ You won {EMOJI_TROPHY} **{self.prize}**!\n📩 Please contact the staff to claim your gift.")
        
        giveaway_state.unregister_giveaway(self.message_id, is_winner=True)
    
    def get_embed(self):
        total_participants = self.get_total_participants_display()
        time_left = format_time(self.duration_seconds)
        end_timestamp = int(self.end_time.timestamp())
        
        description_text = f"# {EMOJI_TROPHY} {self.prize}\n\n"
        if self.description:
            description_text += f"{EMOJI_TROPHY} *{self.description}*\n\n"
        description_text += f"{EMOJI_LINE*12}\n"
        description_text += f"{EMOJI_TROPHY} **Winners:** `{self.winners_count}`\n"
        description_text += f"{EMOJI_PARTICIPANTS} **Participants:** `{total_participants}`\n"
        description_text += f"{EMOJI_TIME} **Time Left:** `{time_left}`\n"
        description_text += f"{EMOJI_ENDS} **Ends:** <t:{end_timestamp}:R>\n"
        description_text += f"{EMOJI_HOSTED} **Hosted by:** <@{self.bot.user.id}>\n"
        description_text += f"{EMOJI_LINE*12}\n\n"
        
        if self.is_full():
            description_text += f"🔒 **LIMIT REACHED!** No more entries allowed."
        else:
            description_text += f"**Click {EMOJI_JOIN} to join!**"
        
        embed = discord.Embed(
            title=f"**{self.title}**",
            description=description_text,
            color=discord.Color.orange() if not self.is_full() else discord.Color.red()
        )
        embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL_URL)
        embed.set_image(url=GIVEAWAY_BANNER_URL)
        embed.set_footer(text=f"Giveaway • {time_left} remaining")
        return embed

async def create_repeat_winner_giveaway(bot, channel, title, description, prize, winners_count, duration_seconds, repeat_hours, forced_winners, participant_limit, fake_members_count, anti_join_count):
    view = GiveawayWinnersView(
        bot=bot, channel_id=channel.id, message_id=0,
        title=title, description=description, prize=prize,
        winners_count=winners_count, duration_seconds=duration_seconds,
        is_daily=True, repeat_hours=repeat_hours,
        forced_winners=forced_winners, participant_limit=participant_limit,
        fake_members_count=fake_members_count,
        anti_join_count=anti_join_count
    )
    embed = view.get_embed()
    message = await channel.send(embed=embed, view=view)
    view.set_message_id(message.id)

def setup_giveaway_winner(bot):
    
    @bot.tree.command(name="giveaway-winners", description="Create a new giveaway with custom winners")
    @app_commands.describe(
        title="Giveaway title",
        description="Giveaway description",
        prize="Prize",
        duration="Duration: 30s, 5m, 2h, 1d, 1h30m",
        winners="Number of winners (1-10)",
        channel="Channel to send giveaway",
        how_winners="Mention specific winners (they win even if not joined)",
        limit="Maximum participants (0 for unlimited)",
        fake_members="Number of fake members to add instantly",
        anti_join="Number of fake members to add gradually (auto-paced)",
        everyday="Repeat automatically? true/false",
        every_giveaway="Time between repeats: 30m, 2h, 1d, 12h (default: 24h)"
    )
    @app_commands.choices(everyday=[
        app_commands.Choice(name="true", value="true"),
        app_commands.Choice(name="false", value="false")
    ])
    async def giveaway_winners(
        interaction: discord.Interaction, title: str, description: str, prize: str,
        duration: str, winners: app_commands.Range[int, 1, 10], channel: discord.TextChannel,
        how_winners: str = "", limit: int = 0, fake_members: int = 0, anti_join: int = 0,
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
        participant_limit = limit if limit > 0 else None
        repeat_seconds = parse_duration(every_giveaway) if every_giveaway else 86400
        repeat_hours = max(1, repeat_seconds // 3600)
        
        if duration_seconds < 30:
            await interaction.response.send_message("❌ Duration must be at least 30 seconds!", ephemeral=True)
            return
        
        forced_winners = []
        if how_winners:
            mentions = re.findall(r'<@!?(\d+)>', how_winners)
            forced_winners = [int(m) for m in mentions]
        
        repeat_time_str = format_time(repeat_seconds)
        
        view = GiveawayWinnersView(
            bot=bot, channel_id=channel.id, message_id=0,
            title=title, description=description, prize=prize,
            winners_count=winners, duration_seconds=duration_seconds,
            is_daily=everyday_bool, repeat_hours=repeat_hours,
            forced_winners=forced_winners, participant_limit=participant_limit,
            fake_members_count=fake_members,
            anti_join_count=anti_join
        )
        
        embed = view.get_embed()
        confirm_msg = f"✅ Creating giveaway in {channel.mention}..."
        if everyday_bool:
            confirm_msg += f"\n🔄 This giveaway will repeat **every {repeat_time_str}** automatically!"
        if forced_winners:
            confirm_msg += f"\n👑 Forced winners: {', '.join([f'<@{w}>' for w in forced_winners])}"
        if participant_limit:
            confirm_msg += f"\n🔒 Participant limit: {participant_limit}"
        if fake_members > 0:
            confirm_msg += f"\n🎭 Instant fake members: +{fake_members}"
        if anti_join > 0:
            confirm_msg += f"\n🚀 Anti-Join: +{anti_join} members will join gradually"
        
        await interaction.response.send_message(confirm_msg, ephemeral=True)
        message = await channel.send(embed=embed, view=view)
        view.set_message_id(message.id)
        
        if everyday_bool:
            daily_giveaways = load_daily_giveaways()
            g_id = f"daily_winner_{channel.id}_{prize}_{datetime.now().timestamp()}"
            daily_giveaways[g_id] = DailyGiveawayData(
                prize=prize, duration_seconds=duration_seconds,
                winners_count=winners, channel_id=channel.id,
                next_run=(datetime.now() + timedelta(seconds=repeat_seconds)).isoformat()
            )
            save_daily_giveaways(daily_giveaways)