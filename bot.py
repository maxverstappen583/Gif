# bot.py
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import Attachment, File, app_commands
from flask import Flask
from threading import Thread
from PIL import Image
import imageio

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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ------------------ HELPERS ------------------
def image_to_gif(image_path, output_path, duration=500):
    img = Image.open(image_path)
    img.save(output_path, save_all=True, append_images=[img], duration=duration, loop=0)

def video_to_gif(video_path, output_path, fps=10, resize_width=320):
    reader = imageio.get_reader(video_path)
    frames = []
    for frame in reader:
        img = Image.fromarray(frame)
        w_percent = resize_width / float(img.width)
        h_size = int(float(img.height) * w_percent)
        img = img.resize((resize_width, h_size), Image.Resampling.LANCZOS)
        frames.append(img)
    reader.close()
    if frames:
        frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=int(1000/fps), loop=0)

# ------------------ EVENTS ------------------
@bot.event
async def on_ready():
    print(f"{bot.user} is online!")
    keep_alive()
    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except Exception as e:
        print(f"Slash command sync failed: {e}")

# ------------------ PREFIX COMMAND ------------------
@bot.command(name="to_gif")
async def to_gif_prefix(ctx):
    if not ctx.message.attachments:
        await ctx.send("Please attach an image or video.")
        return
    await process_gif(ctx, ctx.message.attachments)

# ------------------ SLASH COMMAND ------------------
@bot.tree.command(name="to_gif", description="Convert an image or video to GIF")
@app_commands.describe(file="Upload an image or video")
async def to_gif_slash(interaction: discord.Interaction, file: Attachment):
    if not file:
        await interaction.response.send_message("You must provide a file to convert.")
        return
    await process_gif(interaction, [file])

# ------------------ PROCESS FUNCTION ------------------
async def process_gif(ctx_or_interaction, attachments):
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

        await (ctx_or_interaction.response.send_message if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send)(file=File(output_path))
    except Exception as e:
        await (ctx_or_interaction.response.send_message if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send)(f"Error: {e}")

# ------------------ RUN BOT ------------------
bot.run(TOKEN)
