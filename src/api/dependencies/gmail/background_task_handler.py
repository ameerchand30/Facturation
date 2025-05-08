from fastapi import BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
import asyncio
import logging
from src.configDict import Setting
from src.api.dependencies.gmail.gmail_service_helper import GmailAIHelper
from src.api.models.gmail.email_log_model import EmailLog
settings = Setting()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GmailListener:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.active_listeners: Dict[str, bool] = {}
        self.last_check_time: Dict[str, datetime] = {}
        self.processing_lock = asyncio.Lock()

    async def start_listening(self, user_email: str, oauth_token: str, openai_key: str, db: Session):
        """Start listening for new emails for a specific user"""
        if user_email in self.active_listeners:
            logger.info(f"Listener already active for {user_email}")
            return

        self.active_listeners[user_email] = True
        self.last_check_time[user_email] = datetime.utcnow()

        # Add job to scheduler
        self.scheduler.add_job(
            self._check_new_emails,
            trigger=IntervalTrigger(minutes=1),
            args=[user_email, oauth_token, openai_key, db],
            id=f"gmail_listener_{user_email}",
            replace_existing=True
        )

        if not self.scheduler.running:
            self.scheduler.start()

        logger.info(f"Started Gmail listener for {user_email}")

    async def stop_listening(self, user_email: str):
        """Stop listening for a specific user"""
        if user_email in self.active_listeners:
            self.active_listeners[user_email] = False
            self.scheduler.remove_job(f"gmail_listener_{user_email}")
            logger.info(f"Stopped Gmail listener for {user_email}")

    async def _check_new_emails(self, user_email: str, oauth_token: str, openai_key: str, db: Session):
        """Check for new emails and process them"""
        async with self.processing_lock:
            try:
                if not self.active_listeners.get(user_email):
                    return

                gmail_helper = GmailAIHelper(oauth_token, openai_key)
                last_check = self.last_check_time[user_email]

                # Get new unread emails
                new_emails = await gmail_helper.get_unread_messages_since(last_check)
                
                for email in new_emails:
                    # Generate and send AI response
                    ai_response = await gmail_helper.generate_ai_response(email)
                    if ai_response:
                        success = await gmail_helper.send_ai_reply(email, ai_response)
                        
                        # Log the interaction
                        log_entry = EmailLog(
                            user_email=user_email,
                            thread_id=email['thread_id'],
                            subject=email['subject'],
                            sender=email['from'],
                            ai_response=ai_response,
                            success=success,
                            processed_at=datetime.utcnow()
                        )
                        db.add(log_entry)
                        
                        # Add custom labels/categories
                        if success:
                            await gmail_helper.categorize_email(email)

                db.commit()
                self.last_check_time[user_email] = datetime.utcnow()

            except Exception as e:
                logger.error(f"Error processing emails for {user_email}: {str(e)}")
                db.rollback()

    async def get_unread_messages_since(self, since_time: datetime) -> List[Dict]:
        """Fetch unread messages since a specific time"""
        query = f"after:{int(since_time.timestamp())} is:unread"
    
        try:
            results = self.service.users().messages().list(
            userId='me',
            q=query
            ).execute()

            messages = results.get('messages', [])
            return [self._get_full_message(msg['id']) for msg in messages]
        except Exception as e:
            logger.error(f"Error fetching recent messages: {e}")
        return []

    async def categorize_email(self, email: Dict):
        """Categorize email based on content analysis"""
        try:
        # Use OpenAI to analyze email content
            analysis = await self.ai_client.chat.completions.create(
                model= settings.OPENAI_API_MODEL,
                messages=[
                    {"role": "system", "content": "Analyze this email and categorize it."},
                    {"role": "user", "content": email['body']}
                ]
            )
            category = analysis.choices[0].message.content.lower()
        
            # Create or get label
            label_name = f"AI_Category_{category}"
            try:
                label = self.service.users().labels().create(
                    userId='me',
                    body={'name': label_name}
                ).execute()
            except:
                # Label might already exist
                labels = self.service.users().labels().list(userId='me').execute()
                label = next((l for l in labels['labels'] if l['name'] == label_name), None)
            
            if label:
                # Apply label to email
                self.service.users().messages().modify(
                    userId='me',
                    id=email['id'],
                    body={'addLabelIds': [label['id']]}
                ).execute()
            
        except Exception as e:
            logger.error(f"Error categorizing email: {e}")