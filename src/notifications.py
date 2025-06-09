"""Notification system for alerts and updates."""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

from src.config import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class NotificationChannel:
    """Base class for notification channels."""
    
    async def send(self, subject: str, message: str, data: Dict[str, Any]) -> bool:
        """Send notification through this channel."""
        raise NotImplementedError


class EmailChannel(NotificationChannel):
    """Email notification channel."""
    
    def __init__(self):
        """Initialize email channel."""
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.use_tls = settings.smtp_tls
    
    async def send(self, subject: str, message: str, data: Dict[str, Any]) -> bool:
        """Send email notification."""
        if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
            logger.warning("Email configuration incomplete, skipping notification")
            return False
        
        try:
            # Get recipients from data
            recipients = data.get("recipients", [])
            if not recipients:
                logger.warning("No email recipients specified")
                return False
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Lapis Spider] {subject}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(recipients)
            
            # Create HTML content
            html_content = self._format_html_message(subject, message, data)
            
            # Attach parts
            msg.attach(MIMEText(message, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def _format_html_message(self, subject: str, message: str, data: Dict[str, Any]) -> str:
        """Format HTML email message."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #f4f4f4; padding: 20px; }}
                .content {{ padding: 20px; }}
                .data {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; }}
                .footer {{ background-color: #f4f4f4; padding: 10px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>{subject}</h2>
            </div>
            <div class="content">
                <p>{message}</p>
                {self._format_data_section(data)}
            </div>
            <div class="footer">
                <p>Sent by Lapis Spider at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>
        </body>
        </html>
        """
        return html
    
    def _format_data_section(self, data: Dict[str, Any]) -> str:
        """Format data section for email."""
        if "details" not in data:
            return ""
        
        html = "<div class='data'><h3>Details:</h3><ul>"
        for key, value in data["details"].items():
            html += f"<li><strong>{key}:</strong> {value}</li>"
        html += "</ul></div>"
        
        return html


class SlackChannel(NotificationChannel):
    """Slack notification channel."""
    
    def __init__(self):
        """Initialize Slack channel."""
        self.webhook_url = settings.slack_webhook_url
    
    async def send(self, subject: str, message: str, data: Dict[str, Any]) -> bool:
        """Send Slack notification."""
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured, skipping notification")
            return False
        
        try:
            # Format Slack message
            slack_message = {
                "text": subject,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": subject
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
            
            # Add data fields
            if "details" in data:
                fields = []
                for key, value in data["details"].items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    })
                
                if fields:
                    slack_message["blocks"].append({
                        "type": "section",
                        "fields": fields[:10]  # Limit to 10 fields
                    })
            
            # Send to Slack
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=slack_message,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("Slack notification sent successfully")
                    return True
                else:
                    logger.error(f"Slack API error: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False


class InAppChannel(NotificationChannel):
    """In-app notification channel (stored in database)."""
    
    async def send(self, subject: str, message: str, data: Dict[str, Any]) -> bool:
        """Store notification in database."""
        try:
            from src.database.postgres import get_db_context
            
            user_id = data.get("user_id")
            if not user_id:
                logger.warning("No user_id specified for in-app notification")
                return False
            
            with get_db_context() as db:
                db.execute(
                    """
                    INSERT INTO notifications (user_id, type, title, message, data)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (user_id, "in_app", subject, message, json.dumps(data))
                )
                db.commit()
            
            logger.info(f"In-app notification stored for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in-app notification: {e}")
            return False


class NotificationManager:
    """Manage notification sending across channels."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.channels = {
            "email": EmailChannel(),
            "slack": SlackChannel(),
            "in_app": InAppChannel()
        }
        
        # Notification templates
        self.templates = {
            "website_changes": {
                "subject": "Website Changes Detected",
                "message": "Changes have been detected on {website_id}. {changes_count} pages have been modified.",
                "channels": ["email", "slack", "in_app"]
            },
            "crawl_completed": {
                "subject": "Crawl Job Completed",
                "message": "Crawl job {job_id} completed successfully. {pages_crawled} pages processed.",
                "channels": ["in_app"]
            },
            "crawl_failed": {
                "subject": "Crawl Job Failed",
                "message": "Crawl job {job_id} failed with error: {error}",
                "channels": ["email", "in_app"]
            },
            "daily_report": {
                "subject": "Daily Activity Report",
                "message": "Daily report for {date}: {crawl_statistics[total_crawls]} crawls, {active_users} active users",
                "channels": ["email", "slack"]
            },
            "system_unhealthy": {
                "subject": "System Health Alert",
                "message": "System health check failed. One or more services are unhealthy.",
                "channels": ["email", "slack"]
            },
            "storage_warning": {
                "subject": "Storage Warning",
                "message": "Storage usage is above {threshold}%. Current usage: {usage}%",
                "channels": ["email", "slack"]
            }
        }
    
    async def send(self, notification_type: str, data: Dict[str, Any], 
                   channels: Optional[List[str]] = None) -> Dict[str, bool]:
        """Send notification through specified channels."""
        template = self.templates.get(notification_type)
        if not template:
            logger.error(f"Unknown notification type: {notification_type}")
            return {}
        
        # Format subject and message
        subject = template["subject"]
        message = template["message"]
        
        # Simple template variable replacement
        for key, value in data.items():
            if isinstance(value, dict):
                # Handle nested dictionaries
                for nested_key, nested_value in value.items():
                    placeholder = f"{{{key}[{nested_key}]}}"
                    message = message.replace(placeholder, str(nested_value))
            else:
                placeholder = f"{{{key}}}"
                message = message.replace(placeholder, str(value))
        
        # Determine channels to use
        channels_to_use = channels or template["channels"]
        
        # Send through each channel
        results = {}
        for channel_name in channels_to_use:
            if channel_name in self.channels:
                try:
                    success = await self.channels[channel_name].send(
                        subject, message, data
                    )
                    results[channel_name] = success
                except Exception as e:
                    logger.error(f"Error sending {channel_name} notification: {e}")
                    results[channel_name] = False
            else:
                logger.warning(f"Unknown channel: {channel_name}")
                results[channel_name] = False
        
        return results
    
    async def send_custom(self, subject: str, message: str, 
                         data: Dict[str, Any], channels: List[str]) -> Dict[str, bool]:
        """Send custom notification."""
        results = {}
        
        for channel_name in channels:
            if channel_name in self.channels:
                try:
                    success = await self.channels[channel_name].send(
                        subject, message, data
                    )
                    results[channel_name] = success
                except Exception as e:
                    logger.error(f"Error sending {channel_name} notification: {e}")
                    results[channel_name] = False
            else:
                logger.warning(f"Unknown channel: {channel_name}")
                results[channel_name] = False
        
        return results


# Singleton instance
notification_manager = NotificationManager()


# Convenience functions
async def send_notification(notification_type: str, data: Dict[str, Any], 
                          channels: Optional[List[str]] = None) -> Dict[str, bool]:
    """Send notification through notification manager."""
    return await notification_manager.send(notification_type, data, channels)


async def send_custom_notification(subject: str, message: str,
                                 data: Dict[str, Any], channels: List[str]) -> Dict[str, bool]:
    """Send custom notification."""
    return await notification_manager.send_custom(subject, message, data, channels)