# bot.py
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
from moviepy.editor import VideoFileClip
from PIL import Image

# ------------------ LOAD ENV ------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("Please set DISCORD_TOKEN in your .env file.")

# ------------------ CONFIG ------------------
PREFIX = "?"
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ------------------ FLASK ------------------
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------------ HELPERS ------------------
def image_to_gif(image_path, output_path, duration=500):
    img = Image.open(image_path)
    img.save(output_path, save_all=True, append_images=[img], duration=duration, loop=0)

def video_to_gif(video_path, output_path):
    clip = VideoFileClip(video_path)
    clip = clip.resize(width=320)
    clip.write_gif(output_path, fps=10)
    clip.close()

# ------------------ BOT EVENTS ------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    keep_alive()
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Slash command sync failed: {e}")

# ------------------ PREFIX COMMAND ------------------
@bot.command(name="to_gif")
async def to_gif_prefix(ctx):
    await process_gif(ctx, ctx.message.attachments)

# ------------------ SLASH COMMAND ------------------
@bot.tree.command(name="to_gif", description="Convert an image or video to GIF")
async def to_gif_slash(interaction: discord.Interaction):
    # Slash commands don’t automatically get attachments, we handle it below
    if not interaction.data.get("attachments"):
        await interaction.response.send_message("Please attach an image or video to convert.")
        return
    attachments = interaction.data["attachments"]
    await process_gif(interaction, [discord.Attachment._from_data(att, bot) for att in attachments])

# ------------------ PROCESS FUNCTION ------------------
async def process_gif(ctx_or_interaction, attachments):
    if not attachments:
        await (ctx_or_interaction.response.send_message if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send)("Please attach an image or video.")
        return

    attachment = attachments[0]
    input_path = os.path.join(UPLOAD_FOLDER, attachment.filename)
    output_path = os.path.join(OUTPUT_FOLDER, f"{attachment.filename.split('.')[0]}.gif")

    await attachment.save(input_path)
    await (ctx_or_interaction.response.send_message if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send)("Converting to GIF...")

    try:
        if attachment.filename.lower().endswith((".mp4", ".mov", ".webm", ".mkv")):
            video_to_gif(input_path, output_path)
        elif attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
            image_to_gif(input_path, output_path)
        else:
            await (ctx_or_interaction.response.send_message if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send)("Unsupported file type.")
            return

        await (ctx_or_interaction.response.send_message if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send)(file=discord.File(output_path))
    except Exception as e:
        await (ctx_or_interaction.response.send_message if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send)(f"Error: {e}")

# ------------------ RUN BOT ------------------
bot.run(TOKEN)
