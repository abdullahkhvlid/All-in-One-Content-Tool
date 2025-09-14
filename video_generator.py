import os
import requests
import time
import json
from typing import Optional, Dict, Any
from datetime import datetime

class StabilityVideoGenerator:
    """
    Stability AI Video Generation API Integration (Stable Video Diffusion)
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stability.ai/v2beta/video/generate"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self.output_dir = os.path.join(os.path.dirname(__file__), "..", "media", "outputs")
        os.makedirs(os.path.abspath(self.output_dir), exist_ok=True)

    def generate_video(self, prompt: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Generate video using Stability AI API
        
        Args:
            prompt (str): Text prompt for video generation
            **kwargs: Additional parameters like duration, output_format, etc.
        
        Returns:
            Dict with video generation result or None if failed
        """
        try:
            payload = {
                "prompt": prompt,
                "output_format": kwargs.get("output_format", "mp4"),
                "seed": kwargs.get("seed", None),
                "cfg_scale": kwargs.get("cfg_scale", 2),
                "motion_bucket_id": kwargs.get("motion_bucket_id", 127),
                "steps": kwargs.get("steps", 25),
                "cond_aug": kwargs.get("cond_aug", 0.02),
                "fps": kwargs.get("fps", 7),
                "width": kwargs.get("width", 576),
                "height": kwargs.get("height", 1024),
            }
            # Remove None values
            payload = {k: v for k, v in payload.items() if v is not None}

            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60
            )
            if response.status_code in [200, 201]:
                result = response.json()
                video_url = result.get("video_url")
                if video_url:
                    video_path = self._download_video(video_url, prompt)
                    return {
                        "success": True,
                        "video_url": video_url,
                        "local_path": video_path,
                        "prompt": prompt,
                        "parameters": payload,
                        "generated_at": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"No video URL in API response: {result}",
                        "prompt": prompt
                    }
            else:
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code} - {response.text}",
                    "prompt": prompt
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Network Error: {str(e)}",
                "prompt": prompt
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected Error: {str(e)}",
                "prompt": prompt
            }

    def _download_video(self, video_url: str, prompt: str) -> Optional[str]:
        """
        Download video from URL to local storage
        """
        try:
            safe_filename = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_filename = safe_filename[:50]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stability_video_{safe_filename}_{timestamp}.mp4"
            filepath = os.path.join(self.output_dir, filename)

            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        except Exception as e:
            return None

    def list_available_qualities(self):
        return ["default"]

    def list_available_styles(self):
        return ["default"]

if __name__ == "__main__":
    # Test Stability
    stability_key = "sk-4GJySKv1qQhHQIHNltnVaXVVrLmiopdTVpglP9lfBI1QBI6Y"
    svd = StabilityVideoGenerator(stability_key)
    test_prompt = "A beautiful sunset over the ocean with gentle waves"
    result = svd.generate_video(test_prompt)
    if result and result["success"]:
        print(f"✅ Stability Video generated: {result['local_path']}")
    else:
        print(f"❌ Stability Video generation failed: {result.get('error', 'Unknown error')}")