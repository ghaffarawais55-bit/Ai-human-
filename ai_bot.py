# ==========================================
# SYSTEM CORE VOICES & NETWORKING PATCH
# ==========================================
import sys
import types
sys.modules['davey'] = types.ModuleType('davey')

import discord
from discord.ext import commands
import os
import json
import datetime
import google.generativeai as genai
from google.generativeai.types import APIError

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# ==========================================
# MULTI-KEY ROTATION CONFIGURATION
# ==========================================
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5")
]

ACTIVE_KEYS = [k for k in GEMINI_KEYS if k]
CURRENT_KEY_INDEX = 0

def configure_next_key():
    global CURRENT_KEY_INDEX
    if not ACTIVE_KEYS:
        print("❌ CRITICAL: No valid GEMINI_API_KEYs found in variables!")
        return False
    selected_key = ACTIVE_KEYS[CURRENT_KEY_INDEX]
    genai.configure(api_key=selected_key)
    return True

def rotate_key():
    global CURRENT_KEY_INDEX
    if len(ACTIVE_KEYS) > 1:
        CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(ACTIVE_KEYS)
        print(f"🔄 Swapping key pool target index to slot #{CURRENT_KEY_INDEX + 1}")

# Export values to the global bot object for clean accessibility
bot.configure_next_key = configure_next_key
bot.rotate_key = rotate_key
bot.ACTIVE_KEYS = ACTIVE_KEYS

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
    print(f"🧠 {bot.user.name} AI Core Engine is online and optimized!")
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
            
            # Format context to preserve structural historical loops
            chat_context = []
            for past_turn in user_memories[user_id][-14:]:
                role_label = "user" if past_turn["role"] == "user" else "model"
                chat_context.append({"role": role_label, "parts": [past_turn["text"]]})

            system_instruction = (
                "You are a friendly, highly intelligent, and expressive human-like AI companion named Cypher. "
                "You must speak naturally in everyday conversational Hinglish (a casual mixture of Hindi and English words), "
                "the way close friends text each other in India/Pakistan. Avoid sounding mechanical or using formal translation layers. "
                "Keep your answers punchy, helpful, and fast. Refer to past contexts if the user brings up old themes. "
                "Never stop or cut off mid-sentence."
            )

            max_retries = len(ACTIVE_KEYS) if ACTIVE_KEYS else 1
            for attempt in range(max_retries):
                if not configure_next_key():
                    await message.reply("Arre yaar, configuration settings kharab hain.")
                    return

                try:
                    # Swapped to the ultra-reliable, lightning fast generation engine
                    model = genai.GenerativeModel(
                        model_name='gemini-1.5-flash',
                        system_instruction=system_instruction
                    )
                    
                    response = model.generate_content(
                        contents=chat_context,
                        generation_config={"max_output_tokens": 500, "temperature": 0.7}
                    )
                    
                    ai_reply = response.text.strip()
                    user_memories[user_id].append({"role": "model", "text": ai_reply})
                    save_chat_memory()
                    
                    await message.reply(ai_reply)
                    return 

                except APIError as api_error:
                    if api_error.code == 429:
                        rotate_key()
                        continue
                    else:
                        print(f"⚠️ API Exception: {api_error}")
                        break
                except Exception as error:
                    print(f"⚠️ Engine Pipeline Exception: {error}")
                    break
            
            await message.reply("Arre yaar, saare API links right now busy hain! Please 1 minute baad check karna. 😭")

bot.run(os.getenv("DISCORD_TOKEN"))
              
