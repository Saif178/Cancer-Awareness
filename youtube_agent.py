import json
import re
from typing import List, Dict, Optional
import yt_dlp

# Importing the modern library structure
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

class CancerTranscriptAgentYTDLP:
    def __init__(self, search_query: str = "cancer treatment breakthrough clinical trials"):
        self.search_query = search_query
        
    def discover_videos(self, limit: int = 5) -> List[Dict]:
        """ Uses yt-dlp to search YouTube without layout parsing bugs. """
        print(f"🕵️ Agent: Searching YouTube via yt-dlp for '{self.search_query}'...")
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
        }
        
        video_list = []
        search_url = f"ytsearch{limit}:{self.search_query}"
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                result = ydl.extract_info(search_url, download=False)
                
                if 'entries' in result and result['entries']:
                    for video in result['entries']:
                        if not video:
                            continue
                        video_list.append({
                            'video_id': video.get('id'),
                            'title': video.get('title'),
                            'link': f"https://www.youtube.com/watch?v={video.get('id')}",
                            'duration': video.get('duration'),
                            'view_count': video.get('view_count', 'Unknown')
                        })
                
            print(f"✅ Agent: Found {len(video_list)} relevant videos.")
            return video_list
        except Exception as e:
            print(f"❌ Agent Error during video discovery: {e}")
            return []

    def extract_transcript(self, video_id: str) -> Optional[str]:
        """
        Retrieves transcripts using the modern object-attribute pattern.
        """
        try:
            # Initialize the instance and use modern fetch pattern
            transcript_obj = YouTubeTranscriptApi().fetch(video_id, languages=['en'])
            
            # FIX: transcript_obj contains FetchedTranscriptSnippet models.
            # We access text properties using dot-notation (.text) instead of brackets (['text']).
            text_fragments = []
            for segment in transcript_obj:
                text_fragments.append(segment.text)  # <--- FIXED ATTRIBUTE LOGIC
            
            # Combine individual text tracks into a unified paragraph block
            full_text = " ".join(text_fragments)
            cleaned_text = re.sub(r'\s+', ' ', full_text).strip()
            return cleaned_text
            
        except (TranscriptsDisabled, NoTranscriptFound):
            print(f"⚠️ Agent Warning: Transcripts are disabled or missing for video: {video_id}")
            return None
        except Exception as e:
            print(f"❌ Agent Error extracting transcript for {video_id}: {e}")
            return None

    def run_pipeline(self, max_videos: int = 5) -> List[Dict]:
        discovered_videos = self.discover_videos(limit=max_videos)
        processed_data = []

        for video in discovered_videos:
            if not video['video_id']:
                continue
            print(f"\n📖 Processing: '{video['title']}'")
            transcript = self.extract_transcript(video['video_id'])
            
            if transcript:
                video['transcript'] = transcript
                processed_data.append(video)
                print(f"✨ Successfully extracted {len(transcript.split())} words.")
            else:
                print("⏭️ Skipping video due to missing transcript.")

        return processed_data

# ==========================================
# Execution Block
# ==========================================
if __name__ == "__main__":
    agent = CancerTranscriptAgentYTDLP(search_query="detecting early stage cancer")
    extracted_datasets = agent.run_pipeline(max_videos=100)
    
    output_filename = "cancer_treatment_transcripts.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(extracted_datasets, f, indent=4, ensure_ascii=False)
        
    print(f"\n💾 Pipeline Finished! Dataset saved to '{output_filename}'")
