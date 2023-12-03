from twilio.rest import Client
from flask import Flask, Response, request, jsonify
# Secrets
from dotenv import load_dotenv
load_dotenv()
import os

app = Flask(__name__)

# Twilio credentials
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone_number="12402920128"

@app.route('/', methods=['POST'])
def webhook():
    data = request.json

    # Parse the form_response
    form_response = data['form_response']

    # Initialize variables for full name and phone number
    full_name = ''
    phone_number = ''

    # Iterate through answers and extract data
    for answer in form_response['answers']:
        if answer['type'] == 'text':
            full_name = answer['text']
        elif answer['type'] == 'phone_number':
            phone_number = answer['phone_number']

    # Debugging: print the extracted information
    print("Full Name:", full_name)
    print("Phone Number:", phone_number)

    # Initialize Twilio client
    client = Client(account_sid, auth_token)

    # Make a call
    call = client.calls.create(
        to=phone_number,
        from_=twilio_phone_number,
        url="https://6478-68-146-172-230.ngrok.io/start_call"
    )

    print(call.sid)

    return jsonify({'message': 'Received'}), 200

@app.route("/start_call", methods=['GET', 'POST'])
def start_call():
    response = '''<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Gather input="speech" action="/handle_response" method="POST">
            <Say voice="alice">Hi, how are you doing today?</Say>
        </Gather>
    </Response>'''
    return Response(response, mimetype='text/xml')

@app.route("/handle_response", methods=['POST'])
def handle_response():
    # This is where you'll handle the response from the user
    # For now, we'll just print the SpeechResult
    speech_result = request.form.get('SpeechResult')
    print("The user said:", speech_result)
    return Response('<Response><Say>Thank you for your response.</Say></Response>', mimetype='text/xml')


if __name__ == "__main__":
    app.run(port=3000)
