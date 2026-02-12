"""
Haryanvi Artist Virality & Fan Power Agent - Main Orchestrator
Connects all 8 agents into a single pipeline.

Usage:
    from orchestrator import ArtistOrchestrator
    orch = ArtistOrchestrator()
    result = orch.process("https://youtube.com/watch?v=xxx", vibe="desi", duration_days=15)
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional

class ArtistOrchestrator:
    """Main pipeline connecting all 8 agents for Haryanvi artist content automation."""

    def __init__(self, output_base: str = "output", vizard_api_key: str = None):
        self.output_base = output_base
        self.vizard_api_key = vizard_api_key or os.environ.get("VIZARD_API_KEY", "")

        # Lazy-load agents to avoid heavy imports on Vercel
        self._understanding = None
        self._cutter = None
        self._frame = None
        self._caption = None
        self._trend = None
        self._strategy = None
        self._posting = None
        self._memory = None
        self._vizard = None

    # --- Lazy Agent Loaders ---
    @property
    def understanding(self):
        if not self._understanding:
            from agents.understanding_agent import UnderstandingAgent
            self._understanding = UnderstandingAgent()
        return self._understanding

    @property
    def cutter(self):
        if not self._cutter:
            from agents.viral_cutter_agent import ViralCutterAgent
            self._cutter = ViralCutterAgent()
        return self._cutter

    @property
    def frame(self):
        if not self._frame:
            from agents.frame_power_agent import FramePowerAgent
            self._frame = FramePowerAgent()
        return self._frame

    @property
    def caption(self):
        if not self._caption:
            from agents.caption_agent import CaptionAgent
            self._caption = CaptionAgent()
        return self._caption

    @property
    def trend(self):
        if not self._trend:
            from agents.trend_agent import TrendAgent
            self._trend = TrendAgent()
        return self._trend

    @property
    def strategy(self):
        if not self._strategy:
            from agents.strategy_brain import StrategyBrain
            self._strategy = StrategyBrain()
        return self._strategy

    @property
    def posting(self):
        if not self._posting:
            from agents.auto_posting_agent import AutoPostingAgent
            self._posting = AutoPostingAgent()
        return self._posting

    @property
    def memory(self):
        if not self._memory:
            from agents.memory_agent import MemoryAgent
            self._memory = MemoryAgent()
        return self._memory

    @property
    def vizard(self):
        if not self._vizard and self.vizard_api_key:
            from agents.vizard_agent import VizardAgent
            self._vizard = VizardAgent(api_key=self.vizard_api_key)
        return self._vizard

    def process(self, video_source: str, vibe: str = "desi",
                duration_days: int = 15, note: str = "",
                use_cloud: bool = False, project_id: str = None) -> dict:
        """
        Full pipeline: Video -> Understanding -> Clips -> Frames -> Captions -> Strategy -> Calendar

        Args:
            video_source: YouTube URL or local file path
            vibe: Content mood (desi, sad, akad, gaon, romantic, party)
            duration_days: Content calendar span
            note: Optional artist instruction
            use_cloud: Use Vizard AI for cloud clipping
            project_id: Unique project identifier

        Returns:
            dict with all pipeline outputs
        """
        if not project_id:
            import uuid
            project_id = f"BIRU_{uuid.uuid4().hex[:8]}"

        work_dir = os.path.join(self.output_base, project_id)
        os.makedirs(work_dir, exist_ok=True)

        result = {
            "project_id": project_id,
            "source": video_source,
            "vibe": vibe,
            "status": "started",
            "steps": {},
            "errors": []
        }

        # --- CLOUD PATH (Vizard) ---
        if use_cloud and self.vizard:
            return self._process_cloud(video_source, project_id, result)

        # --- LOCAL PATH (Full Pipeline) ---
        return self._process_local(video_source, work_dir, vibe, duration_days, note, result)

    def _process_cloud(self, url: str, project_id: str, result: dict) -> dict:
        """Cloud processing via Vizard AI"""
        try:
            vizard_id = self.vizard.submit_video(url, project_name=project_id)
            if vizard_id:
                result["status"] = "processing_cloud"
                result["vizard_project_id"] = vizard_id
                result["steps"]["vizard_submit"] = "success"
            else:
                result["status"] = "failed"
                result["errors"].append("Vizard submission returned no project ID")
        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(f"Vizard: {str(e)}")
        return result

    def _process_local(self, video_source: str, work_dir: str,
                       vibe: str, duration_days: int, note: str, result: dict) -> dict:
        """Full local pipeline with all 8 agents"""

        clips_dir = os.path.join(work_dir, "clips")
        reels_dir = os.path.join(work_dir, "reels")
        posters_dir = os.path.join(work_dir, "posters")
        os.makedirs(clips_dir, exist_ok=True)
        os.makedirs(reels_dir, exist_ok=True)
        os.makedirs(posters_dir, exist_ok=True)

        video_path = video_source
        analysis_path = os.path.join(work_dir, "analysis.json")

        # STEP 0: Download if URL
        if video_path.startswith("http"):
            print(f"[ORCHESTRATOR] Downloading: {video_path}")
            try:
                video_path = self._download_video(video_path, work_dir)
                result["steps"]["download"] = "success"
            except Exception as e:
                result["status"] = "failed"
                result["errors"].append(f"Download: {str(e)}")
                return result

        if not os.path.exists(video_path):
            result["status"] = "failed"
            result["errors"].append(f"Video not found: {video_path}")
            return result

        # STEP 1: Understanding Agent
        print("[ORCHESTRATOR] Step 1: Understanding Agent...")
        try:
            if os.path.exists(analysis_path):
                with open(analysis_path, "r", encoding="utf-8") as f:
                    understanding_data = json.load(f)
                print("[ORCHESTRATOR] Loaded cached analysis.")
            else:
                audio_path = self.understanding.extract_audio(video_path)
                transcription = self.understanding.transcribe_with_timestamps(audio_path)
                beat_analysis = self.understanding.detect_beat_drops(audio_path)

                segments = transcription.get("segments", [])
                tagged_segments = self.understanding.tag_emotions(segments)

                understanding_data = {
                    "lyrics_segments": tagged_segments,
                    "beat_analysis": beat_analysis
                }

                chorus = self.understanding.find_chorus(tagged_segments)
                if chorus:
                    understanding_data["beat_analysis"]["chorus_timestamps"] = chorus["timestamps"]

                with open(analysis_path, "w", encoding="utf-8") as f:
                    json.dump(understanding_data, f, indent=2, ensure_ascii=False)

            result["steps"]["understanding"] = "success"
            result["understanding"] = {
                "segments_count": len(understanding_data.get("lyrics_segments", [])),
                "tempo": understanding_data.get("beat_analysis", {}).get("tempo", 0)
            }
        except Exception as e:
            result["errors"].append(f"Understanding: {str(e)}")
            result["steps"]["understanding"] = "failed"
            return result

        # STEP 2: Viral Cutter Agent
        print("[ORCHESTRATOR] Step 2: Viral Cutter Agent...")
        try:
            clip_specs = self.cutter.generate_clip_specs(understanding_data)
            result["steps"]["cutter"] = "success"
            result["clips_count"] = len(clip_specs)

            # Save specs
            specs_json = [vars(spec) for spec in clip_specs]
            with open(os.path.join(work_dir, "clip_specs.json"), "w", encoding="utf-8") as f:
                json.dump(specs_json, f, indent=2)

            # Cut clips using FFmpeg
            clip_files = []
            for i, spec in enumerate(clip_specs[:10]):
                clip_path = os.path.join(clips_dir, f"clip_{i+1}.mp4")
                if not os.path.exists(clip_path):
                    try:
                        self.cutter.cut_video(video_path, spec, clip_path)
                        clip_files.append(clip_path)
                    except Exception as cut_err:
                        result["errors"].append(f"Clip {i+1} cut failed: {str(cut_err)}")
                else:
                    clip_files.append(clip_path)
            result["clip_files"] = clip_files
        except Exception as e:
            result["errors"].append(f"Cutter: {str(e)}")
            result["steps"]["cutter"] = "failed"

        # STEP 3: Frame Power Agent
        print("[ORCHESTRATOR] Step 3: Frame Power Agent...")
        try:
            best_frames = self.frame.extract_key_frames(video_path, understanding_data)
            for i, frame_spec in enumerate(best_frames):
                poster_path = os.path.join(posters_dir, f"poster_{i+1}_{frame_spec.emotion_match}.jpg")
                if not os.path.exists(poster_path):
                    self.frame.create_poster_image(video_path, frame_spec, poster_path, style="desi")
            result["steps"]["frame_power"] = "success"
            result["posters_count"] = len(best_frames)
        except Exception as e:
            result["errors"].append(f"Frame Power: {str(e)}")
            result["steps"]["frame_power"] = "failed"

        # STEP 4: Caption Agent
        print("[ORCHESTRATOR] Step 4: Caption Agent...")
        try:
            all_captions = {}
            for i, spec in enumerate(clip_specs[:10]):
                spec_dict = vars(spec)
                captions = self.caption.generate_captions(spec_dict, understanding_data)
                all_captions[f"clip_{i+1}"] = captions

            with open(os.path.join(work_dir, "captions.json"), "w", encoding="utf-8") as f:
                json.dump(all_captions, f, indent=2, ensure_ascii=False)
            result["steps"]["captions"] = "success"
        except Exception as e:
            result["errors"].append(f"Captions: {str(e)}")
            result["steps"]["captions"] = "failed"

        # STEP 5: Trend Agent
        print("[ORCHESTRATOR] Step 5: Trend Agent...")
        try:
            loop = asyncio.new_event_loop()
            trend_data = loop.run_until_complete(self.trend.analyze_trends())
            loop.close()

            with open(os.path.join(work_dir, "trends.json"), "w", encoding="utf-8") as f:
                json.dump(trend_data, f, indent=2, ensure_ascii=False, default=str)
            result["steps"]["trends"] = "success"
            result["trend_insights"] = len(trend_data.get("insights", []))
        except Exception as e:
            result["errors"].append(f"Trends: {str(e)}")
            result["steps"]["trends"] = "failed"
            trend_data = {"insights": [], "recommendations": []}

        # STEP 6: Strategy Brain
        print("[ORCHESTRATOR] Step 6: Strategy Brain...")
        try:
            memory_data = self.memory.get_learning_report()
            clips_for_strategy = []
            for i, spec in enumerate(clip_specs[:10]):
                d = vars(spec)
                d["clip_id"] = f"clip_{i+1}"
                d["emotions"] = [d.get("target_audience", "general")]
                d["duration_seconds"] = d.get("end_time", 0) - d.get("start_time", 0)
                clips_for_strategy.append(d)

            strategy_output = self.strategy.make_decisions(
                clips=clips_for_strategy,
                trend_insights=trend_data.get("insights", []),
                memory_data=memory_data,
                duration_days=duration_days
            )

            with open(os.path.join(work_dir, "strategy.json"), "w", encoding="utf-8") as f:
                json.dump(strategy_output, f, indent=2, ensure_ascii=False, default=str)
            result["steps"]["strategy"] = "success"
            result["content_calendar_days"] = len(strategy_output.get("content_calendar", []))
            result["action_commands"] = strategy_output.get("action_commands", [])
        except Exception as e:
            result["errors"].append(f"Strategy: {str(e)}")
            result["steps"]["strategy"] = "failed"
            strategy_output = {}

        # STEP 7: Memory Agent - Record this run
        print("[ORCHESTRATOR] Step 7: Memory Agent...")
        try:
            for i, spec in enumerate(clip_specs[:10]):
                self.memory.record_post({
                    "clip_id": f"{result['project_id']}_clip_{i+1}",
                    "platform": spec.platform,
                    "emotion": spec.target_audience,
                    "duration_seconds": spec.end_time - spec.start_time,
                    "hook_line": spec.hook_line
                })
            result["steps"]["memory"] = "success"
        except Exception as e:
            result["errors"].append(f"Memory: {str(e)}")
            result["steps"]["memory"] = "failed"

        # STEP 8: Auto Posting Agent - Queue (approval mode)
        print("[ORCHESTRATOR] Step 8: Auto Posting Agent (queued)...")
        try:
            calendar = strategy_output.get("content_calendar", [])
            if calendar:
                result["steps"]["posting"] = "queued"
                result["posting_queue"] = len(calendar)
            else:
                result["steps"]["posting"] = "no_calendar"
        except Exception as e:
            result["errors"].append(f"Posting: {str(e)}")
            result["steps"]["posting"] = "failed"

        # --- FINAL RESULT ---
        result["status"] = "completed" if not result["errors"] else "completed_with_warnings"

        # Save full result
        with open(os.path.join(work_dir, "pipeline_result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)

        print(f"[ORCHESTRATOR] Pipeline complete! Project: {result['project_id']}")
        print(f"[ORCHESTRATOR] Clips: {result.get('clips_count', 0)} | Posters: {result.get('posters_count', 0)}")
        print(f"[ORCHESTRATOR] Calendar: {result.get('content_calendar_days', 0)} days")
        if result["errors"]:
            print(f"[ORCHESTRATOR] Warnings: {len(result['errors'])}")

        return result

    def _download_video(self, url: str, output_dir: str) -> str:
        """Download video from YouTube/URL"""
        import subprocess
        import sys
        output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

        # Try yt-dlp as module first (works when not on PATH), fallback to direct command
        commands_to_try = [
            [sys.executable, "-m", "yt_dlp", "-f", "best[ext=mp4]/best", "-o", output_template, "--no-playlist", url],
            ["yt-dlp", "-f", "best[ext=mp4]/best", "-o", output_template, "--no-playlist", url],
        ]

        for command in commands_to_try:
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
                break
            except FileNotFoundError:
                continue
        else:
            raise FileNotFoundError("yt-dlp not found. Install with: pip install yt-dlp")

        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.endswith(".mp4")]
        if not files:
            raise FileNotFoundError("Download completed but no MP4 found.")
        return max(files, key=os.path.getmtime)

    def get_project_status(self, project_id: str) -> dict:
        """Check status of a project"""
        work_dir = os.path.join(self.output_base, project_id)
        result_path = os.path.join(work_dir, "pipeline_result.json")
        if os.path.exists(result_path):
            with open(result_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"project_id": project_id, "status": "not_found"}

    def get_whatsapp_summary(self, project_id: str) -> str:
        """Generate WhatsApp-friendly summary of pipeline results"""
        status = self.get_project_status(project_id)
        if status["status"] == "not_found":
            return f"Project {project_id} nahi mila bhai."

        msg = f"*Project: {project_id}*\n"
        msg += f"Status: {status['status']}\n\n"

        if status.get("clips_count"):
            msg += f"Clips: {status['clips_count']} banaye\n"
        if status.get("posters_count"):
            msg += f"Posters: {status['posters_count']} nikale\n"
        if status.get("content_calendar_days"):
            msg += f"Calendar: {status['content_calendar_days']} din ka plan\n"

        commands = status.get("action_commands", [])
        if commands:
            msg += "\n*Agle 3 din ka plan:*\n"
            for cmd in commands[:3]:
                msg += f"- {cmd}\n"

        if status.get("errors"):
            msg += f"\nWarnings: {len(status['errors'])}"

        return msg
