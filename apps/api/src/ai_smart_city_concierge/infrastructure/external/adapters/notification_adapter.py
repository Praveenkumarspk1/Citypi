"""
Notification Service Adapters
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ....application.ports.external_services import NotificationServicePort


@dataclass
class PushNotificationResult:
    """Push notification result"""
    success: bool
    message_id: str | None
    error: str | None


@dataclass
class EmailResult:
    """Email result"""
    success: bool
    message_id: str | None
    error: str | None


@dataclass
class SMSResult:
    """SMS result"""
    success: bool
    message_id: str | None
    error: str | None


class BaseNotificationAdapter(NotificationServicePort, ABC):
    """Base notification adapter"""

    @abstractmethod
    async def _send_push_request(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict[str, Any] | None,
    ) -> PushNotificationResult:
        """Send push notification request"""
        pass

    @abstractmethod
    async def _send_email_request(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None,
    ) -> EmailResult:
        """Send email request"""
        pass

    @abstractmethod
    async def _send_sms_request(
        self,
        to: str,
        body: str,
    ) -> SMSResult:
        """Send SMS request"""
        pass

    @abstractmethod
    async def _send_in_app_request(
        self,
        user_id: UUID,
        notification: dict[str, Any],
    ) -> bool:
        """Send in-app notification request"""
        pass

    async def send_push(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Send push notification"""
        result = await self._send_push_request(user_id, title, body, data)
        return result.success

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> bool:
        """Send email"""
        result = await self._send_email_request(to, subject, body, html_body)
        return result.success

    async def send_sms(
        self,
        to: str,
        body: str,
    ) -> bool:
        """Send SMS"""
        result = await self._send_sms_request(to, body)
        return result.success

    async def send_in_app(
        self,
        user_id: UUID,
        notification: dict[str, Any],
    ) -> bool:
        """Send in-app notification"""
        return await self._send_in_app_request(user_id, notification)


class FCMNotificationAdapter(BaseNotificationAdapter):
    """Firebase Cloud Messaging adapter"""

    def __init__(self, credentials_path: str, project_id: str):
        self.credentials_path = credentials_path
        self.project_id = project_id
        self._app = None

    async def _get_app(self):
        if self._app is None:
            import firebase_admin
            from firebase_admin import credentials

            cred = credentials.Certificate(self.credentials_path)
            self._app = firebase_admin.initialize_app(cred, {
                'projectId': self.project_id,
            })
        return self._app

    async def _send_push_request(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict[str, Any] | None,
    ) -> PushNotificationResult:
        # In practice, you'd need to get the user's FCM token from your database
        # This is a simplified implementation
        try:
            from firebase_admin import messaging

            # Get user's FCM token (would come from your user repository)
            fcm_token = await self._get_user_fcm_token(user_id)
            if not fcm_token:
                return PushNotificationResult(
                    success=False,
                    message_id=None,
                    error="User has no FCM token",
                )

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
                token=fcm_token,
            )

            response = messaging.send(message)

            return PushNotificationResult(
                success=True,
                message_id=response,
                error=None,
            )
        except Exception as e:
            return PushNotificationResult(
                success=False,
                message_id=None,
                error=str(e),
            )

    async def _get_user_fcm_token(self, user_id: UUID) -> str | None:
        # This would query your database for the user's FCM token
        # Simplified implementation
        return None

    async def _send_email_request(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None,
    ) -> EmailResult:
        # FCM doesn't handle email
        return EmailResult(success=False, message_id=None, error="Not supported")

    async def _send_sms_request(
        self,
        to: str,
        body: str,
    ) -> SMSResult:
        # FCM doesn't handle SMS
        return SMSResult(success=False, message_id=None, error="Not supported")

    async def _send_in_app_request(
        self,
        user_id: UUID,
        notification: dict[str, Any],
    ) -> bool:
        # Could store in database for in-app display
        return True


class APNSNotificationAdapter(BaseNotificationAdapter):
    """Apple Push Notification Service adapter"""

    def __init__(
        self,
        key_id: str,
        team_id: str,
        bundle_id: str,
        auth_key_path: str,
        use_sandbox: bool = False,
    ):
        self.key_id = key_id
        self.team_id = team_id
        self.bundle_id = bundle_id
        self.auth_key_path = auth_key_path
        self.use_sandbox = use_sandbox
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from aioapns import APNs
            self._client = APNs(
                key=self.auth_key_path,
                key_id=self.key_id,
                team_id=self.team_id,
                topic=self.bundle_id,
                use_sandbox=self.use_sandbox,
            )
        return self._client

    async def _send_push_request(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict[str, Any] | None,
    ) -> PushNotificationResult:
        try:
            from aioapns import NotificationRequest, PushType

            # Get user's device token
            device_token = await self._get_user_device_token(user_id)
            if not device_token:
                return PushNotificationResult(
                    success=False,
                    message_id=None,
                    error="User has no device token",
                )

            client = await self._get_client()

            request = NotificationRequest(
                device_token=device_token,
                message={
                    "aps": {
                        "alert": {
                            "title": title,
                            "body": body,
                        },
                        "sound": "default",
                        "badge": 1,
                    },
                    "custom": data or {},
                },
                push_type=PushType.ALERT,
            )

            await client.send_notification(request)

            return PushNotificationResult(
                success=True,
                message_id=None,
                error=None,
            )
        except Exception as e:
            return PushNotificationResult(
                success=False,
                message_id=None,
                error=str(e),
            )

    async def _get_user_device_token(self, user_id: UUID) -> str | None:
        # Query database for user's APNS token
        return None

    async def _send_email_request(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None,
    ) -> EmailResult:
        return EmailResult(success=False, message_id=None, error="Not supported")

    async def _send_sms_request(
        self,
        to: str,
        body: str,
    ) -> SMSResult:
        return SMSResult(success=False, message_id=None, error="Not supported")

    async def _send_in_app_request(
        self,
        user_id: UUID,
        notification: dict[str, Any],
    ) -> bool:
        return True


class SendGridEmailAdapter(BaseNotificationAdapter):
    """SendGrid email adapter"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = None

    async def _get_client(self):
        if self._client is None:
            import sendgrid
            self._client = sendgrid.SendGridAPIClient(api_key=self.api_key)
        return self._client

    async def _send_push_request(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict[str, Any] | None,
    ) -> PushNotificationResult:
        return PushNotificationResult(success=False, message_id=None, error="Not supported")

    async def _send_email_request(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None,
    ) -> EmailResult:
        try:
            from sendgrid.helpers.mail import Content, Email, Mail, To

            client = await self._get_client()

            mail = Mail(
                from_email=Email("noreply@smartcityconcierge.com"),
                to_emails=To(to),
                subject=subject,
                plain_text_content=Content("text/plain", body),
            )

            if html_body:
                mail.add_content(Content("text/html", html_body))

            response = client.send(mail)

            return EmailResult(
                success=response.status_code in [200, 201, 202],
                message_id=response.headers.get("X-Message-Id"),
                error=None if response.status_code in [200, 201, 202] else response.body,
            )
        except Exception as e:
            return EmailResult(
                success=False,
                message_id=None,
                error=str(e),
            )

    async def _send_sms_request(
        self,
        to: str,
        body: str,
    ) -> SMSResult:
        return SMSResult(success=False, message_id=None, error="Not supported")

    async def _send_in_app_request(
        self,
        user_id: UUID,
        notification: dict[str, Any],
    ) -> bool:
        return True


class TwilioSMSAdapter(BaseNotificationAdapter):
    """Twilio SMS adapter"""

    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from twilio.rest import Client
            self._client = Client(self.account_sid, self.auth_token)
        return self._client

    async def _send_push_request(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict[str, Any] | None,
    ) -> PushNotificationResult:
        return PushNotificationResult(success=False, message_id=None, error="Not supported")

    async def _send_email_request(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None,
    ) -> EmailResult:
        return EmailResult(success=False, message_id=None, error="Not supported")

    async def _send_sms_request(
        self,
        to: str,
        body: str,
    ) -> SMSResult:
        try:
            client = await self._get_client()

            message = client.messages.create(
                body=body,
                from_=self.from_number,
                to=to,
            )

            return SMSResult(
                success=True,
                message_id=message.sid,
                error=None,
            )
        except Exception as e:
            return SMSResult(
                success=False,
                message_id=None,
                error=str(e),
            )

    async def _send_in_app_request(
        self,
        user_id: UUID,
        notification: dict[str, Any],
    ) -> bool:
        return True


class InAppNotificationAdapter(BaseNotificationAdapter):
    """In-app notification adapter (stores in database)"""

    def __init__(self, notification_repository):
        self.notification_repository = notification_repository

    async def _send_push_request(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: dict[str, Any] | None,
    ) -> PushNotificationResult:
        return PushNotificationResult(success=False, message_id=None, error="Not supported")

    async def _send_email_request(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: str | None,
    ) -> EmailResult:
        return EmailResult(success=False, message_id=None, error="Not supported")

    async def _send_sms_request(
        self,
        to: str,
        body: str,
    ) -> SMSResult:
        return SMSResult(success=False, message_id=None, error="Not supported")

    async def _send_in_app_request(
        self,
        user_id: UUID,
        notification: dict[str, Any],
    ) -> bool:
        try:
            from ....domain.entities.notification import InAppNotification

            in_app_notification = InAppNotification(
                user_id=user_id,
                title=notification.get("title", ""),
                body=notification.get("body", ""),
                data=notification.get("data", {}),
                notification_type=notification.get("type", "info"),
            )

            await self.notification_repository.add(in_app_notification)
            return True
        except Exception:
            return False
