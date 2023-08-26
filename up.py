from telethon import TelegramClient, events
import os
import subprocess
import mimetypes
import zipfile
import shutil
import requests

# Replace these values with your actual credentials
api_id = 21856699
api_hash = '73f10cf0979637857170f03d4c86f251'
bot_token = '6400640505:AAEkS-gVOM_-W1eL_qRtjS3X9ARjBu14S18'

# Initialize the Telegram client
client = TelegramClient('session_name', api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage)
async def handle_message(event):
    if event.message.file or event.message.text.startswith('http'):
        await event.respond("Downloading and processing the files...")

        # Delete existing user directory if present
        user_id = event.message.sender_id
        user_dir = str(user_id)
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)

        # Download the file using wget, curl, or requests
        if event.message.file:
            downloaded_file = await event.message.download_media()
        else:
            download_methods = [
                lambda url, path: subprocess.run(["wget", url, "-O", path]),
                lambda url, path: subprocess.run(["curl", url, "-o", path]),
                lambda url, path: requests.get(url, stream=True).raw,
            ]

            for download_method in download_methods:
                try:
                    response = download_method(event.message.text, 'downloaded_file.zip')
                    if isinstance(response, subprocess.CompletedProcess):
                        if response.returncode == 0:
                            downloaded_file = 'downloaded_file.zip'
                            break
                    elif hasattr(response, 'read'):
                        with open('downloaded_file.zip', 'wb') as f:
                            shutil.copyfileobj(response, f)
                        downloaded_file = 'downloaded_file.zip'
                        break
                except Exception:
                    pass

        # Create a new directory for the user
        os.makedirs(user_dir)

        # Unzip the file
        with zipfile.ZipFile(downloaded_file, 'r') as zip_ref:
            zip_ref.extractall(user_dir)

        # Delete the downloaded zip file
        os.remove(downloaded_file)

        # List all files in the user directory, including subdirectories
        all_files = []
        for root, _, files in os.walk(user_dir):
            for file in files:
                all_files.append(os.path.join(root, file))

        # Prepare a response message with numbered options
        options = "\n".join([f"{i + 1}. {os.path.relpath(file, user_dir)}" for i, file in enumerate(all_files)])
        response_message = f"Select files to send back (separate indices with '&'):\n{options}\nOr type 'all' to send all files."
        await event.respond(response_message)

        async def send_files(selected_indices):
            selected_indices = [int(idx) - 1 for idx in selected_indices]
            selected_files = [all_files[i] for i in selected_indices if 0 <= i < len(all_files)]
            if selected_files:
                await event.respond("Sending the selected files...")
                for file_path in selected_files:
                    mime_type, _ = mimetypes.guess_type(file_path)
                    await client.send_file(event.message.sender_id, file_path, caption=os.path.basename(file_path), force_document=True, mime_type=mime_type)

        @client.on(events.NewMessage)
        async def inner_handle_message(event):
            message = event.message.text
            if message.lower() == 'all':
                await event.respond("Sending all files...")
                for file_path in all_files:
                    mime_type, _ = mimetypes.guess_type(file_path)
                    await client.send_file(event.message.sender_id, file_path, caption=os.path.basename(file_path), force_document=True, mime_type=mime_type)
            elif '&' in message:
                selected_indices = message.split('&')
                await send_files(selected_indices)

client.run_until_disconnected()
