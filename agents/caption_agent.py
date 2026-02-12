import random
from typing import List, Dict

class CaptionAgent:
    def __init__(self):
        self.caption_templates = {
            "akad": [
                "Chhora {place} ka, attitude {city} ka 😏",
                "{line}... aur baat khatam 🔥",
                "Theke pe khade, duniya dekhe 👊",
                "Jaat ka kamaal, {emotion} pe jawab nahi",
                "{line} - ye line sun ke rewind nahi maara? 🎧"
            ],
            "dard": [
                "Dil toota, par chhora nahi jhuka 💔",
                "{line}... samjhe jo samjhe",
                "Yaad teri, raat meri ☕",
                "Koi sunne wala chahiye, bolne wale bahut hain"
            ],
            "gaon_pride": [
                "Gaam ki mitti, shehar ka sapna 🌾",
                "Beta {place} ka, baaki sab timepass",
                "{line} - apne gaam ki baat alag hai",
                "Desi swag, city lag 🚜"
            ],
            "pyaar": [
                "Gore gaal, kaala dil mera 😂",
                "{line}... ab samjh aaya?",
                "Tere bina chain kahan re 💕"
            ],
            "mauj": [
                "Party chal rahi hai, aaja yaar 🎉",
                "{line} - weekend mood ON",
                "Yaari dosti, baaki sab masti 🍻"
            ]
        }
        
        self.question_templates = {
            "akad": [
                "Bata chhore, teri bhi aisi koi line hai?",
                "Ye line sunke kiske yaad aaye? 😏 Tag karo",
                "Akad rakhni chahiye ya nahi? Comment karo",
                "Tera gaam kaunsa? Batade bhai"
            ],
            "dard": [
                "Tujhe bhi kisi ne aisa bola hai kya?",
                "Is line pe kitne baar rewind maara? Count batao",
                "Single ho ya complicated? 😅"
            ],
            "gaon_pride": [
                "Tera gaam kaunsa hai bhai?",
                "Gaam wale tag karo apne aap ko 🙋‍♂️",
                "Shehar better ya gaam? Ladai karo comments mein"
            ],
            "general": [
                "Ye gaana kitni baar suna? Honestly batao",
                "Isko kisne pehle discover kiya? OG fans batao",
                "Aur kaunsa gaana banaun? Request karo"
            ]
        }
        
    def generate_captions(self, clip_data: dict, understanding_data: dict) -> Dict:
        """Clip ke liye captions generate karo"""
        # Extract emotion from clip_spec data (passed as dict here)
        # Note: clip_data here expects the dictionary form of ClipSpec from process_video.py
        
        # We need to map the viral_reason or target_audience to an emotion if not explicitly present
        # In process_video, we might not have 'emotions' directly in ClipSpec, 
        # but we can infer or pass it. 
        # For now, let's assume clip_data has an 'emotion' field or we derive it.
        
        # Fallback logic if emotion is missing
        emotions = clip_data.get("emotions", [])
        if not emotions:
             # Try to infer from viral_reason or target_audience
             audience = clip_data.get("target_audience", "")
             if "ladke" in audience: emotions = ["akad"]
             elif "sad" in audience: emotions = ["dard"]
             elif "couple" in audience: emotions = ["pyaar"]
             elif "party" in audience: emotions = ["mauj"]
             elif "gaon" in audience: emotions = ["gaon_pride"]
             else: emotions = ["general"]

        hook_line = clip_data.get("hook_line", "")
        
        # Select emotion-appropriate templates
        primary_emotion = emotions[0] if emotions else "general"
        
        # Fallback to 'akad' if general or unknown
        templates = self.caption_templates.get(primary_emotion, self.caption_templates["akad"])
        
        # Generate 2 caption variations
        captions = []
        for _ in range(2):
            template = random.choice(templates)
            caption = template.format(
                line=self._shorten_line(hook_line),
                place="Haryana",
                city="Delhi",
                emotion=primary_emotion
            )
            captions.append(caption)
        
        # Generate engagement question
        question_templates = self.question_templates.get(primary_emotion, self.question_templates["general"])
        engagement_question = random.choice(question_templates)
        
        return {
            "captions": captions,
            "engagement_question": engagement_question,
            "hashtags": self._generate_hashtags(primary_emotion, understanding_data)
        }
    
    def _shorten_line(self, line: str, max_chars: int = 40) -> str:
        """Line ko short karo for caption"""
        if not line: return "Yeh line"
        if len(line) <= max_chars:
            return line
        return line[:max_chars-3] + "..."
    
    def _generate_hashtags(self, emotion: str, data: dict) -> List[str]:
        """Relevant hashtags generate karo"""
        base_tags = ["#haryanvi", "#haryanvisong", "#desisong", "#haryana"]
        
        emotion_tags = {
            "akad": ["#attitude", "#akadwala", "#chhora", "#desiboy"],
            "dard": ["#sadsong", "#dard", "#dil", "#heartbroken"],
            "gaon_pride": ["#gaam", "#desi", "#village", "#mitti"],
            "pyaar": ["#love", "#romance", "#pyaar", "#ishq"],
            "mauj": ["#party", "#yaari", "#masti", "#weekend"]
        }
        
        tags = base_tags + emotion_tags.get(emotion, [])
        
        # Add trending tags (from trend agent data if available)
        return tags[:15]  # Instagram limit-ish
    
    def generate_comment_replies(self, comment_type: str) -> List[str]:
        """Auto-reply templates for common comments"""
        replies = {
            "fire_emoji": [
                "Thankyou bhai 🔥",
                "Support karte raho 🙏",
                "Aur aayega boss 💪"
            ],
            "which_song": [
                "Gaana jaldi aara hai, subscribed raho!",
                "Ye clip {song_name} se hai bhai"
            ],
            "request": [
                "Note kar liya bhai, queue mein hai",
                "Agle gaane mein zaroor"
            ]
        }
        return replies.get(comment_type, ["❤️"])

if __name__ == "__main__":
    agent = CaptionAgent()
    print("Caption Agent initialized.")
