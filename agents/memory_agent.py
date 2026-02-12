import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any
import os
import json

class MemoryAgent:
    def __init__(self, db_path: str = "artist_memory.db"):
        self.db_path = db_path
        self._init_database()
        
    def _init_database(self):
        """SQLite database initialize karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Posts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                clip_id TEXT PRIMARY KEY,
                platform TEXT,
                emotion TEXT,
                duration_seconds REAL,
                hook_line TEXT,
                posted_at TIMESTAMP,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                watch_time_avg REAL DEFAULT 0,
                engagement_rate REAL DEFAULT 0
            )
        ''')
        
        # Performance snapshots
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_id TEXT,
                snapshot_at TIMESTAMP,
                views INTEGER,
                likes INTEGER,
                comments INTEGER,
                FOREIGN KEY (clip_id) REFERENCES posts(clip_id)
            )
        ''')
        
        # Insights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_type TEXT,
                insight_text TEXT,
                confidence REAL,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def record_post(self, post_data: Dict):
        """Naya post record karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO posts 
                (clip_id, platform, emotion, duration_seconds, hook_line, posted_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                post_data['clip_id'],
                post_data.get('platform', 'unknown'),
                post_data.get('emotion', 'general'),
                post_data.get('duration_seconds', 0),
                post_data.get('hook_line', ''),
                datetime.now()
            ))
            conn.commit()
        except Exception as e:
            print(f"Error recording post: {e}")
        finally:
            conn.close()
    
    def update_performance(self, clip_id: str, metrics: Dict):
        """Performance metrics update karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate engagement rate
        views = metrics.get('views', 1)
        interactions = (
            metrics.get('likes', 0) + 
            metrics.get('comments', 0) * 2 + 
            metrics.get('shares', 0) * 3
        )
        engagement_rate = interactions / views if views > 0 else 0
        
        cursor.execute('''
            UPDATE posts SET 
                views = ?,
                likes = ?,
                comments = ?,
                shares = ?,
                watch_time_avg = ?,
                engagement_rate = ?
            WHERE clip_id = ?
        ''', (
            metrics.get('views', 0),
            metrics.get('likes', 0),
            metrics.get('comments', 0),
            metrics.get('shares', 0),
            metrics.get('watch_time_avg', 0),
            engagement_rate,
            clip_id
        ))
        
        # Add snapshot
        cursor.execute('''
            INSERT INTO performance_snapshots 
            (clip_id, snapshot_at, views, likes, comments)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            clip_id,
            datetime.now(),
            metrics.get('views', 0),
            metrics.get('likes', 0),
            metrics.get('comments', 0)
        ))
        
        conn.commit()
        conn.close()
        
        # Generate insights from new data (Mock for now)
        if engagement_rate > 0.1: # simple threshold
             self._add_insight("performance_spike", f"High engagement ({engagement_rate:.1%}) on clip {clip_id}", 0.8)

    def _add_insight(self, i_type, text, conf):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO insights (insight_type, insight_text, confidence, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (i_type, text, conf, datetime.now(), datetime.now() + timedelta(days=7)))
        conn.commit()
        conn.close()
    
    def get_emotion_performance(self) -> Dict:
        """Emotion-wise performance analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                emotion,
                COUNT(*) as post_count,
                AVG(engagement_rate) as avg_engagement,
                AVG(views) as avg_views,
                MAX(views) as max_views
            FROM posts
            GROUP BY emotion
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        return {
            row[0]: {
                "post_count": row[1],
                "avg_engagement": row[2] if row[2] else 0,
                "avg_views": row[3] if row[3] else 0,
                "max_views": row[4] if row[4] else 0
            }
            for row in results if row[0]
        }
    
    def get_learning_report(self) -> Dict:
        """Full learning report generate karo"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recent insights
        cursor.execute('SELECT insight_text FROM insights ORDER BY created_at DESC LIMIT 5')
        insights = [r[0] for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            "emotion_performance": self.get_emotion_performance(),
            "recent_insights": insights,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Data-backed recommendations"""
        recommendations = []
        emotion_perf = self.get_emotion_performance()
        
        if emotion_perf:
            best_emotion = max(emotion_perf.items(), key=lambda x: x[1].get('avg_engagement', 0))
            recommendations.append(f"Focus on '{best_emotion[0]}' content (Best Engagement: {best_emotion[1]['avg_engagement']:.1%})")
            
            worst_emotion = min(emotion_perf.items(), key=lambda x: x[1].get('avg_engagement', 0))
            if worst_emotion[1]['post_count'] > 3: # Only if sample size exists
                 recommendations.append(f"Improve '{worst_emotion[0]}' content or reduce frequency (Low Engagement: {worst_emotion[1]['avg_engagement']:.1%})")
        else:
             recommendations.append("Not enough data yet. Post more!")
             
        return recommendations

if __name__ == "__main__":
    mem = MemoryAgent()
    print("Memory Agent initialized and DB created.")
