import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
from gtts import gTTS
import asyncio

class AIVoiceChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ai_client = genai.Client()

    @commands.command()
    async def join(self, ctx):
        """Commands the AI module to lock into your current active voice channel"""
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
        """Generates real-time Hinglish vocal tracking responses directly inside the VC channel link"""
        if not ctx.voice_client:
            return await ctx.send("❌ Main kisi VC mein nahi hoon! Pehle `.join` type kijiye.")
        
        if ctx.voice_client.is_playing():
            return await ctx.send("🤫 Please wait, main abhi bol rahi hoon!")

        status_alert = await ctx.send("⚡ *Thinking...*")

        try:
            # Query the fast Flash infrastructure
            response = self.ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are speaking aloud inside a Discord Voice Channel. Respond with a very short, crisp, single-sentence conversational phrase using natural Hinglish.",
                    max_output_tokens=100
                )
            )
            ai_vocal_text = response.text.strip()
            await status_alert.edit(content=f"🗣️ **AI:** *{ai_vocal_text}*")

            # Convert text to audio in Hindi/Hinglish accent context via gTTS
            tts = gTTS(text=ai_vocal_text, lang='hi', slow=False)
            filename = f"vc_stream_{ctx.guild.id}.mp3"
            tts.save(filename)

            # Play audio file through Discord's audio client engine seamlessly
            source = discord.FFmpegPCMAudio(filename)
            ctx.voice_client.play(source, after=lambda e: os.remove(filename) if os.path.exists(filename) else None)

        except Exception as error:
            print(f"❌ Voice runtime error: {error}")
            await ctx.send("⚠️ Voice convert karne mein thodi problem aayi yaar.")

    @commands.command()
    async def leave(self, ctx):
        """Disconnects the AI bot from the active voice network loop cleanly"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 VC se disconnected! Phir milte hain.")
        else:
            await ctx.send("❌ Main kisi VC mein nahi hoon.")

async def setup(bot):
    await bot.add_cog(AIVoiceChannel(bot))
  
