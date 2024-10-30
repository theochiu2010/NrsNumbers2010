"""Service for managing email recipients from CSV file."""

import os
import csv
import logging
from io import StringIO
from typing import List, Optional

import boto3
from pydantic import BaseModel, EmailStr, Field


logger = logging.getLogger()


class Recipient(BaseModel):
    """Schema for a recipient record from CSV."""

    email: EmailStr
    name: Optional[str] = Field(default="")
    active: bool = Field(default=True)


class RecipientService:
    """Service for managing email recipients from a CSV file stored in S3."""

    def __init__(self):
        """Initialize the service with S3 client and configuration."""
        self.s3_client = boto3.client("s3")
        self.bucket = os.environ["S3_BUCKET"]
        self.file_key = os.environ["RECIPIENTS_FILE"]

    def _read_csv_from_s3(self) -> List[dict]:
        """
        Read and parse CSV file from S3.

        Returns:
            List of dictionaries containing CSV row data

        Raises:
            Exception: If S3 read or CSV parsing fails
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=self.file_key)
            file_content = response["Body"].read().decode("utf-8")
            csv_reader = csv.DictReader(StringIO(file_content))
            return list(csv_reader)

        except Exception as exc:
            logger.error("Error reading CSV from S3: %s", str(exc))
            raise

    def get_active_recipients(self) -> List[str]:
        """
        Get list of active recipient email addresses from CSV.

        Returns:
            List of valid email addresses

        Raises:
            ValueError: If CSV format is invalid
            Exception: If processing fails
        """
        try:
            rows = self._read_csv_from_s3()

            if not rows:
                logger.warning("Empty CSV file")
                return []

            valid_recipients = []
            for row in rows:
                try:
                    recipient = Recipient(
                        email=row["email"].strip(),
                        name=row.get("name", "").strip(),
                        active=row.get("active", "true").lower() == "true",
                    )
                    if recipient.active:
                        valid_recipients.append(recipient)
                except Exception as exc:
                    logger.warning(
                        "Invalid recipient data: %s. Error: %s", row, str(exc)
                    )

            if not valid_recipients:
                logger.warning("No valid recipients found in CSV")
                return []

            logger.info("Found %d valid recipients", len(valid_recipients))
            return [r.email for r in valid_recipients]

        except Exception as exc:
            logger.error("Error processing recipients: %s", str(exc))
            raise

    def get_active_recipients_with_names(self) -> List[dict]:
        """
        Get list of active recipients with their names from CSV.

        Returns:
            List of dictionaries containing email and name

        Raises:
            ValueError: If CSV format is invalid
            Exception: If processing fails
        """
        try:
            rows = self._read_csv_from_s3()

            if not rows:
                logger.warning("Empty CSV file")
                return []

            valid_recipients = []
            for row in rows:
                try:
                    recipient = Recipient(
                        email=row["email"].strip(),
                        name=row.get("name", "").strip(),
                        active=row.get("active", "true").lower() == "true",
                    )
                    if recipient.active:
                        valid_recipients.append(recipient)
                except Exception as exc:
                    logger.warning(
                        "Invalid recipient data: %s. Error: %s", row, str(exc)
                    )

            return [{"email": r.email, "name": r.name} for r in valid_recipients]

        except Exception as exc:
            logger.error("Error processing recipients with names: %s", str(exc))
            raise


def lambda_handler(event, context):
    "a test handler function"
    env = os.environ.get("ENV", "dev")
    try:
        return {"statusCode": 200, "body": f"Hello from {env} environment!"}
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
