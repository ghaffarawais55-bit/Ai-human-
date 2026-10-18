import discord
from discord.ext import commands
import os
import json
import datetime
from google import genai
from google.genai import types
from google.genai.errors import APIError

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ==========================================
# MULTI-KEY ROTATION CONFIGURATION
# ==========================================
# We fetch all 5 keys from your Railway environment variables
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5")
]

# Clean out any empty/None values just in case a key isn't added yet
ACTIVE_KEYS = [k for k in GEMINI_KEYS if k]
CURRENT_KEY_INDEX = 0

def get_next_ai_client():
    global CURRENT_KEY_INDEX
    if not ACTIVE_KEYS:
        print("❌ CRITICAL: No valid GEMINI_API_KEYs found in environment variables!")
        return None
        
    # Pick the current active key from the list
    selected_key = ACTIVE_KEYS[CURRENT_KEY_INDEX]
    return genai.Client(api_key=selected_key)

def rotate_key():
    global CURRENT_KEY_INDEX
    if len(ACTIVE_KEYS) > 1:
        CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(ACTIVE_KEYS)
        print(f"🔄 Rate limit hit or swap triggered! Rotating to API Key Slot #{CURRENT_KEY_INDEX + 1}")

# ==========================================
# MEMORY LOG MANAGEMENT
# ==========================================
MEMORY_FILE = "ai_memory.json"
user_memories = {}

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
    print(f"🧠 {bot.user.name} AI Core Engine is online!")
    print(f"🔑 Loaded {len(ACTIVE_KEYS)} out of 5 API Keys successfully into the pool.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your messages"))
    
    try:
        await bot.load_extension("ai_voice")
        print("🎙️ AI Voice Client tracking loaded cleanly.")
    except Exception as e:
        print(f"❌ Voice loading fallback caught: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("."):
        await bot.process_commands(message)
        return

    if bot.user.mentioned_in(message):
        clean_prompt = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not clean_prompt:
            await message.reply("Haan ji? Boliyen, I'm listening! 😊")
            return

        async with message.channel.typing():
            user_id = str(message.author.id)
            
            if user_id not in user_memories:
                user_memories[user_id] = []
            
            user_memories[user_id].append({"role": "user", "text": clean_prompt})
            
            context_history = ""
            for past_turn in user_memories[user_id][-12:]:
                speaker = "User" if past_turn["role"] == "user" else "AI"
                context_history += f"{speaker}: {past_turn['text']}\n"

            system_instruction = (
                "You are a friendly, highly intelligent, and expressive human-like AI companion named Cypher. "
                "You must speak naturally in everyday conversational Hinglish (a casual mixture of Hindi and English words), "
                "the way close friends text each other in India/Pakistan. Avoid sounding mechanical or using formal translation layers. "
                "Keep your answers punchy, helpful, and fast. Refer to past contexts if the user brings up old themes."
            )

            # Retry logic to cycle through your keys if a rate limit occurs
            max_retries = len(ACTIVE_KEYS)
            for attempt in range(max_retries):
                ai_client = get_next_ai_client()
                if not ai_client:
                    await message.reply("Arre yaar, configuration settings kharab hain. Environment values lagao.")
                    return

                try:
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
                    user_memories[user_id].append({"role": "model", "text": ai_reply})
                    save_chat_memory()
                    
                    await message.reply(ai_reply)
                    return # Action complete! Break loop entirely.

                except APIError as api_error:
                    # Check if the error code is a rate limit flag (429)
                    if api_error.code == 429:
                        rotate_key() # Swap out key instantly
                        continue # Restart loop step using next client
                    else:
                        print(f"⚠️ General API Exception: {api_error}")
                        break
                except Exception as error:
                    print(f"⚠️ Pipeline Exception: {error}")
                    break
            
            # If all attempts completely cycle and exhaust limits
            await message.reply("Arre yaar, saare API links right now busy hain! Please 1 minute baad check karna. 😭")

bot.run(os.getenv("DISCORD_TOKEN"))
      
