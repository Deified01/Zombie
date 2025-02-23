import logging
import re
import base64
import asyncio
import uvloop
from telethon import TelegramClient, sync, events
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import PeerChannel, Document
from telethon.sessions import StringSession
from flask import Flask, jsonify
from datetime import datetime, timedelta
import threading
import os
from pymongo import MongoClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set up the Telegram client
api_id = 8447214
api_hash = '9ec5782ddd935f7e2763e5e49a590c0d'
strinng_session = "1BVtsOL8Bu8ZK0k18_pmgLgWAGbQ4o0x6bloGX785FHl2jPLiafYKd-ZIapn9IuaZmce_KLbz_bG-XBXluXzrJ8az4VCyyIIyZxcFmNUcN-o75HSbZNI4XcC8s3Ms7OVsOz7HxywptvpKGYlxRcUTuC-GYCqIBxQS5x6uA1KqMVATrBgvdM8iSH_FUbDx9sYfNNsqQcUpS5-uBu528qUf_hAXypwa9hmWJzpkZL-mRvXJL2WozrO1BCaFTppU6ltjQjshZt7kV2PGSmgBEWaFo2sP2kYCvU9ETb5Nmo-sLuAAkJ2X1UstNdtvMFFc8m9wbNjkNvG_Dq4BfkxMnID2u1vkkW9yBtk="
string_session = os.getenv("string")
client = TelegramClient(StringSession(string_session), api_id, api_hash)
# Set up MongoDB connection
mongo_client = MongoClient("mongodb+srv://xmon77:fF5ew07G0pll9YI3@cluster0.1travym.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["telegram_data"]
media_collection = db["media_data"]

async def process_messages(messages):
    for message in messages:
        if message and message.text:
            # Remove non-alphanumeric characters except spaces and colons from the message text
            cleaned_text = ''.join(char for char in message.text if char.isalnum() or char in ' :')

            # Extract the full name using regex
            name_match = re.search(r'Character Name: ([\w ]+)', cleaned_text)
            if name_match:
                full_name = name_match.group(1)

                # Exclude the "Anime Name" part from the full name
                anime_name_pattern = re.compile(r"Anime Name", re.IGNORECASE)
                character_name = anime_name_pattern.sub("", full_name)
                print(character_name.strip())

                # Check if the message has media
                if message.media:
                    # Download the media
                    media = await client.download_media(message.media)

                    # Encode the media to base64
                    with open(media, 'rb') as f:
                        media_data = f.read()
                    base64_media = base64.b64encode(media_data).decode('utf-8')

                    # Save the base64 media and character name to MongoDB
                    media_collection.insert_one({"base64_media": base64_media, "character_name": character_name.strip()})
                    logging.info(f"Saved media for {character_name.strip()} to MongoDB")
                else:
                    logging.warning(f"Message {message.id} has no media.")
        else:
            logging.warning(f"Message {message.id} has no text content.")

async def main():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    await client.start()
    async with client:
        # Fetch all the messages at once
        messages = await client.get_messages('slave_update', limit=None)

        # Process the messages
        await process_messages(messages)

        # Start the file sending task
        client.loop.create_task(send_file_to_telegram())

# Flask web server
app = Flask(__name__)

@app.route('/', methods=['GET'])
def hello_world():
    return 'Hello, world!'

def run_flask_server():
    app.run(host='0.0.0.0', port=8080, use_reloader=False)

if __name__ == '__main__':
    # Run the Flask server as a daemon
    flask_thread = threading.Thread(target=run_flask_server)
    flask_thread.daemon = True
    flask_thread.start()

    # Run the Telegram client
    client.loop.run_until_complete(main())

    # Keep the main thread running
  
