import os
import shutil
import asyncio
import subprocess
import time
import sys
import logging
from neonize.client import NewClient
from neonize.events import MessageEv, ConnectedEv, QREv
from neonize.utils.jid import Jid2String
from agents import UnderstandingAgent, ViralCutterAgent

# Logging for neonize can be helpful
logging.basicConfig(level=logging.INFO)

# Initialize Agents
print("Starting Biru Bhai Agents...")
understanding_agent = UnderstandingAgent()
viral_cutter = ViralCutterAgent()

def main():
    # Use a unique name for the session
    session_name = "biru_bhai_bot"
    client = NewClient(session_name)
    
    @client.event(QREv)
    def on_qr(client: NewClient, qr: bytes):
        print("\n\n" + "="*50)
        print("🔥 NEW WHATSAPP QR CODE RECEIVED!")
        print("="*50)
        
        try:
            import segno
            qr_obj = segno.make_qr(qr)
            
            # Save to file (Most reliable for Windows)
            qr_file = "whatsapp_qr.png"
            qr_obj.save(qr_file, scale=10)
            print(f"✅ STEP 1: OPEN THIS FILE -> {os.path.abspath(qr_file)}")
            print("✅ STEP 2: SCAN WITH WHATSAPP LINKED DEVICES")
            
            # Try to show in console but don't crash if encoding fails
            try:
                if sys.platform == "win32":
                    os.system("chcp 65001 > nul")
                qr_obj.terminal(compact=True)
            except:
                print("\n[Notice] Terminal QR hidden due to encoding. Please use the 'whatsapp_qr.png' file.")
                
        except Exception as e:
            print(f"QR Error: {e}")
        print("="*50 + "\n")

    @client.event(ConnectedEv)
    def on_connected(client: NewClient, event: ConnectedEv):
        print("\n" + "!"*30)
        print("🚀 BIRU BHAI WHATSAPP CONNECTED!")
        print("!"*30 + "\n")

    @client.event(MessageEv)
    def handle_message(client: NewClient, event: MessageEv):
        # Proto attributes in neonize are often CamelCase
        msg = event.Message
        chat_id = event.Info.MessageSource.Chat
        
        # Check text
        text = str(msg.conversation or getattr(msg.extendedTextMessage, 'text', ''))
        if not text:
            return
            
        if text.startswith("/cut"):
            parts = text.split()
            if len(parts) < 2:
                client.send_message(chat_id, "❌ Bhejo link! Example: /cut <URL> [count]")
                return
                
            url = parts[1]
            count = int(parts[2]) if len(parts) > 2 else 3
            
            client.send_message(chat_id, f"🚀 *Processing Video!* (Clips: {count})\nBiru Bhai active hai! 🦾")
            
            output_temp = "output/wa_temp"
            os.makedirs(output_temp, exist_ok=True)
            
            try:
                # 1. Download
                client.send_message(chat_id, "🌐 Downloading...")
                command = ['yt-dlp', '-f', 'best[ext=mp4]/best', '-o', f'{output_temp}/%(title)s.%(ext)s', '--no-playlist', url]
                subprocess.run(command, check=True)
                
                files = [os.path.join(output_temp, f) for f in os.listdir(output_temp) if f.endswith('.mp4')]
                if not files:
                    client.send_message(chat_id, "❌ Download failed.")
                    return
                video_path = max(files, key=os.path.getmtime)

                # 2. Analysis
                client.send_message(chat_id, "🧠 Generating Viral Clips...")
                audio_path = understanding_agent.extract_audio(video_path)
                transcription = understanding_agent.transcribe_with_timestamps(audio_path)
                beat_analysis = understanding_agent.detect_beat_drops(audio_path)
                
                understanding_data = {
                    "lyrics_segments": understanding_agent.tag_emotions(transcription.get('segments', [])),
                    "beat_analysis": beat_analysis
                }
                
                # 3. Cut
                clip_specs = viral_cutter.generate_clip_specs(understanding_data)
                if not clip_specs:
                    client.send_message(chat_id, "❌ No clips found.")
                    return

                client.send_message(chat_id, f"🔥 Found {len(clip_specs)} clips. Sending top {count}...")
                
                for i, spec in enumerate(clip_specs[:count]):
                    clip_path = os.path.join("output", "clips", f"wa_clip_{i+1}.mp4")
                    os.makedirs(os.path.dirname(clip_path), exist_ok=True)
                    viral_cutter.cut_video(video_path, spec, clip_path)
                    
                    if os.path.exists(clip_path):
                        client.send_message(chat_id, f"✅ *Clip #{i+1}*: {spec.viral_reason}")
                        with open(clip_path, "rb") as f:
                            client.send_video(chat_id, f.read(), caption=f"Biru Bhai Clip #{i+1}")
                    
                client.send_message(chat_id, "🏁 *Task Complete!* Enjoy. 🚜")
                
            except Exception as e:
                client.send_message(chat_id, f"❌ Error: {str(e)}")
            finally:
                if os.path.exists(output_temp):
                    shutil.rmtree(output_temp, ignore_errors=True)

        elif text == "/start":
            client.send_message(chat_id, "👋 *Biru Bhai WhatsApp* Online!\n\nUse `/cut URL [count]` to generate reels.")

    print("\n[System] Starting WhatsApp Link Process...")
    client.connect()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
