import discord
from discord.ext import commands
import datetime
import random
from gtts import gTTS
import os
from google.genai.errors import APIError

class AIVoiceChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("❌ Pehle aap khud kisi voice channel (VC) mein join kijiye!")
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send(f"🎙️ **Joined {channel.name}!** Ab aap `.speak [message]` use karke mujhse baat kar sakte hain.")

    @commands.command()
    async def speak(self, ctx, *, prompt: str):
        if not ctx.voice_client:
            return await ctx.send("❌ Main kisi VC mein nahi hoon! Pehle `.join` type kijiye.")
        if ctx.voice_client.is_playing():
            return await ctx.send("🤫 Please wait, main abhi bol rahi hoon!")

        status_alert = await ctx.send("⚡ *Thinking...*")

        # Safely extract core rotation attributes bound directly to the master bot instance
        max_retries = len(self.bot.ACTIVE_KEYS) if self.bot.ACTIVE_KEYS else 1
        
        for attempt in range(max_retries):
            ai_client = self.bot.get_next_ai_client()
            if not ai_client:
                await status_alert.edit(content="❌ Configuration error: No valid API keys available.")
                return

            try:
                from google.genai import types
                # UPGRADED: Running on updated gemini-3.8-flash infrastructure
                response = ai_client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are speaking aloud inside a Discord Voice Channel. Respond with a very short, crisp, single-sentence conversational phrase using natural Hinglish.",
                        max_output_tokens=100
                    )
                )
                ai_vocal_text = response.text.strip()
                await status_alert.edit(content=f"🗣️ **AI:** *{ai_vocal_text}*")

                tts = gTTS(text=ai_vocal_text, lang='hi', slow=False)
                filename = f"vc_stream_{ctx.guild.id}.mp3"
                tts.save(filename)

                source = discord.FFmpegPCMAudio(filename)
                ctx.voice_client.play(source, after=lambda e: os.remove(filename) if os.path.exists(filename) else None)
                return  

            except APIError as api_error:
                if api_error.code == 429:
                    self.bot.rotate_key()  
                    continue  
                else:
                    print(f"❌ Voice module API Exception: {api_error}")
                    await status_alert.edit(content="⚠️ Output generation stream error.")
                    return
            except Exception as error:
                print(f"❌ Voice client runtime exception: {error}")
                await status_alert.edit(content="⚠️ Voice structure engine encountered an error.")
                return

        await status_alert.edit(content="Arre yaar, saare API links right now busy hain! 😭")

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 VC se disconnected! Phir milte hain.")
        else:
            await ctx.send("❌ Main kisi VC mein nahi hoon.")

async def setup(bot):
    await bot.add_cog(AIVoiceChannel(bot))
  
