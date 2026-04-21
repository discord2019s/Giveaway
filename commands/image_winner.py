# commands/image_winner.py
import discord
from discord.ext import commands
from discord import app_commands
from config import ALLOWED_COMMAND_ROLES
from winner_image import get_winner_image, set_winner_image, clear_winner_image, set_send_mode

IMAGES = {
    "SpongeBob-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235683221274715/77120d8d3186c9dce155cffac03e92b3.jpg?ex=69d351a2&is=69d20022&hm=397cf107f916d49a40b67dab58a5c5717f94d47d6e3c9df190068bbe1f5b152a&",
    "SpongeBob-give-crab-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235682667499581/06b2fdbf320435fdbc0f0ccbe4395d7b.jpg?ex=69d351a1&is=69d20021&hm=2cc3531cb26da998bbcc1401663e1da2c1a3b83df602a4176551ab7fa91e77fb&",
    "cat-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235687130107934/0f49fb9c878d9fff5ed8232fc559d6c6.jpg?ex=69d351a3&is=69d20023&hm=38e6e515561da7bd32792f0c35ac132d69e72c45aa13fc6c3c277c6be6dbda23&",
    "cat-sigma-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235682222772264/ca918f83730cfbdcd951d64380308b10_1.jpg?ex=69d351a1&is=69d20021&hm=310db7c2af0852cf8292196c4eadeea5cd048e33a048d1c84f95800dc05af0d1&",
    "crab-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235687327367278/c48b1bedcef71689757ef0e0f19fcfdd.jpg?ex=69d351a3&is=69d20023&hm=eba726be8241d41575268428a7a1f1d47c629d510d178f0eed0742aafc1ac56e&",
    "girl-tory-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235682998718544/18a2b471db020d0674aa2e4c85556239.jpg?ex=69d351a2&is=69d20022&hm=058a7551312feac28c6945f4d260f78b10e4debdcf12e7c5c6b60f38076844f2&"
}

GIFS = {
    "crab-king-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235680021024900/34858f85a6a1d1aa7f39f5fc74ce7d04.gif?ex=69d351a1&is=69d20021&hm=78edcae0561d160d9c9b63a4536603ebecd9fd58670ba947cf2d2a1706c96209&",
    "duck-swim-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235680947703828/faaaf069bea3f60ef40eb4e242f124dc.gif?ex=69d351a1&is=69d20021&hm=175d4c28da43ecd72916ad69dda7f233ce0853df29f412781150ab8d83c852b2&",
    "duck-sigma-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235681878970368/1f47dc697c60890be0fa28b27309fa21.gif?ex=69d351a1&is=69d20021&hm=e8f3d765afb97936b826e6c15a0ad19c67a70af0293e3c09b87a7f732e3c761f&",
    "rabbit-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235681333838004/16cf39d045417e86679d30261577be8b.gif?ex=69d351a1&is=69d20021&hm=53d23a3f9fd0c6678e938cd1e8ef49d5a12353a452057ba33b1d0bafacd8a5ab&",
    "Benson-money": "https://cdn.discordapp.com/attachments/1488826553201852468/1490235680385663066/3984e8769e417fd37f76ed0d650e37e7_1.gif?ex=69d351a1&is=69d20021&hm=71f3e82abad1a66b0fba61c58df71e3609c33141813534aa061c5a94c563b337&"
}

class ImageSelect(discord.ui.Select):
    def __init__(self, image_dict: dict, image_type: str):
        options = []
        for name in image_dict.keys():
            options.append(discord.SelectOption(
                label=name[:100],
                description=f"{image_type} winner image",
                emoji="🖼️" if image_type == "Image" else "🎞️"
            ))
        
        super().__init__(
            placeholder=f"Choose a {image_type} for winners...",
            options=options[:25],
            min_values=1,
            max_values=1
        )
        self.image_dict = image_dict
        self.image_type = image_type
    
    async def callback(self, interaction: discord.Interaction):
        selected_name = self.values[0]
        image_url = self.image_dict[selected_name]
        
        current = get_winner_image()
        send_mode = current.get("send_mode", "private")
        
        set_winner_image(selected_name, image_url, self.image_type.lower(), send_mode)
        
        mode_text = {
            "private": "📩 Private (DM)",
            "server": "📢 Server (Channel)",
            "all": "📩+📢 Both"
        }.get(send_mode, "📩 Private")
        
        embed = discord.Embed(
            title="✅ **Winner Image Set!**",
            description=f"Successfully set winner image to:\n📛 **Name:** `{selected_name}`\n🎞️ **Type:** {self.image_type}\n📤 **Send Mode:** {mode_text}\n\n🖼️ **Preview:**",
            color=discord.Color.green()
        )
        embed.set_image(url=image_url)
        embed.set_footer(text="This image will be sent to all future giveaway winners")
        
        await interaction.response.edit_message(embed=embed, view=None)

def setup_image_winner(bot):
    
    @bot.tree.command(name="image-winner", description="Set a custom image/GIF to send to all giveaway winners")
    @app_commands.describe(
        option="Choose an option: Image, GIF, Send Mode, False, or Preview"
    )
    @app_commands.choices(option=[
        app_commands.Choice(name="Image - Choose from images", value="image"),
        app_commands.Choice(name="GIF - Choose from animated GIFs", value="gif"),
        app_commands.Choice(name="Send - Set where to send the image", value="send"),
        app_commands.Choice(name="False - Disable custom image", value="false"),
        app_commands.Choice(name="Preview - Preview current image", value="preview")
    ])
    async def image_winner(
        interaction: discord.Interaction,
        option: str
    ):
        user_role_ids = [role.id for role in interaction.user.roles]
        has_permission = any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids)
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (has_permission or is_admin):
            await interaction.response.send_message("❌ You don't have permission to use this command!", ephemeral=True)
            return
        
        current = get_winner_image()
        
        if option == "preview":
            if not current["name"]:
                await interaction.response.send_message("❌ No winner image set! Use `/image-winner` with `Image` or `GIF` option to set one.", ephemeral=True)
                return
            
            send_mode_text = {
                "private": "📩 Private (DM)",
                "server": "📢 Server (Channel)",
                "all": "📩 + 📢 Both"
            }.get(current.get("send_mode", "private"), "Private")
            
            embed = discord.Embed(
                title="👁️ **Current Winner Image Preview**",
                description=f"📛 **Name:** `{current['name']}`\n🎞️ **Type:** {current['type'].capitalize()}\n📤 **Send Mode:** {send_mode_text}",
                color=discord.Color.blue()
            )
            embed.set_image(url=current["url"])
            embed.set_footer(text="This image will be sent to all future giveaway winners")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if option == "send":
            current_mode = current.get("send_mode", "private")
            mode_text = {
                "private": "📩 Private (DM only)",
                "server": "📢 Server (Channel only)",
                "all": "📩+📢 Both (DM + Channel)"
            }.get(current_mode, "📩 Private")
            
            embed = discord.Embed(
                title="📤 **Set Send Mode**",
                description=f"Choose where the winner image should be sent:\n\n📩 **Private** - Send only in DM to the winner\n📢 **Server** - Send only in the giveaway channel\n📩+📢 **All** - Send in both DM and server channel\n\n📌 **Current Mode:** {mode_text}",
                color=discord.Color.purple()
            )
            
            view = discord.ui.View(timeout=60)
            
            async def set_send_mode_callback(interaction: discord.Interaction, mode: str):
                set_send_mode(mode)
                
                mode_text_result = {
                    "private": "📩 Private (DM only)",
                    "server": "📢 Server (Channel only)",
                    "all": "📩+📢 Both (DM + Channel)"
                }.get(mode, mode)
                
                result_embed = discord.Embed(
                    title="✅ **Send Mode Updated!**",
                    description=f"Winner image will now be sent to:\n**{mode_text_result}**",
                    color=discord.Color.green()
                )
                
                await interaction.response.edit_message(embed=result_embed, view=None)
            
            private_button = discord.ui.Button(label="📩 Private", style=discord.ButtonStyle.primary, custom_id="private")
            private_button.callback = lambda i: set_send_mode_callback(i, "private")
            
            server_button = discord.ui.Button(label="📢 Server", style=discord.ButtonStyle.primary, custom_id="server")
            server_button.callback = lambda i: set_send_mode_callback(i, "server")
            
            all_button = discord.ui.Button(label="📩+📢 All", style=discord.ButtonStyle.success, custom_id="all")
            all_button.callback = lambda i: set_send_mode_callback(i, "all")
            
            view.add_item(private_button)
            view.add_item(server_button)
            view.add_item(all_button)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        
        if option == "false":
            clear_winner_image()
            
            embed = discord.Embed(
                title="✅ **Winner Image Disabled!**",
                description="Custom winner image has been disabled. Winners will receive the default image instead.",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if option == "image":
            embed = discord.Embed(
                title="📸 **Select Winner Image**",
                description="Choose an image from the menu below to send to winners:",
                color=discord.Color.purple()
            )
            
            if current["name"]:
                send_mode_text = {
                    "private": "📩 Private",
                    "server": "📢 Server",
                    "all": "📩+📢 Both"
                }.get(current.get("send_mode", "private"), "Private")
                
                embed.add_field(
                    name="📌 **Current Settings**",
                    value=f"📛 Image: `{current['name']}`\n📤 Send Mode: {send_mode_text}",
                    inline=False
                )
            
            view = discord.ui.View(timeout=120)
            image_select = ImageSelect(IMAGES, "Image")
            view.add_item(image_select)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        
        elif option == "gif":
            embed = discord.Embed(
                title="🎞️ **Select Winner GIF**",
                description="Choose a GIF from the menu below to send to winners:",
                color=discord.Color.purple()
            )
            
            if current["name"]:
                send_mode_text = {
                    "private": "📩 Private",
                    "server": "📢 Server",
                    "all": "📩+📢 Both"
                }.get(current.get("send_mode", "private"), "Private")
                
                embed.add_field(
                    name="📌 **Current Settings**",
                    value=f"🎞️ GIF: `{current['name']}`\n📤 Send Mode: {send_mode_text}",
                    inline=False
                )
            
            view = discord.ui.View(timeout=120)
            gif_select = ImageSelect(GIFS, "GIF")
            view.add_item(gif_select)
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)