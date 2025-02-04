from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import groq
import os
import base64
import time
from email.mime.text import MIMEText

GROQ_API_KEY="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"
SCOPES=['https://www.googleapis.com/auth/gmail.compose']


def authenticate_gmail():
    creds = None
    # Check if token.json exists
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        # If no valid creds, initiate new authentication
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # If no creds, create a new one using the OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)  # This will open a browser for you to log in
        # Save credentials to token.json for next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Return the Gmail service object
    return build('gmail', 'v1', credentials=creds)

import requests

def generate_email_content(user_input, recipient):
    """Generate email content using Groq API."""
    prompt = f"Write a professional email to {recipient} about: {user_input}"
    
    # Initialize Groq client
    client = groq.Groq(api_key=GROQ_API_KEY)
    
    retries = 3
    for attempt in range(retries):
        try:
            # Use the Groq client to generate completion
            completion = client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model="mixtral-8x7b-32768",
                temperature=0.7,
                max_tokens=200
            )
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                print("Retrying...")
                time.sleep(2)
            else:
                raise Exception("Max retries exceeded")




def create_message(sender, to, subject, message_text):
    """Create a MIME message for the email."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message, 'to': to, 'subject': subject, 'message': message_text}

def send_email(service, user_id, message):
    """Send the email using the system's default email client."""
    try:
        import webbrowser
        from urllib.parse import quote
        
        # Extract email components
        to_email = message['to']
        subject = message['subject']
        body = message['message']
        
        # Create mailto URL
        mailto_url = f"mailto:{to_email}?subject={quote(subject)}&body={quote(body)}"
        
        # Open default email client
        webbrowser.open(mailto_url, new=1)
        
        print("Email draft opened in default email client")
        
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    # Get user input
    user_input = input("Enter the purpose of the email: ")
    recipient = input("Enter the recipient's email address: ")

    # Generate email content
    email_content = generate_email_content(user_input, recipient)
    print("\nGenerated Email Content:\n", email_content)

    # Authenticate Gmail
    service = authenticate_gmail()

    # Create and send the email
    sender = "me"  # 'me' refers to the authenticated user's email
    subject = "Automated Email"
    message = create_message(sender, recipient, subject, email_content)
    send_email(service, "me", message)

if __name__ == "__main__":
    main()
