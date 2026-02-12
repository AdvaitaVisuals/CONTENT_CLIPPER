import argparse
import os
import json
import subprocess
import shutil
import imageio_ffmpeg
from agents import UnderstandingAgent, ViralCutterAgent, FramePowerAgent, CaptionAgent

# Ensure FFmpeg is in PATH for Whisper and other libraries
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(ffmpeg_exe)
if ffmpeg_dir not in os.environ["PATH"]:
    print(f"Adding FFmpeg to PATH: {ffmpeg_dir}")
    os.environ["PATH"] += os.pathsep + ffmpeg_dir

def download_youtube_video(url, output_dir):
    """Downloads a YouTube video using yt-dlp."""
    print(f"Downloading video from {url}...")
    try:
        # Construct the output template for yt-dlp
        output_template = os.path.join(output_dir, '%(title)s.%(ext)s')
        
        # Run yt-dlp command
        # CHANGED: 'best[ext=mp4]' usually ensures a single file with both video and audio.
        # 'bestvideo+bestaudio' requires ffmpeg to merge, which might be missing in PATH.
        command = [
            'yt-dlp', 
            '-f', 'best[ext=mp4]/best', 
            '-o', output_template, 
            '--no-playlist',
            url
        ]
        
        # Capture output to find the filename
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        # Find the downloaded file
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith('.mp4')]
        if not files:
             raise FileNotFoundError("Download completed but no MP4 file found.")
             
        # Return the most recently modified file
        newest_file = max(files, key=os.path.getmtime)
        print(f"Downloaded to: {newest_file}")
        return newest_file

    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e.stderr}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Process video for viral clips using Understanding, Viral Cutter, Frame Power, and Caption agents.")
    parser.add_argument("video_source", help="Path to the input video file (mp4) OR a YouTube URL")
    parser.add_argument("--output_dir", default="output", help="Directory to save clips")
    
    args = parser.parse_args()
    
    # Create output directory first
    os.makedirs(args.output_dir, exist_ok=True)
    clips_dir = os.path.join(args.output_dir, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    posters_dir = os.path.join(args.output_dir, "posters")
    os.makedirs(posters_dir, exist_ok=True)

    video_path = args.video_source

    # Check if input is a URL
    if video_path.startswith("http://") or video_path.startswith("https://") or "youtube.com" in video_path or "youtu.be" in video_path:
        # Check if video already downloaded
        existing_mp4s = [os.path.join(args.output_dir, f) for f in os.listdir(args.output_dir) if f.endswith('.mp4')]
        if existing_mp4s:
            video_path = max(existing_mp4s, key=os.path.getmtime)
            print(f"Using already downloaded video: {video_path}")
        else:
            try:
                video_path = download_youtube_video(video_path, args.output_dir)
            except Exception:
                return # Exit on download failure
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return
    
    print("Initializing agents...")
    understanding_agent = UnderstandingAgent()
    viral_cutter = ViralCutterAgent()
    frame_power = FramePowerAgent()
    caption_agent = CaptionAgent()
    
    print(f"Processing video: {video_path}")
    
    # Step 1: Extract Audio
    print("Extracting audio...")
    try:
        audio_path = understanding_agent.extract_audio(video_path)
    except Exception as e:
        print(f"Error extracting audio: {e}")
        return

    # Step 2: Understand Content
    print("Transcribing and analyzing audio (this may take a while)...")
    try:
        if os.path.exists(os.path.join(args.output_dir, "analysis.json")):
             print("Loading existing analysis...")
             with open(os.path.join(args.output_dir, "analysis.json"), "r", encoding="utf-8") as f:
                 understanding_data = json.load(f)
        else:
            transcription = understanding_agent.transcribe_with_timestamps(audio_path)
            beat_analysis = understanding_agent.detect_beat_drops(audio_path)
            
            # Prepare data for understanding agent
            segments = transcription.get('segments', [])
            tagged_segments = understanding_agent.tag_emotions(segments)
            
            understanding_data = {
                "lyrics_segments": tagged_segments,
                "beat_analysis": beat_analysis
            }
            
            # Check for chorus
            chorus = understanding_agent.find_chorus(tagged_segments)
            if chorus:
                understanding_data["beat_analysis"]["chorus_timestamps"] = chorus["timestamps"]
                print(f"Chorus detected: '{chorus['text']}' (x{chorus['count']})")
            
            # Save analysis for debugging
            with open(os.path.join(args.output_dir, "analysis.json"), "w", encoding="utf-8") as f:
                json.dump(understanding_data, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error in understanding phase: {e}")
        return

    # Step 3: Generate Clips
    print("Generating clip specifications...")
    try:
        clip_specs = viral_cutter.generate_clip_specs(understanding_data)
        print(f"Generated {len(clip_specs)} potential clips.")
        
        # Save clip specs
        with open(os.path.join(args.output_dir, "clip_specs.json"), "w", encoding="utf-8") as f:
            # Convert dataclass to dict for json serialization (simple approach)
            specs_json = [vars(spec) for spec in clip_specs]
            json.dump(specs_json, f, indent=2)
            
    except Exception as e:
        print(f"Error generating clip specs: {e}")
        return

    # Step 4: Render 9:16 Reels via Remotion with TikTok-style captions
    # Collect all word-level timestamps for captions
    all_words = []
    for seg in understanding_data.get("lyrics_segments", []):
        for w in seg.get("words", []):
            all_words.append({
                "word": w["word"],
                "start": w["start"],
                "end": w["end"]
            })

    reels_dir = os.path.join(args.output_dir, "reels")
    os.makedirs(reels_dir, exist_ok=True)
    remotion_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remotion")
    remotion_public = os.path.join(remotion_dir, "public")
    os.makedirs(remotion_public, exist_ok=True)

    # Copy source video into Remotion's public dir (staticFile requires it)
    video_public_name = "source.mp4"
    video_public_path = os.path.join(remotion_public, video_public_name)
    if not os.path.exists(video_public_path):
        print("Copying video to Remotion public dir...")
        shutil.copy2(os.path.abspath(video_path), video_public_path)

    # Ensure Node.js is in PATH for Remotion
    npx_path = shutil.which("npx")
    if not npx_path:
        # Try common Node.js install locations on Windows
        for node_dir in [r"C:\Program Files\nodejs", r"C:\Program Files (x86)\nodejs"]:
            if os.path.exists(os.path.join(node_dir, "npx.cmd")):
                os.environ["PATH"] += os.pathsep + node_dir
                npx_path = os.path.join(node_dir, "npx.cmd")
                break
    if not npx_path:
        print("Warning: npx not found. Remotion rendering unavailable, using ffmpeg fallback.")
    else:
        print(f"Using npx at: {npx_path}")

    print(f"Rendering top {min(len(clip_specs), 10)} Instagram Reels (9:16 via Remotion)...")
    captions_data = {}

    for i, spec in enumerate(clip_specs[:10]):
        clip_name = f"reel_{i+1}_{spec.platform}_{spec.viral_reason[:10].replace(' ', '_')}"
        output_filename = f"{clip_name}.mp4"
        output_path = os.path.join(reels_dir, output_filename)

        # Caption Generation
        try:
            spec_dict = vars(spec)
            captions = caption_agent.generate_captions(spec_dict, understanding_data)
            captions_data[clip_name] = captions
        except Exception as e:
            print(f"Error generating captions for clip {i+1}: {e}")
            captions = {}

        # Skip if already rendered
        if os.path.exists(output_path):
            print(f"Reel {i+1} already exists, skipping.")
            continue

        print(f"Rendering reel {i+1}/{min(len(clip_specs), 10)}: {spec.viral_reason} ({spec.start_time:.1f}s - {spec.end_time:.1f}s)")

        # Build Remotion props
        props = {
            "videoSrc": video_public_name,
            "startTimeSec": spec.start_time,
            "endTimeSec": spec.end_time,
            "words": all_words,
            "hookLine": spec.hook_line if spec.hook_line != "Chorus Loop" else ""
        }

        props_path = os.path.join(args.output_dir, f"_props_{i+1}.json")
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, ensure_ascii=False)

        # Render via Remotion
        try:
            if not npx_path:
                raise FileNotFoundError("npx not available")
            render_cmd = [
                npx_path, "remotion", "render",
                "InstaReel",
                "--props", os.path.abspath(props_path),
                "--output", os.path.abspath(output_path),
                "--codec", "h264",
            ]
            subprocess.run(render_cmd, check=True, cwd=remotion_dir, shell=True)
            print(f"Reel saved: {output_path}")
        except Exception as e:
            print(f"Failed to render reel {i+1}: {e}")
            # Fallback: cut with ffmpeg (no 9:16 crop but at least produces a clip)
            fallback_path = os.path.join(clips_dir, f"clip_{i+1}_fallback.mp4")
            try:
                viral_cutter.cut_video(video_path, spec, fallback_path)
                print(f"Fallback clip saved: {fallback_path}")
            except Exception as e2:
                print(f"Fallback also failed: {e2}")

        # Clean up temp props file
        if os.path.exists(props_path):
            os.remove(props_path)

    # Save captions
    if captions_data:
        with open(os.path.join(args.output_dir, "captions.json"), "w", encoding="utf-8") as f:
            json.dump(captions_data, f, indent=2, ensure_ascii=False)

    # Step 5: Extract Posters
    print("Extracting high-quality posters...")
    try:
        if os.path.exists(os.path.join(posters_dir, "poster_1_akad.jpg")): # Simple check to avoid redo
             print("Posters might already exist, checking...")
        
        best_frames = frame_power.extract_key_frames(video_path, understanding_data)
        print(f"Found {len(best_frames)} high-quality frames.")
        
        for i, frame_spec in enumerate(best_frames):
            poster_filename = f"poster_{i+1}_{frame_spec.emotion_match}.jpg"
            poster_path = os.path.join(posters_dir, poster_filename)
            
            if not os.path.exists(poster_path):
                frame_power.create_poster_image(video_path, frame_spec, poster_path, style="desi")
            
    except Exception as e:
        print(f"Error extracting posters: {e}")

    print("\nProcessing complete!")
    print(f"Analysis saved to: {os.path.join(args.output_dir, 'analysis.json')}")
    print(f"9:16 Reels saved to: {reels_dir}")
    print(f"Captions saved to: {os.path.join(args.output_dir, 'captions.json')}")
    print(f"Posters saved to: {posters_dir}")

if __name__ == "__main__":
    main()
