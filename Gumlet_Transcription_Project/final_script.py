import requests
import os
import re

# --- Configuration ---
# Replace with the new key
API_KEY = "xxxxx"
COLLECTION_ID = "xxxxx"
TARGET_TAG = "webinar"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json"
}

def clean_vtt_to_text(vtt_content):
    """Removes timestamps, metadata and HTML tags from VTT files."""
    lines = vtt_content.splitlines()
    clean_lines = []
    for line in lines:
        if line.strip() and "-->" not in line and "WEBVTT" not in line:
            clean_line = re.sub(r'<[^>]+>', '', line)
            clean_lines.append(clean_line.strip())
    # dict.fromkeys removes duplicates while preserving order
    return "\n".join(dict.fromkeys(clean_lines))

def process_all_assets():
    """Main function to fetch, filter, and save transcriptions."""
    if not os.path.exists("transcriptions"):
        os.makedirs("transcriptions")

    page = 1
    has_more = True
    found_count = 0

    print(f"🚀 Starting extraction for tag: {TARGET_TAG}")

    while has_more:
        url = f"https://api.gumlet.com/v1/video/assets/list/{COLLECTION_ID}"
        params = {
            "page": page,
            "per_page": 50  # Fetching maximum allowed assets per page
        }
        
        print(f"🔍 Checking page {page}...")
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            assets = data.get('all_assets', [])
            
            if not assets:
                has_more = False
                break

            for asset in assets:
                tags = asset.get('tag', [])
                if TARGET_TAG in tags:
                    found_count += 1
                    asset_id = asset.get('asset_id')
                    title = asset.get('input', {}).get('title', asset_id)
                    
                    # Clean filename and add Asset ID prefix
                    safe_title = re.sub(r'[\\/*?:"<>|]', "", title).replace(" ", "_")
                    filename = f"{asset_id}_{safe_title}.txt"
                    
                    subtitles = asset.get('output', {}).get('storage_details', {}).get('subtitle', [])
                    
                    if subtitles:
                        vtt_filename = subtitles[0].get('fileName')
                        # Constructing the direct VTT download URL
                        vtt_url = f"https://video.gumlet.io/{COLLECTION_ID}/{asset_id}/{vtt_filename}"
                        
                        print(f"📥 Downloading: {filename}")
                        vtt_res = requests.get(vtt_url)
                        if vtt_res.status_code == 200:
                            clean_text = clean_vtt_to_text(vtt_res.text)
                            with open(f"transcriptions/{filename}", "w", encoding="utf-8") as f:
                                f.write(clean_text)
                        else:
                            print(f"❌ Failed to download VTT for: {title}")
                    else:
                        print(f"⚠️ No subtitle found for: {title}")
            
            page += 1 # Move to the next page
        else:
            print(f"❌ API Error {response.status_code}. Please check your API Key.")
            has_more = False

    print(f"✅ Process Complete. Total files saved: {found_count}")

if __name__ == "__main__":
    process_all_assets()