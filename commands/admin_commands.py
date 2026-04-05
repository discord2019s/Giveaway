# commands/admin_commands.py
import discord
from discord.ext import commands
import asyncio
import random
from datetime import datetime, timedelta
from config import ALLOWED_COMMAND_ROLES, GIVEAWAY_THUMBNAIL_URL, GIVEAWAY_BANNER_URL
from winner_image import get_winner_image
from utils import parse_duration, format_time
import giveaway_state

def setup_admin_commands(bot):
    
    @bot.command(name="next")
    async def next_winner(ctx):
        """!next - Select a new winner instead of the current winner"""
        if not check_permission(ctx.author):
            await ctx.send("❌ **You don't have permission to use this command!**")
            return
        
        giveaway_view = None
        for msg_id, view in giveaway_state.active_giveaways.items():
            if view.channel_id == ctx.channel.id and not view.ended:
                giveaway_view = view
                break
        
        if not giveaway_view:
            for msg_id, view in giveaway_state.winner_active_giveaways.items():
                if view.channel_id == ctx.channel.id and not view.ended:
                    giveaway_view = view
                    break
        
        if not giveaway_view:
            await ctx.send("❌ **No active giveaway in this channel!**")
            return
        
        if len(giveaway_view.participants) < 1:
            await ctx.send("❌ **No participants in this giveaway!**")
            return
        
        new_winner = random.choice(giveaway_view.participants)
        
        winner_image = get_winner_image()
        send_mode = winner_image.get("send_mode", "private")
        
        embed = discord.Embed(
            title="🎲 **NEW WINNER SELECTED!** 🎲",
            description=f"🔄 A new winner has been chosen for **{giveaway_view.prize}**!\n\n🏆 **New Winner:** <@{new_winner}>\n\n✨ Congratulations!",
            color=discord.Color.gold()
        )
        
        if winner_image["url"] and send_mode in ["server", "all"]:
            embed.set_image(url=winner_image["url"])
        
        await ctx.send(embed=embed)
        
        try:
            winner_user = await bot.fetch_user(new_winner)
            winner_embed = discord.Embed(
                title="🎉 **YOU ARE THE NEW WINNER!** 🎉",
                description=f"Congratulations! You have been selected as the new winner for:\n**{giveaway_view.prize}**\n\n📩 Please contact the staff to claim your prize!",
                color=discord.Color.gold()
            )
            if winner_image["url"] and send_mode in ["private", "all"]:
                winner_embed.set_image(url=winner_image["url"])
            await winner_user.send(embed=winner_embed)
        except:
            pass
    
    @bot.command(name="edit_time")
    async def edit_time(ctx, new_duration: str):
        """!edit_time <duration> - Change the remaining time of the giveaway"""
        if not check_permission(ctx.author):
            await ctx.send("❌ **You don't have permission to use this command!**")
            return
        
        giveaway_view = None
        for msg_id, view in giveaway_state.active_giveaways.items():
            if view.channel_id == ctx.channel.id and not view.ended:
                giveaway_view = view
                break
        
        if not giveaway_view:
            for msg_id, view in giveaway_state.winner_active_giveaways.items():
                if view.channel_id == ctx.channel.id and not view.ended:
                    giveaway_view = view
                    break
        
        if not giveaway_view:
            await ctx.send("❌ **No active giveaway in this channel!**")
            return
        
        try:
            new_seconds = parse_duration(new_duration)
            if new_seconds < 10:
                await ctx.send("❌ **Time must be at least 10 seconds!**")
                return
            
            old_time = giveaway_view.duration_seconds
            giveaway_view.duration_seconds = new_seconds
            giveaway_view.end_time = datetime.now() + timedelta(seconds=new_seconds)
            
            await giveaway_view.update_embed()
            
            await ctx.send(f"✅ **Time changed successfully!**\n⏰ From `{format_time(old_time)}` to `{format_time(new_seconds)}`")
        except Exception as e:
            await ctx.send(f"❌ **Error parsing time!**\nUse for example: `30s`, `5m`, `2h`, `1d`")
    
    @bot.command(name="ulimit")
    async def ulimit(ctx, limit: int):
        """!ulimit <number> - Change the number of winners"""
        if not check_permission(ctx.author):
            await ctx.send("❌ **You don't have permission to use this command!**")
            return
        
        giveaway_view = None
        for msg_id, view in giveaway_state.active_giveaways.items():
            if view.channel_id == ctx.channel.id and not view.ended:
                giveaway_view = view
                break
        
        if not giveaway_view:
            for msg_id, view in giveaway_state.winner_active_giveaways.items():
                if view.channel_id == ctx.channel.id and not view.ended:
                    giveaway_view = view
                    break
        
        if not giveaway_view:
            await ctx.send("❌ **No active giveaway in this channel!**")
            return
        
        if limit < 1 or limit > 50:
            await ctx.send("❌ **Number of winners must be between 1 and 50!**")
            return
        
        old_limit = giveaway_view.winners_count
        giveaway_view.winners_count = limit
        
        await giveaway_view.update_embed()
        
        await ctx.send(f"✅ **Winners count changed successfully!**\n🏆 From `{old_limit}` to `{limit}`")
    
    @bot.command(name="bothelp")
    async def bot_help(ctx):
        """!bothelp - Show all available commands"""
        embed = discord.Embed(
            title="📚 **BOT COMMANDS HELP** 📚",
            description="Here are all the available bot commands:",
            color=discord.Color.blurple()
        )
        
        embed.add_field(
            name="━━━━━━━ **SLASH COMMANDS** ━━━━━━━",
            value="",
            inline=False
        )
        
        embed.add_field(
            name="</giveaway-create:>",
            value="🎯 **Create a new giveaway**\n`/giveaway-create title: description: prize: duration: winners: channel: everyday: every_giveaway:`\n• title - Giveaway title\n• description - Giveaway description\n• prize - Prize\n• duration - Duration (30s, 5m, 2h, 1d, 1h30m)\n• winners - Number of winners (1-10)\n• channel - Channel\n• everyday - Auto repeat (true/false)\n• every_giveaway - Repeat time (30m, 2h, 1d)",
            inline=False
        )
        
        embed.add_field(
            name="</giveaway-winners:>",
            value="👑 **Create giveaway with specific winners**\n`/giveaway-winners title: description: prize: duration: winners: channel: how_winners: limit: fake_members: everyday: every_giveaway:`\n• how_winners - Specific winners (@user1 @user2)\n• limit - Max participants (0 for unlimited)\n• fake_members - Number of fake members to display",
            inline=False
        )
        
        embed.add_field(
            name="</image-winner:>",
            value="🎨 **Set winner image**\n`/image-winner option:`\n• Image - Choose image from list\n• GIF - Choose GIF from list\n• Send - Set send location (Private/Server/All)\n• False - Disable custom image\n• Preview - Preview current image",
            inline=False
        )
        
        embed.add_field(
            name="━━━━━━━ **PREFIX COMMANDS (!)** ━━━━━━━",
            value="",
            inline=False
        )
        
        embed.add_field(
            name="!next",
            value="🎲 **Select new winner**\nSelects a new winner instead of the current winner in the active giveaway",
            inline=False
        )
        
        embed.add_field(
            name="!edit_time <duration>",
            value="⏰ **Change remaining time**\nExample: `!edit_time 5m` (5 minutes), `!edit_time 30s` (30 seconds)",
            inline=False
        )
        
        embed.add_field(
            name="!ulimit <number>",
            value="🏆 **Change number of winners**\nExample: `!ulimit 5` (5 winners)",
            inline=False
        )
        
        embed.add_field(
            name="!bothelp",
            value="📚 **Show this list**\nShows all available commands with explanations",
            inline=False
        )
        
        embed.add_field(
            name="!active",
            value="📊 **Show active giveaways**\nShows all active giveaways in the current channel",
            inline=False
        )
        
        embed.add_field(
            name="━━━━━━━ **INFO** ━━━━━━━",
            value=f"📌 **Prefix:** `!`\n🔗 **Slash Commands:** `/`\n👑 **Permissions:** Admins and authorized roles only",
            inline=False
        )
        
        embed.set_footer(text="Giveaway Bot • Use commands wisely!")
        embed.set_thumbnail(url=GIVEAWAY_THUMBNAIL_URL)
        
        await ctx.send(embed=embed)
    
    @bot.command(name="active")
    async def active_giveaways_cmd(ctx):
        """!active - Show active giveaways in the channel"""
        if not check_permission(ctx.author):
            await ctx.send("❌ **You don't have permission to use this command!**")
            return
        
        active_list = []
        for msg_id, view in giveaway_state.active_giveaways.items():
            if view.channel_id == ctx.channel.id and not view.ended:
                active_list.append(view)
        
        for msg_id, view in giveaway_state.winner_active_giveaways.items():
            if view.channel_id == ctx.channel.id and not view.ended:
                active_list.append(view)
        
        if not active_list:
            await ctx.send("📭 **No active giveaways in this channel!**")
            return
        
        embed = discord.Embed(
            title="🎁 **Active Giveaways** 🎁",
            description=f"There are {len(active_list)} active giveaways in this channel:",
            color=discord.Color.green()
        )
        
        for view in active_list:
            time_left = format_time(view.duration_seconds)
            embed.add_field(
                name=f"📦 {view.title[:30]}",
                value=f"🏆 Prize: {view.prize[:30]}\n👥 Participants: {len(view.participants)}\n⏰ Time Left: {time_left}\n🏆 Winners: {view.winners_count}",
                inline=False
            )
        
        await ctx.send(embed=embed)

def check_permission(user: discord.Member) -> bool:
    """Check user permissions"""
    from config import OWNER_ID, ADMIN_ID
    
    is_owner = user.id == OWNER_ID
    is_admin_user = user.id == ADMIN_ID
    is_guild_admin = user.guild_permissions.administrator
    
    allowed_role_ids = ALLOWED_COMMAND_ROLES
    has_allowed_role = any(role.id in allowed_role_ids for role in user.roles)
    
    return is_owner or is_admin_user or is_guild_admin or has_allowed_role