import discord
from discord.ext import commands
import os
import json
import datetime
from google import genai
from google.genai import types

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Initialize the new Google GenAI Client smoothly
# Make sure to add GEMINI_API_KEY inside your Railway environment variables!
ai_client = genai.Client()

MEMORY_FILE = "ai_memory.json"
user_memories = {}

# Load up persistent long-term storage strings
if os.path.exists(MEMORY_FILE):
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            user_memories = json.load(f)
    except:
        user_memories = {}

def save_chat_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(user_memories, f, ensure_ascii=False, indent=4)

@bot.event
async def on_ready():
    print(f"🧠 {bot.user.name} AI Core Engine is online and lightning fast!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your messages"))
    
    # Dynamically load the isolated fast voice extension module file
    try:
        await bot.load_extension("ai_voice")
        print("🎙️ AI Voice Client tracking loaded cleanly.")
    except Exception as e:
        print(f"❌ Voice loading runtime fallback caught: {e}")

@bot.event
async def on_message(message):
    # Ignore signals firing from the bot itself
    if message.author.bot:
        return

    # Let normal prefix commands bypass the raw chat listener checks
    if message.content.startswith("."):
        await bot.process_commands(message)
        return

    # Trigger custom chat routing if the bot gets tagged or mentioned directly
    if bot.user.mentioned_in(message):
        clean_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_prompt:
            await message.reply("Haan ji? Boliyen, I'm listening! 😊")
            return

        async with message.channel.typing():
            user_id = str(message.author.id)
            
            # Fetch past conversation log history chunks
            if user_id not in user_memories:
                user_memories[user_id] = []
            
            # Append current message text layout
            user_memories[user_id].append({"role": "user", "text": clean_prompt})
            
            # Format context to preserve structural historical retention loops
            context_history = ""
            # Pass up to the last 12 turns to stay highly responsive and fast
            for past_turn in user_memories[user_id][-12:]:
                speaker = "User" if past_turn["role"] == "user" else "AI"
                context_history += f"{speaker}: {past_turn['text']}\n"

            # Construct the system instruction prompt
            system_instruction = (
                "You are a friendly, highly intelligent, and expressive human-like AI companion named Cypher. "
                "You must speak naturally in everyday conversational Hinglish (a casual mixture of Hindi and English words), "
                "the way close friends text each other in India/Pakistan. Avoid sounding mechanical or using formal translation layers. "
                "Keep your answers punchy, helpful, and fast. Refer to past contexts if the user brings up old themes."
            )

            try:
                # Use the ultra-fast gemini-2.5-flash production model
                response = ai_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=f"{context_history}AI:",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        max_output_tokens=350,
                        temperature=0.72
                    )
                )
                
                ai_reply = response.text.strip()
                
                # Commit response to the user's permanent memory array map
                user_memories[user_id].append({"role": "model", "text": ai_reply})
                save_chat_memory()
                
                # Send the response back
                await message.reply(ai_reply)

            except Exception as error:
                print(f"⚠️ API Pipeline exception caught: {error}")
                await message.reply("Arre yaar, brain processing short-circuit ho gaya! Ek baar phir se try karna? 😭")

bot.run(os.getenv("DISCORD_TOKEN"))
          
