from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from openai import OpenAI
import openai
import base64
from email.mime.text import MIMEText
from typing import List, Dict, Optional
import json
from src.configDict import Setting

settings = Setting()


class GmailAIHelper:
    def __init__(self, oauth_token: str, openai_key: str):
        self.credentials = Credentials(
            token=oauth_token,
            scopes=['https://www.googleapis.com/auth/gmail.modify']
        )
        self.service = build('gmail', 'v1', credentials=self.credentials)
        # self.ai_client = OpenAI(api_key=openai_key)
        # Initialize the ASYNCHRONOUS client
        self.ai_client = openai.AsyncOpenAI(api_key=openai_key)

    async def get_unread_messages(self, max_results: int = 10) -> List[Dict]:
        """Fetch unread messages from Gmail"""
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['UNREAD', 'INBOX'],
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            email_list = []

            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()

                email_data = self._parse_email_message(msg)
                email_list.append(email_data)

            return email_list
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def _parse_email_message(self, message: Dict) -> Dict:
        """Parse Gmail message into structured format"""
        headers = message['payload']['headers']
        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'from': next(h['value'] for h in headers if h['name'].lower() == 'from'),
            'subject': next(h['value'] for h in headers if h['name'].lower() == 'subject'),
            'body': self._get_email_body(message['payload']),
            'date': next(h['value'] for h in headers if h['name'].lower() == 'date')
        }

    def _get_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    return base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8')
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8')
        return ""

    async def generate_ai_response(self, email_content: Dict) -> str:
        """Generate AI response using OpenAI"""
        try:
            prompt = f"""
            Generate a professional email response based on this context:
            Subject: {email_content['subject']}
            Original Email: {email_content['body']}
            
            Requirements:
            - Maintain professional tone
            - Address key points from original email
            - Keep response concise
            - Add appropriate greeting and signature
            """

            response = await self.ai_client.chat.completions.create(
                model= settings.OPENAI_API_MODEL,
                messages=[
                    {"role": "system", "content": "You are a professional email assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating AI response: {e}")
            return ""

    async def send_ai_reply(self, email: Dict, ai_response: str) -> bool:
        """Send AI-generated response"""
        try:
            message = MIMEText(ai_response)
            message['to'] = email['from']
            message['subject'] = f"Re: {email['subject']}"
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')

            self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message, 'threadId': email['thread_id']}
            ).execute()

            return True
        except Exception as e:
            print(f"Error sending reply: {e}")
            return False

