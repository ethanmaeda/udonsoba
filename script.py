import re
import googleapiclient.discovery
import csv
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

CHANNELS = {
    'OSAKA_NARA': 'UCsyzqlcYZJUdAV2D9DXjp6g',
    'KYOTO_HYOGO': 'UCm9X4pcqEdPlW7lIYzWGEQA',
    'TOKYO': 'UCIKvmvEvZdi96rtPqRu9ahQ',
    'HIROSHIMA_OKAYAMA': 'UCLR62h0m5rvt6qaeScNmBoA',
    'FUKUOKA': 'UC7ljLL8UKkeVYWsYYZZZrxQ',
    'HOKURIKU': 'UCaT7UdqAk5KpgWgvAM9tjXg',
    'NAGOYA_TOKAI': 'UCnYWfTfQnULKX3hsjJcJtXg',
    'KAGAWA_SHIKOKU': 'UCJgBEZGNmEf_WbOn-YPeoeg',
    'HOKKAIDO': 'UCzEg7YyDQ3BSuCmL6xaE9yQ'
}

def extract_address_from_description(description):
    match = re.search(r'([一-龯]{2,}(都|道|府|県)[^\n\r]{5,40})', description)
    if match:
        return match.group(1).strip()
    return None

def get_all_video_ids(youtube, uploads_playlist_id):
    video_ids = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response['items']:
            video_ids.append(item['contentDetails']['videoId'])

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

def get_video_descriptions(youtube, video_ids):
    descriptions = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        request = youtube.videos().list(
            part="snippet",
            id=",".join(batch)
        )
        response = request.execute()

        for item in response['items']:
            desc = item['snippet']['description']
            descriptions.append(desc)

    return descriptions

def uploads_to_csv(location, channel_id):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)
    
    # Get uploads playlist
    channel_request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    channel_response = channel_request.execute()
    uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Get all video IDs
    video_ids = get_all_video_ids(youtube, uploads_playlist_id)

    # Get video metadata
    entries = []
    desc_without_address = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        request = youtube.videos().list(
            part="snippet",
            id=",".join(batch)
        )
        response = request.execute()

        for item in response['items']:
            desc = item['snippet']['description']
            title = item['snippet']['title']
            video_id = item['id']
            link = f"https://www.youtube.com/watch?v={video_id}"
            address = extract_address_from_description(desc)

            if address:
                entries.append({
                    'Name': title,
                    'Address': address,
                    'YouTube Link': link
                })
            else:
                desc_without_address.append(desc)

    # Write CSV
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)
    
    output_path = os.path.join(output_folder, location + ".csv")
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["Name", "Address", "YouTube Link"])
        writer.writeheader()
        for entry in entries:
            writer.writerow(entry)

    print(f"✅ Wrote {len(entries)} entries to", output_path, "\n")

    # Log descriptions with no address
    if desc_without_address:
        with open("no_address.log", "w", encoding="utf-8") as log_file:
            log_file.write("Descriptions with no addresses:\n")
            for desc in desc_without_address:
                log_file.write("\n" + "-"*50 + "\n")
                log_file.write(desc + "\n")
                log_file.write("-"*50 + "\n")

def main():
    for location, channel_id in CHANNELS.items():
        print(f"Processing channel: {location}")
        uploads_to_csv(location, channel_id)

if __name__ == "__main__":
    main()
