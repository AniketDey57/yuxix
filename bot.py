import os
import re
import shutil
import subprocess
from urllib.parse import urlparse
from telethon import TelegramClient, events
from mutagen import File

# Set up your MTProto API credentials (API ID and hash from Telegram's Developer Portal)
api_id = '3555648'
api_hash = 'a08b1rd3365ha3b04bcj2bcbf71afgdf4d'
session_name = 'beatport_downloader'

# Regular expressions for Beatport and Crates.co URLs
beatport_pattern = '^https:\/\/www\.beatport\.com\/track\/[\w -]+\/\d+$'
crates_pattern = '^https:\/\/crates\.co\/track\/[\w -]+\/\d+$'

# Initialize the client
client = TelegramClient(session_name, api_id, api_hash)

# Start the client and listen for new messages
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply("Hi! I'm Beatport Track Downloader using MTProto API.\n\n"
                      "Commands:\n"
                      "/download <track_url> - Download a track from Beatport or Crates.co.\n\n"
                      "Example:\n"
                      "/download https://www.beatport.com/track/take-me/17038421\n"
                      "/download https://crates.co/track/take-me/17038421")

@client.on(events.NewMessage(pattern='/download'))
async def download_handler(event):
    input_text = event.message.text.split(maxsplit=1)[1]
    
    # Validate the track URL against Beatport and Crates.co patterns
    is_beatport = re.match(rf'{beatport_pattern}', input_text)
    is_crates = re.match(rf'{crates_pattern}', input_text)

    if is_beatport or is_crates:
        # Convert Crates.co link to Beatport link if necessary
        if is_crates:
            input_text = input_text.replace('crates.co', 'www.beatport.com')

        await event.reply("Downloading and processing the audio file... Please be patient.")
        url = urlparse(input_text)
        components = url.path.split('/')

        # Run the orpheus script to download the track
        os.system(f'python orpheus.py {input_text}')

        # Get the downloaded filename
        filename = os.listdir(f'downloads/{components[-1]}')[0]
        filepath = f'downloads/{components[-1]}/{filename}'

        # Extract metadata using mutagen
        audio = File(filepath, easy=True)
        artist = audio.get('artist', ['Unknown Artist'])[0]
        title = audio.get('title', ['Unknown Title'])[0]

        # Create the new filename based on artist and title
        new_filename = f"{artist} - {title}.flac"
        new_filepath = f'downloads/{components[-1]}/{new_filename}'

        # Convert the downloaded file to FLAC format using ffmpeg
        subprocess.run(['ffmpeg', '-i', filepath, new_filepath])

        # Send the renamed FLAC file to the user
        await client.send_file(event.chat_id, new_filepath)

        # Clean up the downloaded files
        shutil.rmtree(f'downloads/{components[-1]}')
    else:
        await event.reply('Invalid track link.\nPlease enter a valid track link.')

async def main():
    # Start the Telegram client
    async with client:
        print("Client is running...")
        await client.run_until_disconnected()

if __name__ == '__main__':
    client.loop.run_until_complete(main())
