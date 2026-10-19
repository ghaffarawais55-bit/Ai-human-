import discord
from discord.ext import commands
import google.generativeai as genai
from google.generativeai.types import APIError
from gtts import gTTS
import os
import ffmpeg_downloader

class AIVoiceChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        """Commands the AI module to lock into your current active voice channel"""
        if not ctx.author.voice:
            return await ctx.send("❌ Pehle aap khud kisi voice channel (VC) mein join kijiye!")
        
        channel = ctx.author.voice.channel
        
        # Enhanced structural override to force connect past layout blocks
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect(timeout=20.0, reconnect=True)
            
        await ctx.send(f"🎙️ **Joined {channel.name}!** Ab aap `.speak [message]` use karke mujhse baat kar sakte hain.")

    @commands.command()
    async def speak(self, ctx, *, prompt: str):
        """Generates real-time Hinglish vocal tracking responses directly inside the VC"""
        if not ctx.voice_client:
            return await ctx.send("❌ Main kisi VC mein nahi hoon! Pehle `.join` type kijiye.")
        if ctx.voice_client.is_playing():
            return await ctx.send("🤫 Please wait, main abhi bol rahi hoon!")

        status_alert = await ctx.send("⚡ *Thinking...*")

        max_retries = len(self.bot.ACTIVE_KEYS) if self.bot.ACTIVE_KEYS else 1
        
        for attempt in range(max_retries):
            if not self.bot.configure_next_key():
                await status_alert.edit(content="❌ Configuration error: No valid API keys available.")
                return

            try:
                model = genai.GenerativeModel(
                    model_name='gemini-1.5-flash',
                    system_instruction="You are speaking aloud inside a Discord Voice Channel. Respond with a very short, crisp, single-sentence conversational phrase using natural Hinglish."
                )
                
                response = model.generate_content(
                    contents=prompt,
                    generation_config={"max_output_tokens": 120, "temperature": 0.7}
                )
                
                ai_vocal_text = response.text.strip()
                await status_alert.edit(content=f"🗣️ **AI:** *{ai_vocal_text}*")

                # Process text to audio accent cleanly
                tts = gTTS(text=ai_vocal_text, lang='hi', slow=False)
                filename = f"vc_stream_{ctx.guild.id}.mp3"
                tts.save(filename)

                ffmpeg_bin_path = ffmpeg_downloader.get_ffmpeg_path()
                source = discord.FFmpegPCMAudio(filename, executable=ffmpeg_bin_path)
                
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
        """Disconnects the AI bot from the active voice network loop cleanly"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 VC se disconnected! Phir milte hain.")
        else:
            await ctx.send("❌ Main kisi VC mein nahi hoon.")

async def setup(bot):
    await bot.add_cog(AIVoiceChannel(bot))
              
