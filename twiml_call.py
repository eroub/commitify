from openai import OpenAI
import requests
from flask import Flask, Response, request
import threading
import time
from twilio.rest import Client
# Secrets
from dotenv import load_dotenv
load_dotenv()
import os

app = Flask(__name__)

# Credentials
openai_api_key = os.getenv('OPENAI_API_KEY')
vocode_api_key = os.getenv('VOCODE_API_KEY')
twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
# Setup
client = Client(twilio_account_sid, twilio_auth_token)
twilio_phone_number = "+17072205808"
openai_client = OpenAI(api_key=openai_api_key)
# OpenAI
assistant = openai_client.beta.assistants.create(
    name="My AI Assistant",
    instructions="You are a helpful assistant. Make conversation with the user. Be as natural as possible.",
    model="gpt-4-1106-preview"  # You can specify other models
)
thread = openai_client.beta.threads.create()

def initiate_call(user_first_name):
    time.sleep(5)
    phone_number = "+14039932200"
    print(f"Initiating call to {user_first_name}")
    call = client.calls.create(
        to=phone_number,
        from_=twilio_phone_number,
        url=f"https://5f77-2001-56a-74b3-8400-1528-8ac3-b441-ab28.ngrok.io/start_call?user_first_name={user_first_name}"
    )
    print(f"Call initiated, SID: {call.sid}")

@app.route("/start_call", methods=['GET', 'POST'])
def start_call():
    user_first_name = request.args.get('user_first_name', 'there')
    ai_speech = f"Hi {user_first_name}, how are you doing today?"
    print(f"AI says: {ai_speech}")
    response = f'''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather input="speech" action="/handle_response" method="POST" transcribe="true" transcribeCallback="/transcription">
            <Say voice="Google.en-US-Wavenet-G">{ai_speech}</Say>
        </Gather>
    </Response>'''
    return Response(response, mimetype='text/xml')

def text_to_speech(text):
    """Converts text to speech using Vocode's API."""
    headers = {
        'Authorization': f'Bearer {vocode_api_key}'
    }
    data = {
        'text': text,
        # Add additional parameters as needed for voice customization
    }
    response = requests.post('https://api.vocode.io/api/v1/text-to-speech', headers=headers, json=data)
    if response.status_code == 200:
        return response.json()['audio_file_url']  # URL of the generated audio file
    else:
        print(f"Error with Vocode API: {response.text}")
        return None

@app.route("/handle_response", methods=['POST'])
def handle_response():
    user_speech = request.form.get('SpeechResult')
    print(f"User said: {user_speech}")

    try:
        # Send the user's message to the Assistant
        openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_speech
        )

        # Run the Assistant
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        # Check the Run status periodically
        run_status = run.status
        while run_status == 'queued' or run_status == 'in_progress':
            time.sleep(1)  # Wait for a second before checking again
            run = openai_client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(run)
            run_status = run.status

        print(run_status)

        if run_status == 'completed':
            # Retrieve the response from the Assistant
            messages = openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )['data']
            ai_reply = next((msg['content']['text']['value'] for msg in messages if msg['role'] == 'assistant'), "I'm not sure how to respond.")
        else:
            ai_reply = "The assistant was unable to complete the response."

        print(f"AI reply: {ai_reply}")

    except Exception as e:
        print(f"Error generating AI response: {e}")
        ai_reply = "I'm having trouble understanding right now."

    return Response(f'<Response><Say>{ai_reply}</Say></Response>', mimetype='text/xml')

@app.route("/transcription", methods=['POST'])
def transcription():
    transcription_text = request.form.get('TranscriptionText')
    print(f"Transcription: {transcription_text}")
    return Response('', mimetype='text/xml')

if __name__ == "__main__":
    user_first_name = "Evan"
    threading.Thread(target=initiate_call, args=(user_first_name,)).start()
    app.run(port=3000)
