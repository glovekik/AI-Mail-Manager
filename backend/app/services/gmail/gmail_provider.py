import base64

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


class GmailProvider:

    def __init__(
        self,
        credentials: Credentials,
    ):
        self.credentials = credentials

        self.service = build(
            "gmail",
            "v1",
            credentials=self.credentials,
            cache_discovery=False,
        )

    # ========================================================
    # List messages
    # ========================================================

    def list_messages(
        self,
        max_results: int = 10,
    ):
        messages = []
        page_token = None

        while len(messages) < max_results:

            remaining = (
                max_results
                - len(messages)
            )

            response = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    maxResults=min(
                        100,
                        remaining,
                    ),
                    pageToken=page_token,
                )
                .execute()
            )

            messages.extend(
                response.get(
                    "messages",
                    [],
                )
            )

            page_token = response.get(
                "nextPageToken"
            )

            if not page_token:
                break

        return messages[:max_results]

    # ========================================================
    # Get single message
    # ========================================================

    def get_message(
        self,
        message_id: str,
    ):
        return (
            self.service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="full",
            )
            .execute()
        )

    # ========================================================
    # Get messages
    # ========================================================

    def get_messages(
        self,
        max_results: int = 10,
    ):
        message_refs = self.list_messages(
            max_results
        )

        emails = []

        for message_ref in message_refs:

            message = self.get_message(
                message_ref["id"]
            )

            normalized_email = (
                self._normalize_message(
                    message
                )
            )

            emails.append(
                normalized_email
            )

        return emails

    # ========================================================
    # Mark as read
    # ========================================================

    def mark_as_read(
        self,
        message_id: str,
    ):
        return (
            self.service.users()
            .messages()
            .modify(
                userId="me",
                id=message_id,
                body={
                    "removeLabelIds": [
                        "UNREAD"
                    ]
                },
            )
            .execute()
        )

    # ========================================================
    # Mark as unread
    # ========================================================

    def mark_as_unread(
        self,
        message_id: str,
    ):
        return (
            self.service.users()
            .messages()
            .modify(
                userId="me",
                id=message_id,
                body={
                    "addLabelIds": [
                        "UNREAD"
                    ]
                },
            )
            .execute()
        )

    # ========================================================
    # Archive
    # ========================================================

    def archive_message(
        self,
        message_id: str,
    ):
        return (
            self.service.users()
            .messages()
            .modify(
                userId="me",
                id=message_id,
                body={
                    "removeLabelIds": [
                        "INBOX"
                    ]
                },
            )
            .execute()
        )

    # ========================================================
    # Move to trash
    # ========================================================

    def trash_message(
        self,
        message_id: str,
    ):
        return (
            self.service.users()
            .messages()
            .trash(
                userId="me",
                id=message_id,
            )
            .execute()
        )

    # ========================================================
    # Normalize Gmail message
    # ========================================================

    def _normalize_message(
        self,
        message: dict,
    ):
        payload = message.get(
            "payload",
            {},
        )

        headers = payload.get(
            "headers",
            [],
        )

        header_map = {
            header["name"].lower(): header["value"]
            for header in headers
        }

        body = self._extract_body(
            payload
        )

        labels = message.get(
            "labelIds",
            [],
        )

        return {
            "id": message.get(
                "id"
            ),
            "thread_id": message.get(
                "threadId"
            ),
            "sender": (
                self._extract_email_address(
                    header_map.get(
                        "from",
                        "",
                    )
                )
            ),
            "sender_name": (
                self._extract_sender_name(
                    header_map.get(
                        "from",
                        "",
                    )
                )
            ),
            "subject": header_map.get(
                "subject",
                "",
            ),
            "received_at": header_map.get(
                "date",
                "",
            ),
            "snippet": message.get(
                "snippet",
                "",
            ),
            "body": body,
            "labels": labels,
            "is_read": (
                "UNREAD" not in labels
            ),
        }

    # ========================================================
    # Extract body
    # ========================================================

    def _extract_body(
        self,
        payload: dict,
    ):
        body_data = (
            payload
            .get("body", {})
            .get("data")
        )

        if body_data:
            return self._decode_body(
                body_data
            )

        parts = payload.get(
            "parts",
            [],
        )

        # ----------------------------------------------------
        # Look for plain text
        # ----------------------------------------------------

        for part in parts:

            mime_type = part.get(
                "mimeType",
                "",
            )

            if mime_type == "text/plain":

                data = (
                    part
                    .get("body", {})
                    .get("data")
                )

                if data:
                    return self._decode_body(
                        data
                    )

        # ----------------------------------------------------
        # Look through nested MIME parts
        # ----------------------------------------------------

        for part in parts:

            nested_parts = part.get(
                "parts"
            )

            if nested_parts:

                body = self._extract_body(
                    {
                        "parts": nested_parts
                    }
                )

                if body:
                    return body

        return ""

    # ========================================================
    # Decode body
    # ========================================================

    @staticmethod
    def _decode_body(
        data: str,
    ):
        decoded_bytes = (
            base64.urlsafe_b64decode(
                data
                + "="
                * (-len(data) % 4)
            )
        )

        return decoded_bytes.decode(
            "utf-8",
            errors="replace",
        )

    # ========================================================
    # Extract email address
    # ========================================================

    @staticmethod
    def _extract_email_address(
        sender: str,
    ):
        if (
            "<" in sender
            and ">" in sender
        ):
            return (
                sender
                .split("<", 1)[1]
                .split(">", 1)[0]
                .strip()
            )

        return sender.strip()

    # ========================================================
    # Extract sender name
    # ========================================================

    @staticmethod
    def _extract_sender_name(
        sender: str,
    ):
        if "<" in sender:
            return (
                sender
                .split("<", 1)[0]
                .strip()
                .strip('"')
            )

        return ""