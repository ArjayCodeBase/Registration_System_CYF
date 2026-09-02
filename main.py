from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, UploadFile, File
from fastapi import BackgroundTasks
from starlette.requests import ClientDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
import time
import asyncio
from types import SimpleNamespace
import uuid
import shutil
import urllib.error
from fastapi.responses import JSONResponse
import urllib.request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from email.message import EmailMessage
from decimal import Decimal
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    DateTime,
    text,
    Boolean, 
    Text,
    ForeignKey,
    func,
    inspect,
    or_,
    func 
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Session
)

from passlib.context import CryptContext

from pydantic import BaseModel, EmailStr, Field

import datetime

from sqlalchemy import create_engine

import requests
import json
import hmac
import hashlib
import time
import uuid
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ======================================================
# APP CONFIGURATION
# ======================================================

app = FastAPI(
    title="Event Registration System",
    version="1.0.0"
)

# ============================================================
# STATIC FILES
# ============================================================


# ============================================================
# UPLOADED FILES
# ============================================================

app.mount(
    "/uploads",
    StaticFiles(
        directory="/app/data/uploads"
    ),
    name="uploads"
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)






load_dotenv()


# ======================================================
# PAYMONGO CONFIGURATION
# ======================================================

PAYMONGO_SECRET_KEY = os.getenv(
    "PAYMONGO_SECRET_KEY"
)

PAYMONGO_API_URL = os.getenv(
    "PAYMONGO_API_URL",
    "https://api.paymongo.com"
)


# ======================================================
# PAYMONGO WEBHOOK CONFIGURATION
# ======================================================

PAYMONGO_WEBHOOK_SECRET = os.getenv(
    "PAYMONGO_WEBHOOK_SECRET"
)



# ======================================================
# GMAIL API CONFIGURATION
# ======================================================
#
# Gmail API is used for ALL system emails.
#
# Railway environment variables required:
#
#   GMAIL_CLIENT_ID
#   GMAIL_CLIENT_SECRET
#   GMAIL_REFRESH_TOKEN
#   GMAIL_SENDER_EMAIL
#
# No credentials.json is required.
# No token.json is required.
# No custom domain is required.
#
# The Gmail account associated with the refresh token
# is the account that sends the system emails.
# ======================================================

import os
import json
import base64
import httpx
import asyncio

from dotenv import load_dotenv

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# ======================================================
# LOAD ENVIRONMENT VARIABLES
# ======================================================

load_dotenv()


# ======================================================
# GMAIL SETTINGS
# ======================================================

GMAIL_CLIENT_ID = os.getenv(
    "GMAIL_CLIENT_ID",
    ""
).strip()


GMAIL_CLIENT_SECRET = os.getenv(
    "GMAIL_CLIENT_SECRET",
    ""
).strip()


GMAIL_REFRESH_TOKEN = os.getenv(
    "GMAIL_REFRESH_TOKEN",
    ""
).strip()


GMAIL_SENDER_EMAIL = os.getenv(
    "GMAIL_SENDER_EMAIL",
    ""
).strip()


GMAIL_FROM_NAME = os.getenv(
    "GMAIL_FROM_NAME",
    "Event Registration System"
).strip()


GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


# ======================================================
# VALIDATE GMAIL CONFIGURATION
# ======================================================

def _validate_gmail_config():
    """
    Make sure all required Gmail environment variables
    are configured.

    This does NOT expose the secret values.
    """

    missing = []

    if not GMAIL_CLIENT_ID:
        missing.append("GMAIL_CLIENT_ID")

    if not GMAIL_CLIENT_SECRET:
        missing.append("GMAIL_CLIENT_SECRET")

    if not GMAIL_REFRESH_TOKEN:
        missing.append("GMAIL_REFRESH_TOKEN")

    if not GMAIL_SENDER_EMAIL:
        missing.append("GMAIL_SENDER_EMAIL")

    if missing:
        raise RuntimeError(
            "Gmail environment variables are missing: "
            + ", ".join(missing)
        )


# ======================================================
# LOAD GMAIL OAUTH CREDENTIALS
# ======================================================

def _load_gmail_credentials():
    """
    Create Gmail OAuth credentials directly from Railway
    environment variables.

    No credentials.json.
    No token.json.
    No local browser authorization.
    """

    _validate_gmail_config()

    try:

        creds = Credentials(
            token=None,

            refresh_token=GMAIL_REFRESH_TOKEN,

            token_uri="https://oauth2.googleapis.com/token",

            client_id=GMAIL_CLIENT_ID,

            client_secret=GMAIL_CLIENT_SECRET,

            scopes=GMAIL_SCOPES
        )

        return creds

    except Exception as exc:

        raise RuntimeError(
            "Unable to create Gmail OAuth credentials "
            "from environment variables."
        ) from exc


# ======================================================
# GET GMAIL SERVICE
# ======================================================

def get_gmail_service():
    """
    Return an authenticated Gmail API service.

    The Gmail API client automatically uses the refresh
    token to obtain an access token when necessary.
    """

    creds = _load_gmail_credentials()

    return build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False
    )


# ======================================================
# SEND EMAIL THROUGH GMAIL
# ======================================================

def send_gmail(
    recipient_email: str,
    subject: str,
    html_body: str | None = None,
    plain_body: str | None = None,
    reply_to: str | None = None
):
    """
    Send an email through the Gmail API.

    Sender:
        GMAIL_SENDER_EMAIL

    Recipient:
        recipient_email

    No Resend.
    No custom domain.
    No credentials.json.
    No token.json.
    """

    # --------------------------------------------------
    # CLEAN INPUT
    # --------------------------------------------------

    recipient_email = str(
        recipient_email or ""
    ).strip()


    subject = str(
        subject or ""
    ).replace(
        "\r",
        " "
    ).replace(
        "\n",
        " "
    ).strip()


    # --------------------------------------------------
    # VALIDATE
    # --------------------------------------------------

    if not recipient_email:

        raise ValueError(
            "Recipient email is empty."
        )


    if not subject:

        raise ValueError(
            "Email subject is empty."
        )


    _validate_gmail_config()


    # --------------------------------------------------
    # DEFAULT PLAIN TEXT
    # --------------------------------------------------

    if plain_body is None:

        plain_body = (
            "This email contains HTML content. "
            "Please use an HTML-compatible email client."
        )


    if html_body is None:

        html_body = ""


    # --------------------------------------------------
    # CREATE MIME MESSAGE
    # --------------------------------------------------

    message = MIMEMultipart(
        "alternative"
    )


    message["To"] = recipient_email


    message["From"] = (
        f"{GMAIL_FROM_NAME} "
        f"<{GMAIL_SENDER_EMAIL}>"
    )


    message["Subject"] = subject


    if reply_to:

        message["Reply-To"] = str(
            reply_to
        ).strip()


    # --------------------------------------------------
    # PLAIN TEXT PART
    # --------------------------------------------------

    message.attach(
        MIMEText(
            str(plain_body),
            "plain",
            "utf-8"
        )
    )


    # --------------------------------------------------
    # HTML PART
    # --------------------------------------------------

    if html_body:

        message.attach(
            MIMEText(
                str(html_body),
                "html",
                "utf-8"
            )
        )


    # --------------------------------------------------
    # ENCODE MESSAGE
    # --------------------------------------------------

    raw_message = (
        base64.urlsafe_b64encode(
            message.as_bytes()
        )
        .decode("utf-8")
    )


    # --------------------------------------------------
    # SEND THROUGH GMAIL API
    # --------------------------------------------------

    try:

        service = get_gmail_service()


        result = (
            service
            .users()
            .messages()
            .send(
                userId="me",
                body={
                    "raw": raw_message
                }
            )
            .execute()
        )


    except Exception as exc:

        print(
            "GMAIL SEND ERROR:",
            repr(exc)
        )

        raise RuntimeError(
            f"Unable to send Gmail message: {exc}"
        ) from exc


    # --------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------

    return {

        "success": True,

        "provider": "gmail_api",

        "sender":
            GMAIL_SENDER_EMAIL,

        "recipient":
            recipient_email,

        "subject":
            subject,

        "message_id":
            result.get("id")

    }


# ======================================================
# ASYNC GMAIL SENDER
# ======================================================

async def send_gmail_async(
    recipient_email: str,
    subject: str,
    html_body: str | None = None,
    plain_body: str | None = None,
    reply_to: str | None = None
):
    """
    Async Gmail API sender.

    Gmail's Python client is synchronous, so the actual
    send operation runs in a worker thread so that it does
    not block FastAPI.
    """

    return await asyncio.to_thread(
        send_gmail,
        recipient_email,
        subject,
        html_body,
        plain_body,
        reply_to
    )




# ======================================================
# SQLITE DATABASE
# ======================================================

DATABASE_URL = "sqlite:////app/data/registration_system.db"
# DATABASE_URL = "sqlite:///./registration_system.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

Base = declarative_base()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
        
# ======================================================
# PASSWORD HASHING
# ======================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str):

    return pwd_context.hash(password)


def verify_password(
    plain_password,
    hashed_password
):

    return pwd_context.verify(
        plain_password,
        hashed_password
    )





















# ======================================================
# DATABASE MODELS
# ======================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    fname = Column(String(100))
    mname = Column(String(100))
    lname = Column(String(100))

    age = Column(Integer)

    birthday = Column(Date)

    address = Column(String(255))

    email = Column(
        String(150),
        unique=True
    )

    sex = Column(String(20))

    local_church = Column(String(150))

    contact_number = Column(String(20))

    sector = Column(String(100))

    username = Column(
        String(100),
        unique=True
    )

    password = Column(String(255))

    role = Column(String(50))

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
    
    last_login = Column(
        DateTime, 
        nullable=True
    )
    
    
# ======================================================
# EVENT MODEL
# ======================================================

class Event(Base):

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    event_name = Column(String(100), nullable=False)

    registration_start = Column(Date, nullable=False)

    registration_end = Column(Date, nullable=False)

    kickoff_date = Column(Date, nullable=False)

    wrapup_date = Column(Date, nullable=False)

    is_archived = Column(Integer, default=0)

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
    

# ======================================================
# PARTICIPANT MODEL
# ======================================================

class Participant(Base):

    __tablename__ = "participants"

    # ======================================================
    # PRIMARY KEY
    # ======================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ======================================================
    # EVENT REFERENCE
    # ======================================================

    event_id = Column(
        Integer,
        nullable=False
    )

    # ======================================================
    # EVENT SNAPSHOT
    # ======================================================

    event_name = Column(
        String(100),
        nullable=False
    )

    registration_start = Column(
        Date,
        nullable=False
    )

    registration_end = Column(
        Date,
        nullable=False
    )

    kickoff_date = Column(
        Date,
        nullable=False
    )

    wrapup_date = Column(
        Date,
        nullable=False
    )

    # ======================================================
    # REGISTRATION INFORMATION
    # ======================================================

    registration_number = Column(
        String(30),
        unique=True,
        nullable=False
    )

    registration_date = Column(
        Date,
        default=datetime.date.today
    )

    registration_phase = Column(
        String(20),
        nullable=False
    )

    registration_status = Column(
        String(20),
        nullable=False,
        default="Pending"
    )
    
    participant_type = Column(
    String(50),
    nullable=False,
    default="Regular Participants"
    )

    # ======================================================
    # PARTICIPANT INFORMATION
    # ======================================================

    fname = Column(
        String(100),
        nullable=False
    )

    mname = Column(
    String(100),
    nullable=True
    )

    lname = Column(
        String(100),
        nullable=False
    )

    registration_age = Column(
        Integer,
        nullable=False
    )

    sex = Column(
        String(20)
    )

    birthdate = Column(
        Date
    )

    address = Column(
        String(255)
    )

    contact_number = Column(
        String(20)
    )

    emergency_contact = Column(
        String(20)
    )

    email = Column(
        String(150)
    )

    local_church = Column(
        String(150)
    )

    sector = Column(
        String(100)
    )
    
    # ======================================================
    # MERCHANDISE PAYMENT STATUS
    # ======================================================

    tshirt_status = Column(
        String(20),
        nullable=False,
        default="Unpaid"
    )

    lanyard_status = Column(
        String(20),
        nullable=False,
        default="Unpaid"
    )    
    
    tshirt_size = Column(
    String(10),
    nullable=True
    )

    # ======================================================
    # RECORD STATUS
    # ======================================================

    is_archived = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )

# ======================================================
# QUESTIONNAIRE MODEL
# ======================================================

class Questionnaire(Base):

    __tablename__ = "questionnaires"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    participant_id = Column(
        Integer,
        unique=True,
        nullable=False
    )

    # -----------------------------
    # Section 1
    # -----------------------------

    camp_attendance = Column(String(100))

    leadership_position = Column(String(100))

    church_involvement = Column(String(100))

    # -----------------------------
    # Section 2
    # -----------------------------

    primary_strength = Column(String(150))

    ministry_skill = Column(String(150))

    # -----------------------------
    # Section 3
    # -----------------------------

    salvation_assurance = Column(String(255))

    daily_devotion = Column(String(255))

    ministry_involvement = Column(String(255))

    sermon_notes = Column(String(255))

    small_group = Column(String(255))

    gospel_sharing = Column(String(255))

    temptation_response = Column(String(255))

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
    
# ======================================================
# PARTICIPANT EVALUATION
# ======================================================

class ParticipantEvaluation(Base):

    __tablename__ = "participant_evaluations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    participant_id = Column(
        Integer,
        unique=True,
        nullable=False
    )

    influence_score = Column(
        Integer,
        default=0
    )

    spiritual_score = Column(
        Integer,
        default=0
    )

    creative_status = Column(
        String(30)
    )

    participant_tier = Column(
        String(50)
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )

# ======================================================
# EVENT RULES AGREEMENT
# ======================================================

class EventRulesAgreement(Base):

    __tablename__ = "event_rules_agreements"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    participant_id = Column(
        Integer,
        unique=True,
        nullable=False
    )

    agreed = Column(
        Integer,
        default=0
    )

    agreed_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )        

# ======================================================
# CHAPERONE MODEL
# ======================================================

class Chaperone(Base):

    __tablename__ = "chaperones"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ======================================================
    # EVENT REFERENCE
    # ======================================================

    event_id = Column(
        Integer,
        nullable=False
    )

    # ======================================================
    # CHAPERONE INFORMATION
    # ======================================================

    fname = Column(
        String(100),
        nullable=False
    )

    mname = Column(
        String(100),
        nullable=True
    )

    lname = Column(
        String(100),
        nullable=False
    )


    sex = Column(
        String(20),
        nullable=True
    )

    birthday = Column(
        Date,
        nullable=True
    )

    contact = Column(
        String(20),
        nullable=True
    )

    local_church = Column(
        String(150),
        nullable=True
    )

    sector = Column(
        String(100),
        nullable=True
    )

    # ======================================================
    # RECORD STATUS
    # ======================================================

    is_archived = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )
    
    
# ======================================================
# STAFF MODEL
# ======================================================

class Staff(Base):

    __tablename__ = "staff"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ======================================================
    # EVENT REFERENCE
    # ======================================================

    event_id = Column(
        Integer,
        nullable=False
    )

    # ======================================================
    # STAFF INFORMATION
    # ======================================================

    fname = Column(
        String(100),
        nullable=False
    )

    mname = Column(
        String(100)
    )

    lname = Column(
        String(100),
        nullable=False
    )
    
     # ADD THIS
    position = Column(String, nullable=True)

    sex = Column(
        String(20),
        nullable=False
    )

    birthday = Column(
        Date,
        nullable=False
    )

    contact = Column(
        String(20),
        nullable=False
    )

    local_church = Column(
        String(150),
        nullable=False
    )

    sector = Column(
        String(100),
        nullable=False
    )

    # ======================================================
    # RECORD STATUS
    # ======================================================

    is_archived = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    ) 
    
    
    
    
       

# ======================================================
# PAYMENT MODEL
# ======================================================

class Payment(Base):

    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ==================================================
    # PARTICIPANT
    # ==================================================

    participant_id = Column(
        Integer,
        ForeignKey("participants.id"),
        nullable=True
    )

    # ==================================================
    # PAYMENT TYPE
    # ==================================================
    #
    # Participant
    # Sponsor
    # Store
    #

    payment_type = Column(
        String(30),
        nullable=False,
        default="Participant",
        index=True
    )

    # ==================================================
    # STORE PURCHASE
    # ==================================================
    #
    # These fields are important.
    #
    # The webhook must be able to identify the
    # purchased StoreItem without depending on
    # PayMongo metadata.
    #


    # ========================================================
    # STORE
    # ========================================================

    store_order_id = Column(
        String(100),
        nullable=True,
        index=True
    )

    
    store_item_id = Column(
        Integer,
        ForeignKey("store_items.id"),
        nullable=True,
        index=True
    )

    store_quantity = Column(
        Integer,
        nullable=True,
        default=1
    )

    # Store clothing size.
    #
    # Example:
    # S
    # M
    # L
    # XL
    # 2XL
    #

    store_size = Column(
        String(20),
        nullable=True
    )

    # ==================================================
    # AMOUNT
    # ==================================================

    amount = Column(
        Integer,
        nullable=False
    )

    currency = Column(
        String(10),
        nullable=False,
        default="PHP"
    )

    # ==================================================
    # PAYMENT STATUS
    # ==================================================

    status = Column(
        String(30),
        nullable=False,
        default="Pending",
        index=True
    )

    # ==================================================
    # PARTICIPANT ITEMS
    # ==================================================

    tshirt_selected = Column(
        Integer,
        default=0
    )

    lanyard_selected = Column(
        Integer,
        default=0
    )

    tshirt_size = Column(
        String(10),
        nullable=True
    )

    # ==================================================
    # SPONSORSHIP
    # ==================================================

    sponsorship_tier = Column(
        String(30),
        nullable=True,
        index=True
    )

    sponsor_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    # ==================================================
    # PAYMONGO
    # ==================================================

    paymongo_link_id = Column(
        String(100),
        nullable=True,
        index=True
    )

    paymongo_payment_id = Column(
        String(100),
        nullable=True,
        index=True
    )

    paymongo_reference = Column(
        String(100),
        nullable=True,
        index=True
    )

    checkout_url = Column(
        String(500),
        nullable=True
    )

    # ==================================================
    # PAYMENT DESCRIPTION
    # ==================================================

    description = Column(
        String(500),
        nullable=True
    )

    # ==================================================
    # CUSTOMER INFORMATION
    # ==================================================

    customer_name = Column(
        String(255),
        nullable=True
    )

    customer_contact = Column(
        String(100),
        nullable=True
    )

    customer_email = Column(
        String(255),
        nullable=True
    )

    # ==================================================
    # PAYMENT DATES
    # ==================================================

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    paid_at = Column(
        DateTime,
        nullable=True
    )
    
    
    
    
    
    


# ============================================================
# SPONSORSHIP PACKAGE
# ============================================================

class SponsorshipPackage(Base):

    __tablename__ = "sponsorship_packages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    tier = Column(
        String(50),
        nullable=False,
        unique=True
    )

    minimum_amount = Column(
        Integer,
        nullable=False
    )

    maximum_amount = Column(
        Integer,
        nullable=True
    )

    description = Column(
        Text,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )


# ============================================================
# CASH SPONSORSHIP
# ============================================================

class CashSponsorship(Base):

    __tablename__ = "cash_sponsorships"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    sponsor_name = Column(
        String(255),
        nullable=False
    )

    local_church = Column(
        String(255),
        nullable=False
    )

    contact = Column(
        String(100),
        nullable=False
    )

    sector = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        nullable=False
    )

    selected_tier = Column(
        String(50),
        nullable=False
    )

    donation_amount = Column(
        Integer,
        nullable=False
    )

    payment_status = Column(
        String(30),
        default="Pending",
        nullable=False
    )

    paymongo_link_id = Column(
        String(255),
        nullable=True,
        index=True
    )

    paymongo_reference = Column(
        String(255),
        nullable=True,
        index=True
    )

    payment_url = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now,
        nullable=False
    )

    paid_at = Column(
        DateTime,
        nullable=True
    )
    
    cash_total_added = Column(
    Integer,
    default=False,
    nullable=False
    )


# ============================================================
# ITEM DONATION INVENTORY
# ============================================================

class SponsorshipItem(Base):

    __tablename__ = "sponsorship_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    item_name = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    total_quantity = Column(
        Integer,
        nullable=False,
        default=0
    )

    remaining_quantity = Column(
        Integer,
        nullable=False,
        default=0
    )

    unit = Column(
        String(50),
        nullable=False,
        default="piece"
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now,
        nullable=False
    )


# ============================================================
# ITEM DONATION RECORD
# ============================================================

class ItemSponsorship(Base):

    __tablename__ = "item_sponsorships"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    sponsor_name = Column(
        String(255),
        nullable=False
    )

    local_church = Column(
        String(255),
        nullable=False
    )
    
    visiting_church = Column(
    String,
    nullable=True
    )

    contact = Column(
        String(100),
        nullable=False
    )

    sector = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(255),
        nullable=False
    )

    item_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    item_name = Column(
        String(255),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    status = Column(
        String(30),
        default="Confirmed",
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now,
        nullable=False
    )


# ============================================================
# STORE ITEM MODEL
# ============================================================

class StoreItem(Base):

    __tablename__ = "store_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # ITEM NAME
    # --------------------------------------------------------

    item_name = Column(
        String(255),
        nullable=False
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = Column(
        String(1000),
        nullable=True
    )

    # --------------------------------------------------------
    # CATEGORY
    #
    # clothes
    # souvenir
    # others
    # --------------------------------------------------------

    category = Column(
        String(50),
        nullable=False,
        default="others",
        index=True
    )

    # --------------------------------------------------------
    # AVAILABLE SIZES
    #
    # Stored as JSON text.
    #
    # Example:
    #
    # ["S","M","L","XL","2XL"]
    #
    # For non-clothes:
    #
    # NULL
    # --------------------------------------------------------

    sizes = Column(
        Text,
        nullable=True
    )

    # --------------------------------------------------------
    # INVENTORY
    # --------------------------------------------------------

    quantity = Column(
        Integer,
        nullable=False,
        default=0
    )

    # --------------------------------------------------------
    # PRICE
    #
    # Store this as PHP amount.
    #
    # Example:
    #
    # 350
    #
    # means ₱350.00
    # --------------------------------------------------------

    price = Column(
        Integer,
        nullable=False
    )
    
    # --------------------------------------------------------
    # IMAGES
    # --------------------------------------------------------
    
    
    image_url = Column(
    String,
    nullable=True
    )

    # --------------------------------------------------------
    # ARCHIVE
    # --------------------------------------------------------

    is_archived = Column(
        Integer,
        nullable=False,
        default=0
    )

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    created_at = Column(
        DateTime,
        default=datetime.datetime.now
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now
    )

class RegistrationItem(Base):

    __tablename__ = "registration_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    item_name = Column(
        String(100),
        unique=True,
        nullable=False
    )

    price = Column(
        Integer,
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        nullable=False
    )


# ============================================================
# CASH DONATION TOTAL MODEL
# ============================================================

class CashDonationTotal(Base):

    __tablename__ = "cash_donation_total"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    total_amount = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.datetime.now,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.datetime.now,
        onupdate=datetime.datetime.now,
        nullable=False
    )











# def migrate_cash_sponsorship_cash_total_added():

#     with engine.connect() as connection:

#         # ====================================================
#         # CHECK EXISTING COLUMNS
#         # ====================================================

#         result = connection.execute(
#             text("""
#                 PRAGMA table_info(cash_sponsorships)
#             """)
#         )

#         columns = {
#             row[1]: row
#             for row in result
#         }

#         # ====================================================
#         # COLUMN DOES NOT EXIST
#         # ====================================================
#         #
#         # If the column does not exist at all, simply create
#         # it as INTEGER.
#         #
#         # ====================================================

#         if "cash_total_added" not in columns:

#             connection.execute(
#                 text("""
#                     ALTER TABLE cash_sponsorships
#                     ADD COLUMN cash_total_added
#                     INTEGER NOT NULL DEFAULT 0
#                 """)
#             )

#             connection.commit()

#             print(
#                 "Created cash_total_added INTEGER column."
#             )

#             return

#         # ====================================================
#         # EXISTING COLUMN
#         #
#         # SQLite cannot directly change BOOLEAN -> INTEGER.
#         #
#         # Rename the old column first.
#         # ====================================================

#         old_column = columns[
#             "cash_total_added"
#         ]

#         old_type = str(
#             old_column[2] or ""
#         ).upper()

#         print(
#             "Existing cash_total_added type:",
#             old_type
#         )

#         # ====================================================
#         # ALREADY INTEGER
#         # ====================================================

#         if old_type in [
#             "INTEGER",
#             "INT",
#             "BIGINT"
#         ]:

#             print(
#                 "cash_total_added is already INTEGER."
#             )

#             connection.commit()

#             return

#         # ====================================================
#         # RENAME OLD BOOLEAN COLUMN
#         # ====================================================

#         connection.execute(
#             text("""
#                 ALTER TABLE cash_sponsorships
#                 RENAME COLUMN cash_total_added
#                 TO cash_total_added_old
#             """)
#         )

#         # ====================================================
#         # CREATE CORRECT INTEGER COLUMN
#         # ====================================================

#         connection.execute(
#             text("""
#                 ALTER TABLE cash_sponsorships
#                 ADD COLUMN cash_total_added
#                 INTEGER NOT NULL DEFAULT 0
#             """)
#         )

#         # ====================================================
#         # BACKFILL OLD PAID CASH SPONSORSHIPS
#         # ====================================================
#         #
#         # Old records did not have cash_total_added.
#         #
#         # If an old sponsorship is already Paid, assume its
#         # donation amount has already been received.
#         #
#         # donation_amount is stored in centavos.
#         #
#         # Example:
#         #
#         # donation_amount = 50000
#         # cash_total_added = 500
#         #
#         # This prevents old paid sponsorships from being added
#         # again when the webhook is triggered.
#         #
#         # ====================================================

#         connection.execute(
#             text("""
#                 UPDATE cash_sponsorships
#                 SET cash_total_added =
#                     CAST(
#                         COALESCE(
#                             donation_amount,
#                             0
#                         ) / 100
#                         AS INTEGER
#                     )
#                 WHERE LOWER(
#                     COALESCE(
#                         payment_status,
#                         ''
#                     )
#                 ) = 'paid'
#             """)
#         )

#         # ====================================================
#         # OLD PENDING / FAILED RECORDS
#         #
#         # These should remain 0 because their donation has not
#         # been added to CashDonationTotal.
#         # ====================================================

#         connection.execute(
#             text("""
#                 UPDATE cash_sponsorships
#                 SET cash_total_added = 0
#                 WHERE LOWER(
#                     COALESCE(
#                         payment_status,
#                         ''
#                     )
#                 ) != 'paid'
#             """)
#         )

#         # ====================================================
#         # DROP OLD BOOLEAN COLUMN
#         # ====================================================
#         #
#         # SQLite versions supporting DROP COLUMN can remove it.
#         #
#         # ====================================================

#         try:

#             connection.execute(
#                 text("""
#                     ALTER TABLE cash_sponsorships
#                     DROP COLUMN cash_total_added_old
#                 """)
#             )

#         except Exception as e:

#             print(
#                 "WARNING: Could not drop old "
#                 "cash_total_added_old column:",
#                 repr(e)
#             )

#             print(
#                 "The old column can remain temporarily."
#             )

#         # ====================================================
#         # COMMIT
#         # ====================================================

#         connection.commit()

#         print(
#             "cash_total_added successfully migrated "
#             "to INTEGER."
#         )







# def migrate_staff_table():
#     inspector = inspect(engine)

#     columns = {
#         column["name"]
#         for column in inspector.get_columns("staff")
#     }

#     with engine.begin() as conn:

#         if "position" not in columns:
#             conn.execute(
#                 text("ALTER TABLE staff ADD COLUMN position VARCHAR")
#             )

#         if "sex" in columns:
#             pass

#         if "birthday" in columns:
#             pass

#         if "contact" in columns:
#             pass

#         if "local_church" in columns:
#             pass

#         if "sector" in columns:
#             pass


# # ============================================================
# # MIGRATE CASH SPONSORSHIP COLUMNS
# # ============================================================

# def migrate_cash_sponsorship_columns():

#     with engine.connect() as connection:

#         # ----------------------------------------------------
#         # CHECK EXISTING COLUMNS
#         # ----------------------------------------------------

#         result = connection.execute(
#             text(
#                 "PRAGMA table_info(cash_sponsorships)"
#             )
#         )

#         columns = [
#             row[1]
#             for row in result
#         ]

#         # ----------------------------------------------------
#         # ADD CASH TOTAL ADDED
#         # ----------------------------------------------------

#         if "cash_total_added" not in columns:

#             connection.execute(
#                 text("""
#                     ALTER TABLE cash_sponsorships
#                     ADD COLUMN cash_total_added
#                     BOOLEAN
#                     DEFAULT 0
#                     NOT NULL
#                 """)
#             )

#             connection.commit()

#         # ----------------------------------------------------
#         # IMPORTANT:
#         #
#         # OLD PAID SPONSORSHIPS
#         #
#         # These records existed before
#         # cash_total_added was created.
#         #
#         # Mark them as already added so the new
#         # sponsorship logic does NOT add them again.
#         # ----------------------------------------------------

#         connection.execute(
#             text("""
#                 UPDATE cash_sponsorships

#                 SET cash_total_added = 1

#                 WHERE
#                     LOWER(
#                         TRIM(
#                             COALESCE(
#                                 payment_status,
#                                 ''
#                             )
#                         )
#                     )

#                     IN (
#                         'paid',
#                         'success',
#                         'succeeded',
#                         'completed'
#                     )
#             """)
#         )

#         # ----------------------------------------------------
#         # OLD PENDING / FAILED RECORDS
#         #
#         # These should NOT be added to the cash total.
#         # ----------------------------------------------------

#         connection.execute(
#             text("""
#                 UPDATE cash_sponsorships

#                 SET cash_total_added = 0

#                 WHERE
#                     LOWER(
#                         TRIM(
#                             COALESCE(
#                                 payment_status,
#                                 ''
#                             )
#                         )
#                     )

#                     NOT IN (
#                         'paid',
#                         'success',
#                         'succeeded',
#                         'completed'
#                     )
#             """)
#         )

#         # ----------------------------------------------------
#         # COMMIT
#         # ----------------------------------------------------

#         connection.commit()




# # ============================================================
# # MIGRATE STORE ITEM TABLE
# # ============================================================

# def migrate_store_item_columns():

#     with engine.connect() as connection:

#         result = connection.execute(
#             text("PRAGMA table_info(store_items)")
#         )

#         columns = [
#             row[1]
#             for row in result
#         ]

#         # ----------------------------------------------------
#         # CATEGORY
#         # ----------------------------------------------------

#         if "category" not in columns:

#             connection.execute(
#                 text("""
#                     ALTER TABLE store_items
#                     ADD COLUMN category
#                     VARCHAR(50)
#                     NOT NULL
#                     DEFAULT 'others'
#                 """)
#             )

#         # ----------------------------------------------------
#         # SIZES
#         # ----------------------------------------------------

#         if "sizes" not in columns:

#             connection.execute(
#                 text("""
#                     ALTER TABLE store_items
#                     ADD COLUMN sizes
#                     TEXT
#                 """)
#             )

#         # ----------------------------------------------------
#         # IMAGE
#         # ----------------------------------------------------

#         if "image_url" not in columns:

#             connection.execute(
#                 text("""
#                     ALTER TABLE store_items
#                     ADD COLUMN image_url
#                     TEXT
#                 """)
#             )

#         # ----------------------------------------------------
#         # COMMIT
#         # ----------------------------------------------------

#         connection.commit()







    
    
# # # ======================================================
# # # MIGRATE PAYMENT TABLE
# # # ======================================================

# # def migrate_payment_columns():

# #     with engine.connect() as connection:

# #         result = connection.execute(
# #             text("PRAGMA table_info(payments)")
# #         )

# #         columns = [
# #             row[1]
# #             for row in result
# #         ]

# #         # ----------------------------------------------
# #         # PAYMENT TYPE
# #         # ----------------------------------------------

# #         if "payment_type" not in columns:

# #             connection.execute(
# #                 text("""
# #                     ALTER TABLE payments
# #                     ADD COLUMN payment_type
# #                     VARCHAR(30)
# #                     NOT NULL
# #                     DEFAULT 'Participant'
# #                 """)
# #             )

# #         # ----------------------------------------------
# #         # SPONSORSHIP TIER
# #         # ----------------------------------------------

# #         if "sponsorship_tier" not in columns:

# #             connection.execute(
# #                 text("""
# #                     ALTER TABLE payments
# #                     ADD COLUMN sponsorship_tier
# #                     VARCHAR(30)
# #                 """)
# #             )

# #         # ----------------------------------------------
# #         # SPONSOR ID
# #         # ----------------------------------------------

# #         if "sponsor_id" not in columns:

# #             connection.execute(
# #                 text("""
# #                     ALTER TABLE payments
# #                     ADD COLUMN sponsor_id
# #                     INTEGER
# #                 """)
# #             )

# #         # ----------------------------------------------
# #         # DESCRIPTION
# #         # ----------------------------------------------

# #         if "description" not in columns:

# #             connection.execute(
# #                 text("""
# #                     ALTER TABLE payments
# #                     ADD COLUMN description
# #                     VARCHAR(500)
# #                 """)
# #             )

# #         # ----------------------------------------------
# #         # CUSTOMER NAME
# #         # ----------------------------------------------

# #         if "customer_name" not in columns:

# #             connection.execute(
# #                 text("""
# #                     ALTER TABLE payments
# #                     ADD COLUMN customer_name
# #                     VARCHAR(150)
# #                 """)
# #             )

# #         # ----------------------------------------------
# #         # CUSTOMER CONTACT
# #         # ----------------------------------------------

# #         if "customer_contact" not in columns:

# #             connection.execute(
# #                 text("""
# #                     ALTER TABLE payments
# #                     ADD COLUMN customer_contact
# #                     VARCHAR(50)
# #                 """)
# #             )

# #         # ----------------------------------------------
# #         # CUSTOMER EMAIL
# #         # ----------------------------------------------

# #         if "customer_email" not in columns:

# #             connection.execute(
# #                 text("""
# #                     ALTER TABLE payments
# #                     ADD COLUMN customer_email
# #                     VARCHAR(255)
# #                 """)
# #             )

# #         connection.commit()


# # # ======================================================
# # # MAKE PARTICIPANT ID NULLABLE
# # #
# # # REQUIRED FOR STORE PAYMENTS
# # # ======================================================

# # def migrate_payment_participant_nullable():

# #     with engine.connect() as connection:

# #         # --------------------------------------------------
# #         # CHECK PAYMENTS TABLE
# #         # --------------------------------------------------

# #         result = connection.execute(
# #             text("""
# #                 PRAGMA table_info(payments)
# #             """)
# #         )

# #         columns = list(result)

# #         participant_column = None

# #         for column in columns:

# #             # PRAGMA table_info:
# #             #
# #             # column[0] = cid
# #             # column[1] = name
# #             # column[2] = type
# #             # column[3] = notnull
# #             # column[4] = default
# #             # column[5] = primary key

# #             if column[1] == "participant_id":

# #                 participant_column = column

# #                 break

# #         # --------------------------------------------------
# #         # PARTICIPANT COLUMN NOT FOUND
# #         # --------------------------------------------------

# #         if participant_column is None:

# #             raise RuntimeError(
# #                 "payments.participant_id column was not found."
# #             )

# #         # --------------------------------------------------
# #         # ALREADY NULLABLE
# #         # --------------------------------------------------

# #         if participant_column[3] == 0:

# #             print(
# #                 "Payment migration: "
# #                 "participant_id is already nullable."
# #             )

# #             return

# #         # --------------------------------------------------
# #         # GET ORIGINAL TABLE SQL
# #         # --------------------------------------------------

# #         result = connection.execute(
# #             text("""
# #                 SELECT sql
# #                 FROM sqlite_master
# #                 WHERE type = 'table'
# #                 AND name = 'payments'
# #             """)
# #         )

# #         row = result.fetchone()

# #         if not row or not row[0]:

# #             raise RuntimeError(
# #                 "Unable to read payments table definition."
# #             )

# #         original_sql = row[0]

# #         # --------------------------------------------------
# #         # RENAME ORIGINAL TABLE
# #         # --------------------------------------------------

# #         connection.execute(
# #             text("""
# #                 ALTER TABLE payments
# #                 RENAME TO payments_old
# #             """)
# #         )

# #         # --------------------------------------------------
# #         # CHANGE PARTICIPANT_ID
# #         #
# #         # Remove NOT NULL from participant_id only.
# #         # --------------------------------------------------

# #         new_sql = original_sql

# #         replacements = [

# #             (
# #                 '"participant_id" INTEGER NOT NULL',
# #                 '"participant_id" INTEGER'
# #             ),

# #             (
# #                 '`participant_id` INTEGER NOT NULL',
# #                 '`participant_id` INTEGER'
# #             ),

# #             (
# #                 'participant_id INTEGER NOT NULL',
# #                 'participant_id INTEGER'
# #             ),

# #             (
# #                 '"participant_id" INTEGER NOT NULL DEFAULT',
# #                 '"participant_id" INTEGER DEFAULT'
# #             ),

# #             (
# #                 '`participant_id` INTEGER NOT NULL DEFAULT',
# #                 '`participant_id` INTEGER DEFAULT'
# #             ),

# #             (
# #                 'participant_id INTEGER NOT NULL DEFAULT',
# #                 'participant_id INTEGER DEFAULT'
# #             )
# #         ]

# #         for old_text, new_text in replacements:

# #             new_sql = new_sql.replace(
# #                 old_text,
# #                 new_text
# #             )

# #         # --------------------------------------------------
# #         # CHANGE TABLE NAME
# #         # --------------------------------------------------

# #         new_sql = new_sql.replace(
# #             '"payments"',
# #             '"payments_new"',
# #             1
# #         )

# #         new_sql = new_sql.replace(
# #             '`payments`',
# #             '`payments_new`',
# #             1
# #         )

# #         # Handle unquoted CREATE TABLE payments
# #         if (
# #             "CREATE TABLE payments_new"
# #             not in new_sql
# #         ):

# #             new_sql = new_sql.replace(
# #                 "CREATE TABLE payments",
# #                 "CREATE TABLE payments_new",
# #                 1
# #             )

# #         # --------------------------------------------------
# #         # VERIFY PARTICIPANT_ID IS NOW NULLABLE
# #         # --------------------------------------------------

# #         if (
# #             'participant_id INTEGER NOT NULL'
# #             in new_sql
# #             or
# #             '"participant_id" INTEGER NOT NULL'
# #             in new_sql
# #             or
# #             '`participant_id` INTEGER NOT NULL'
# #             in new_sql
# #         ):

# #             # Roll back before raising the error.
# #             connection.rollback()

# #             raise RuntimeError(
# #                 "Unable to make payments.participant_id nullable. "
# #                 "The existing SQLite table definition has an "
# #                 "unexpected format."
# #             )

# #         # --------------------------------------------------
# #         # CREATE NEW PAYMENTS TABLE
# #         # --------------------------------------------------

# #         connection.execute(
# #             text(new_sql)
# #         )

# #         # --------------------------------------------------
# #         # GET COLUMN NAMES
# #         # --------------------------------------------------

# #         column_result = connection.execute(
# #             text("""
# #                 PRAGMA table_info(payments_old)
# #             """)
# #         )

# #         column_names = [
# #             row[1]
# #             for row in column_result
# #         ]

# #         if not column_names:

# #             connection.rollback()

# #             raise RuntimeError(
# #                 "Unable to read columns from payments_old."
# #             )

# #         column_list = ", ".join(
# #             f'"{column}"'
# #             for column in column_names
# #         )

# #         # --------------------------------------------------
# #         # COPY EXISTING PAYMENT DATA
# #         # --------------------------------------------------

# #         connection.execute(
# #             text(
# #                 f"""
# #                 INSERT INTO payments_new (
# #                     {column_list}
# #                 )
# #                 SELECT
# #                     {column_list}
# #                 FROM payments_old
# #                 """
# #             )
# #         )

# #         # --------------------------------------------------
# #         # REMOVE OLD TABLE
# #         # --------------------------------------------------

# #         connection.execute(
# #             text("""
# #                 DROP TABLE payments_old
# #             """)
# #         )

# #         # --------------------------------------------------
# #         # RENAME NEW TABLE
# #         # --------------------------------------------------

# #         connection.execute(
# #             text("""
# #                 ALTER TABLE payments_new
# #                 RENAME TO payments
# #             """)
# #         )

# #         connection.commit()

# #         print(
# #             "Payment migration: "
# #             "participant_id is now nullable."
# #         )


# # ======================================================
# # STAFF DATABASE MIGRATION
# # ======================================================

# def migrate_staff_columns():
#     """Add Staff.position and allow profile fields to remain empty for admin-created placeholders."""
#     from sqlalchemy import text

#     with engine.begin() as connection:
#         columns = connection.execute(text("PRAGMA table_info(staff)")).fetchall()
#         if not columns:
#             return

#         names = {row[1] for row in columns}
#         if "position" not in names:
#             connection.execute(text("ALTER TABLE staff ADD COLUMN position VARCHAR(100)"))

#         # SQLite cannot directly change NOT NULL columns. Rebuild only when the
#         # existing staff table still has the old NOT NULL profile columns.
#         info = connection.execute(text("PRAGMA table_info(staff)")).fetchall()
#         notnull = {row[1]: row[3] for row in info}
#         needs_rebuild = any(notnull.get(col) == 1 for col in [
#             "sex", "birthday", "contact", "local_church", "sector"
#         ])

#         if not needs_rebuild:
#             return

#         connection.execute(text("PRAGMA foreign_keys=OFF"))
#         connection.execute(text("DROP TABLE IF EXISTS staff_new"))
#         connection.execute(text("""
#             CREATE TABLE staff_new (
#                 id INTEGER PRIMARY KEY,
#                 event_id INTEGER NOT NULL,
#                 fname VARCHAR(100) NOT NULL,
#                 mname VARCHAR(100),
#                 lname VARCHAR(100) NOT NULL,
#                 position VARCHAR(100) NOT NULL DEFAULT '',
#                 sex VARCHAR(20),
#                 birthday DATE,
#                 contact VARCHAR(20),
#                 local_church VARCHAR(150),
#                 sector VARCHAR(100),
#                 is_archived INTEGER DEFAULT 0,
#                 created_at DATETIME,
#                 updated_at DATETIME
#             )
#         """))
#         connection.execute(text("""
#             INSERT INTO staff_new
#             (id,event_id,fname,mname,lname,position,sex,birthday,contact,local_church,sector,is_archived,created_at,updated_at)
#             SELECT id,event_id,fname,mname,lname,COALESCE(position,''),sex,birthday,contact,local_church,sector,is_archived,created_at,updated_at
#             FROM staff
#         """))
#         connection.execute(text("DROP TABLE staff"))
#         connection.execute(text("ALTER TABLE staff_new RENAME TO staff"))
#         connection.execute(text("CREATE INDEX IF NOT EXISTS ix_staff_id ON staff (id)"))
#         connection.execute(text("PRAGMA foreign_keys=ON"))


# # ======================================================
# # CREATE TABLES
# # ======================================================

# Base.metadata.create_all(
#     bind=engine
# )


# # ======================================================
# # RUN STAFF MIGRATION
# # ======================================================

# migrate_staff_columns()


# # ======================================================
# # RUN PAYMENT MIGRATIONS
# # ======================================================

# # migrate_payment_columns()


# # ======================================================
# # MAKE STORE PAYMENTS POSSIBLE
# # ======================================================

# # migrate_payment_participant_nullable()

# migrate_store_item_columns()

# migrate_cash_sponsorship_columns()

# migrate_staff_table()



# ============================================================
# MIGRATE PAYMENT TABLE
# ADD STORE ORDER ID
# ============================================================

def migrate_payment_store_order_id():

    with engine.connect() as connection:

        result = connection.execute(
            text("PRAGMA table_info(payments)")
        )

        columns = [
            row[1]
            for row in result
        ]

        # ----------------------------------------------------
        # STORE ORDER ID
        # ----------------------------------------------------

        if "store_order_id" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE payments
                    ADD COLUMN store_order_id
                    VARCHAR(100)
                """)
            )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        connection.commit()


migrate_payment_store_order_id()






































# ======================================================
# PYDANTIC SCHEMAS
# ======================================================

class LoginSchema(BaseModel):

    username: str

    password: str
    

    
class AdminChangeCredentialSchema(BaseModel):

    username: str

    old_password: str

    new_username: str

    new_password: str
    
class LoginResponseSchema(BaseModel):

    message: str

    role: str

    redirect: str

    fullname: str

    username: str
    
class LogoutSchema(BaseModel):

    username: str
    
# ======================================================
# ADMIN SCHEMAS
# ======================================================

class AdminCreateRegistrationTeamSchema(BaseModel):

    admin_username: str

    fname: str

    mname: str

    lname: str


    birthday: datetime.date

    address: str

    email: EmailStr

    sex: str

    local_church: str

    contact_number: str

    sector: str

    username: str

    password: str

class AdminUpdateCredentialSchema(BaseModel):

    username: str

    old_password: str

    new_username: str

    new_password: str
    

# ======================================================
# EVENT SCHEMAS
# ======================================================

class EventCreateSchema(BaseModel):

    event_name: str

    registration_start: datetime.date

    registration_end: datetime.date

    kickoff_date: datetime.date

    wrapup_date: datetime.date
    

class EventUpdateSchema(BaseModel):

    event_name: str

    registration_start: datetime.date

    registration_end: datetime.date

    kickoff_date: datetime.date

    wrapup_date: datetime.date    



# ======================================================
# PARTICIPANT SCHEMAS
# ======================================================

class ParticipantCreateSchema(BaseModel):

    event_id: int

    participant_type: str

    fname: str
    mname: Optional[str] = None
    lname: str

    sex: str
    birthdate: datetime.date

    address: str
    contact_number: str
    emergency_contact: str

    email: EmailStr

    local_church: str
    sector: str
    

class ParticipantUpdateSchema(BaseModel):

    event_id:int
    
    participant_type: str

    fname:str

    mname:str=""

    lname:str

    sex:str

    birthdate:datetime.date

    address:str

    contact_number:str

    emergency_contact:str

    email:EmailStr

    local_church:str

    sector:str


# ======================================================
# QUESTIONNAIRE SCHEMA
# ======================================================

class QuestionnaireSchema(BaseModel):

    participant_id: int

    camp_attendance: str

    leadership_position: str

    church_involvement: str

    primary_strength: str

    ministry_skill: str

    salvation_assurance: str

    daily_devotion: str

    ministry_involvement: str

    sermon_notes: str

    small_group: str

    gospel_sharing: str

    temptation_response: str
    
# ======================================================
# COMPLETE ONLINE REGISTRATION SCHEMA
# ======================================================

class OnlineRegistrationSchema(BaseModel):

    # --------------------------------------------------
    # PARTICIPANT INFORMATION
    # --------------------------------------------------

    participant: ParticipantCreateSchema

    # --------------------------------------------------
    # QUESTIONNAIRE
    # --------------------------------------------------

    questionnaire: dict

    # --------------------------------------------------
    # AGREEMENTS
    # --------------------------------------------------

    rules_agreed: bool

    confidentiality_agreed: bool


# ======================================================
# EVENT RULES SCHEMA
# ======================================================

class EventRulesAgreementSchema(BaseModel):

    participant_id: int

    agreed: bool



# ======================================================
# STAFF REGISTRATION SCHEMA
# ======================================================

class StaffCreateSchema(BaseModel):

    event_id: int

    fname: str

    mname: Optional[str] = None

    lname: str

    position: str

    sex: Optional[str] = None

    birthday: Optional[datetime.date] = None

    contact_number: Optional[str] = None

    local_church: Optional[str] = None

    sector: Optional[str] = None


# ======================================================
# CHAPERONE REGISTRATION SCHEMA
# ======================================================

class ChaperoneCreateSchema(BaseModel):

    event_id: int

    fname: str

    mname: Optional[str] = None

    lname: str

    sex: str

    birthday: datetime.date

    contact_number: str

    local_church: str

    sector: str


class ChaperoneUpdateSchema(BaseModel):

    fname: str

    mname: Optional[str] = None

    lname: str

    sex: str

    birthday: datetime.date

    contact: str

    local_church: str

    sector: str


class StaffUpdateSchema(BaseModel):

    fname: str

    mname: Optional[str] = None

    lname: str

    position: str

    sex: Optional[str] = None

    birthday: Optional[datetime.date] = None

    contact_number: Optional[str] = None

    local_church: Optional[str] = None

    sector: Optional[str] = None








# ======================================================
# PAYMENT CREATE SCHEMA
# SUPPORTS SINGLE + BULK PARTICIPANTS
# ======================================================

class PaymentCreateSchema(BaseModel):

    # --------------------------------------------------
    # SINGLE PARTICIPANT
    # --------------------------------------------------

    participant_id: Optional[int] = None


    # --------------------------------------------------
    # BULK PARTICIPANTS
    # --------------------------------------------------

    participant_ids: Optional[List[int]] = None


    # --------------------------------------------------
    # ITEM SELECTION
    # --------------------------------------------------

    tshirt_selected: bool = False

    lanyard_selected: bool = False


    # --------------------------------------------------
    # OPTIONAL ALIASES
    #
    # Allows frontend to send:
    #
    # "tshirt"
    # "lanyard"
    #
    # in addition to:
    #
    # "tshirt_selected"
    # "lanyard_selected"
    # --------------------------------------------------

    tshirt: Optional[bool] = None

    lanyard: Optional[bool] = None


    # --------------------------------------------------
    # T-SHIRT SIZE
    # --------------------------------------------------

    tshirt_size: Optional[str] = None


    # --------------------------------------------------
    # BULK FLAG
    # --------------------------------------------------

    bulk: bool = False
    
    
    
    
    
    
    
    

# ============================================================
# CASH SPONSORSHIP SCHEMA
# ============================================================

class CashSponsorshipCreate(BaseModel):

    sponsor_name: str = Field(
        min_length=2,
        max_length=255
    )

    local_church: str = Field(
        min_length=2,
        max_length=255
    )

    contact: str = Field(
        min_length=7,
        max_length=50
    )

    sector: str

    email: EmailStr

    selected_tier: str

    donation_amount: float










# ============================================================
# ITEM SPONSORSHIP SCHEMA
# ============================================================

class ItemSponsorshipItem(BaseModel):

    item_id: int

    item_name: Optional[str] = None

    quantity: int


class ItemSponsorshipCreate(BaseModel):

    sponsor_name: str

    local_church: str

    visiting_church: Optional[str] = None

    contact: Optional[str] = None

    sector: str

    email: Optional[str] = None

    items: List[ItemSponsorshipItem]









# ============================================================
# CREATE SPONSORSHIP ITEM
# ============================================================

class SponsorshipItemCreate(BaseModel):

    item_name: str

    description: Optional[str] = None

    quantity: int = Field(
        gt=0
    )

    unit: str = "piece"


@app.post("/sponsorship/items")
def create_sponsorship_item(
    data: SponsorshipItemCreate,
    db: Session = Depends(get_db)
):

    item = SponsorshipItem(

        item_name=
            data.item_name.strip(),

        description=
            data.description,

        total_quantity=
            data.quantity,

        remaining_quantity=
            data.quantity,

        unit=
            data.unit.strip(),

        is_active=True

    )

    db.add(item)

    db.commit()

    db.refresh(item)

    return {

        "success": True,

        "message":
            "Sponsorship item created.",

        "item": {

            "id": item.id,

            "item_name":
                item.item_name,

            "total_quantity":
                item.total_quantity,

            "remaining_quantity":
                item.remaining_quantity,

            "unit":
                item.unit

        }

    }










# ======================================================
# CREATE SPONSORSHIP ITEM SCHEMA
# ======================================================

class SponsorshipItemCreateSchema(BaseModel):

    item_name: str
    description: Optional[str] = None
    unit: str
    required_quantity: int











# ============================================================
# STORE ITEM CREATE SCHEMA
# ============================================================

class StoreItemCreateSchema(BaseModel):
    item_name: str
    description: str | None = None
    category: str
    quantity: int
    price: float
    image_url: str | None = None
    sizes: list[str] | None = None


class StoreItemUpdateSchema(BaseModel):
    item_name: str
    description: str | None = None
    category: str
    quantity: int
    price: float
    image_url: str | None = None
    sizes: list[str] | None = None











# ============================================================
# STORE CART ITEM
# ============================================================

class StorePurchaseItemSchema(BaseModel):

    store_item_id: int

    quantity: int

    size: Optional[str] = None








# ============================================================
# STORE PURCHASE
# ============================================================

class StorePurchaseSchema(BaseModel):

    customer_name: str

    customer_contact: str

    customer_email: EmailStr

    items: List[StorePurchaseItemSchema]








# ============================================================
# CONTACT RECEIVER
# ============================================================

CONTACT_RECEIVER_EMAIL = (
    "matulacarianjay1@gmail.com"
)






# ==========================================================
# CONTACT REQUEST MODEL
# ==========================================================

class ContactRequest(BaseModel):

    name: str
    email: EmailStr
    subject: str
    message: str






# ==========================================================
# EMAIL CONFIGURATION
# ==========================================================

CONTACT_RECEIVER = (
    "matulacarianjay1@gmail.com"
)







# ==========================================================
# GMAIL API EMAIL CONFIGURATION
# ==========================================================

# The authorized Gmail account is the sender.
# No custom domain and no Gmail App Password are required.

CONTACT_RECEIVER_EMAIL = (
    os.getenv("CONTACT_RECEIVER_EMAIL")
    or GMAIL_SENDER_EMAIL
)


def send_gmail_smtp(
    recipient_email,
    subject,
    text_body=None,
    html_body=None,
    reply_to=None
):
    """
    Backward-compatible function name.

    This no longer uses SMTP. It sends through the Gmail API.
    """

    return send_gmail(
        recipient_email,
        subject,
        html_body=html_body,
        plain_body=text_body,
        reply_to=reply_to
    )







# ==========================================================
# ASYNC GMAIL SMTP SENDER
# ==========================================================


async def send_gmail_smtp_async(
    recipient_email,
    subject,
    text_body=None,
    html_body=None,
    reply_to=None
):
    """
    Backward-compatible async function name.

    This no longer uses SMTP. It sends through the Gmail API.
    """

    return await send_gmail_async(
        recipient_email,
        subject,
        html_body=html_body,
        plain_body=text_body,
        reply_to=reply_to
    )








# ==========================================================
# SEND CONTACT EMAIL
# ==========================================================

def send_contact_email(
    contact: ContactRequest
):

    # ------------------------------------------------------
    # Check Gmail configuration
    # ------------------------------------------------------

    if not GMAIL_SENDER_EMAIL:
        raise RuntimeError(
            "GMAIL_SENDER_EMAIL is not configured."
        )

    if not CONTACT_RECEIVER_EMAIL:
        raise RuntimeError(
            "CONTACT_RECEIVER_EMAIL is not configured."
        )


    # ------------------------------------------------------
    # Clean user input
    # ------------------------------------------------------

    name = contact.name.strip()

    sender_email = contact.email.strip()

    subject = contact.subject.strip()

    message = contact.message.strip()


    # ------------------------------------------------------
    # Prevent header injection
    # ------------------------------------------------------

    subject = (
        subject
        .replace("\r", " ")
        .replace("\n", " ")
    )

    name = (
        name
        .replace("\r", " ")
        .replace("\n", " ")
    )


    # ------------------------------------------------------
    # Create HTML email
    # ------------------------------------------------------

    email_html = f"""
    <html>

        <body>

            <h2>Contact Us Message</h2>

            <hr>

            <p>
                <strong>Name:</strong>
                {name}
            </p>

            <p>
                <strong>Email:</strong>
                {sender_email}
            </p>

            <p>
                <strong>Subject:</strong>
                {subject}
            </p>

            <p>
                <strong>Message:</strong>
            </p>

            <p>
                {message}
            </p>

            <hr>

            <p>
                This message was submitted through the
                CYF Registration System Contact Us form.
            </p>

        </body>

    </html>
    """


    # ------------------------------------------------------
    # Send email through Gmail SMTP
    # ------------------------------------------------------

    # ------------------------------------------------------
    # SEND THROUGH GMAIL SMTP
    # ------------------------------------------------------

    response = send_gmail_smtp(
        CONTACT_RECEIVER_EMAIL,
        f"Contact Us Message - {subject}",
        text_body=(
            f"Name: {name}\n"
            f"Email: {sender_email}\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{message}\n\n"
            "This message was submitted through the "
            "CYF Registration System Contact Us form."
        ),
        html_body=email_html,
        reply_to=sender_email
    )


    # ------------------------------------------------------
    # Log successful email
    # ------------------------------------------------------

    print(
        "CONTACT EMAIL SENT SUCCESSFULLY:"
    )

    print(
        response
    )


    return response











# ==========================================================
# CONTACT API
# ==========================================================

@app.post("/contact")
async def contact_us(
    contact: ContactRequest
):

    try:

        send_contact_email(
            contact
        )

        return {
            "success": True,
            "message": (
                "Your message has been sent successfully."
            )
        }


    except Exception as error:

        print(
            "CONTACT EMAIL ERROR:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to send your message. "
                "Please try again later."
            )
        )



















# ============================================================
# ITEM SPONSORSHIP RESPONSE
# ============================================================

class ItemSponsorshipResponse(BaseModel):

    id: int

    sponsor_name: str

    local_church: str

    visiting_church: Optional[str] = None

    contact: Optional[str] = None

    sector: Optional[str] = None

    email: Optional[str] = None

    item_id: int

    item_name: str

    quantity: int

    status: str

    created_at: datetime.datetime

    class Config:
        from_attributes = True











# ============================================================
# CASH SPONSORSHIP RESPONSE
# ============================================================

class CashSponsorshipResponse(BaseModel):

    id: int

    sponsor_name: str

    local_church: str

    contact: Optional[str] = None

    sector: Optional[str] = None

    email: Optional[str] = None

    selected_tier: str

    donation_amount: int

    payment_status: str

    paymongo_link_id: Optional[str] = None

    paymongo_reference: Optional[str] = None

    payment_url: Optional[str] = None

    created_at: datetime.datetime

    paid_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):

    id: int

    participant_id: Optional[int] = None

    payment_type: str

    store_item_id: Optional[int] = None
    store_quantity: Optional[int] = None
    store_size: Optional[str] = None

    amount: int
    currency: str
    status: str

    tshirt_selected: int = 0
    lanyard_selected: int = 0
    tshirt_size: Optional[str] = None

    sponsorship_tier: Optional[str] = None
    sponsor_id: Optional[int] = None

    paymongo_link_id: Optional[str] = None
    paymongo_payment_id: Optional[str] = None
    paymongo_reference: Optional[str] = None
    checkout_url: Optional[str] = None

    description: Optional[str] = None

    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_email: Optional[str] = None

    created_at: Optional[datetime.datetime] = None
    paid_at: Optional[datetime.datetime] = None

    # ==========================================
    # DISPLAY NAME
    # ==========================================

    participant_name: Optional[str] = None

    class Config:
        from_attributes = True
 
 
 
 
 
 
 
        
        
# ============================================================
# REGISTRATION ITEM SCHEMAS
# ============================================================

class RegistrationItemCreate(BaseModel):

    item_name: str

    price: int


class RegistrationItemUpdate(BaseModel):

    item_name: Optional[str] = None

    price: Optional[int] = None

    is_active: Optional[bool] = None


class RegistrationItemResponse(BaseModel):

    id: int

    item_name: str

    price: int

    is_active: bool

    created_at: datetime.datetime

    updated_at: datetime.datetime

    class Config:
        from_attributes = True        
        
 
 
 
 
 
 
 
        
        
# ============================================================
# SCHEMAS
# ============================================================

class CashDonationTotalCreateSchema(BaseModel):

    amount: int


class CashDonationTotalUpdateSchema(BaseModel):

    amount: int        
        
        
        
        
        
        
        
        
        
















    

# ======================================================
# HELPER FUNCTIONS
# ======================================================

def verify_admin(db: Session, username: str):

    admin = db.query(User).filter(

        User.username == username,

        User.role == "Admin"

    ).first()

    if not admin:

        raise HTTPException(

            status_code=403,

            detail="Administrator account not found."

        )

    return admin



# ======================================================
# EVENT HELPER FUNCTIONS
# ======================================================

def get_registration_phase(event):

    today = datetime.date.today()

    if today < event.registration_start:

        return "Registration Closed"

    elif event.registration_start <= today <= event.registration_end:

        return "Early-bird"

    elif event.registration_end < today <= event.wrapup_date:

        return "Walk-in"

    else:

        return "Event Closed"


    
# ======================================================
# DEFAULT ADMIN
# ======================================================

def create_default_admin():

    db = SessionLocal()

    admin = db.query(User).filter(
        User.role == "Admin"
    ).first()

    if admin:

        db.close()

        return

    admin = User(

        fname="System",

        mname="",

        lname="Administrator",

        age=0,

        birthday=datetime.date.today(),

        address="",

        email="admin@system.local",

        sex="",

        local_church="",

        contact_number="",

        sector="Administrator",

        username="admin",

        password=hash_password("admin123"),

        role="Admin"
    )

    db.add(admin)

    db.commit()

    db.close()

    print("Default Admin Created")
    

# ======================================================
# PARTICIPANT HELPER FUNCTIONS
# ======================================================

def registration_duplicate_validation(

    db: Session,

    event_id: int,

    fname: str,

    mname: str,

    lname: str,

    birthdate: datetime.date

):

    participant = db.query(Participant).filter(

        Participant.event_id == event_id,

        Participant.fname == fname,

        Participant.mname == mname,

        Participant.lname == lname,

        Participant.birthdate == birthdate,

        Participant.is_archived == 0

    ).first()

    return participant



def registration_phase_validation(event):

    today = datetime.date.today()

    if today <= event.registration_end:

        return "Early-bird"

    return "Walk-in"




def registration_number_generator(

    db: Session,

    event

):

    year = event.kickoff_date.year

    if event.event_name == "Summer Youth Camp":

        prefix = "SYC"

    else:

        prefix = "YBC"

    count = db.query(Participant).filter(

        Participant.event_id == event.id

    ).count()

    return f"{prefix}-{year}-{count + 1:04d}"    


# ======================================================
# QUESTIONNAIRE HELPER
# ======================================================

def questionnaire_duplicate_validation(

    db: Session,

    participant_id: int

):

    return db.query(Questionnaire).filter(

        Questionnaire.participant_id == participant_id

    ).first()


def influence_score_calculator(questionnaire):

    score = 0

    # Camp Attendance

    if questionnaire.camp_attendance == "3 or more camps":

        score += 3

    elif questionnaire.camp_attendance == "1 to 2 camps":

        score += 2

    else:

        score += 1

    # Leadership

    if questionnaire.leadership_position == "Yes, active leader":

        score += 3

    elif questionnaire.leadership_position == "No, but I help out often":

        score += 2

    else:

        score += 1

    # Church Involvement

    if questionnaire.church_involvement.startswith("Highly active"):

        score += 3

    elif questionnaire.church_involvement.startswith("Fairly regular"):

        score += 2

    else:

        score += 1

    return score


def spiritual_score_calculator(questionnaire):

    score = 0

    questions = [

        questionnaire.salvation_assurance,

        questionnaire.daily_devotion,

        questionnaire.ministry_involvement,

        questionnaire.sermon_notes,

        questionnaire.small_group,

        questionnaire.gospel_sharing,

        questionnaire.temptation_response

    ]

    for answer in questions:

        if answer.startswith("Yes") or answer.startswith("Very"):

            score += 2

        elif answer.startswith("Sometimes") or answer.startswith("Somewhat") or answer.startswith("No, but") or answer.startswith("I believe") or answer.startswith("I try"):

            score += 1

        else:

            score += 0

    return score


def creative_identifier(questionnaire):

    creative_skills = [

        "Music / Singing",

        "Arts / Dance / Media Production"

    ]

    if questionnaire.ministry_skill in creative_skills:

        return "Creative"

    return "Non-Creative"


def tier_assignment(

    influence_score,

    spiritual_score,

    creative_status

):

    if spiritual_score >= 11 and influence_score >= 7:

        return "Tier 1 - Anchor Leaders"

    if creative_status == "Creative":

        return "Tier 2 - Culture Catalysts"

    if 7 <= spiritual_score <= 10:

        return "Tier 3 - The Steady Core"

    if 3 <= spiritual_score <= 6:

        return "Tier 4 - The Fresh Soil"

    return "Tier 5 - The Wildcards"


# ======================================================
# RULES VALIDATION
# ======================================================

def registration_rules_validation(

    db: Session,

    participant_id: int

):

    return db.query(EventRulesAgreement).filter(

        EventRulesAgreement.participant_id == participant_id,

        EventRulesAgreement.agreed == 1

    ).first()


def calculate_registration_age(

    birthdate: datetime.date

):

    today = datetime.date.today()

    age = today.year - birthdate.year

    if (

        today.month,

        today.day

    ) < (

        birthdate.month,

        birthdate.day

    ):

        age -= 1

    return age

# ======================================================
# SEND PAYMENT EMAIL
# ======================================================

async def send_payment_email(
    participant,
    event,
    payment
):

    # --------------------------------------------------
    # CHECK EMAIL
    # --------------------------------------------------

    if not participant.email:

        print(
            f"WARNING: Participant "
            f"{participant.id} has no email address."
        )

        return False

    # --------------------------------------------------
    # FORMAT INFORMATION
    # --------------------------------------------------

    fullname = (
        f"{participant.fname} "
        f"{participant.mname or ''} "
        f"{participant.lname}"
    ).strip()

    amount_display = (
        f"₱{payment.amount / 100:,.2f}"
    )

    # --------------------------------------------------
    # EMAIL SUBJECT
    # --------------------------------------------------

    subject = (
        f"Payment Instructions - "
        f"{event.event_name}"
    )

    # --------------------------------------------------
    # EMAIL HTML
    # --------------------------------------------------

    html = f"""
    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width, initial-scale=1.0">

        <title>Payment Instructions</title>

    </head>

    <body style="
        margin:0;
        padding:0;
        background:#f5f5f5;
        font-family:Arial,Helvetica,sans-serif;
    ">

        <div style="
            max-width:650px;
            margin:30px auto;
            background:white;
            border-radius:12px;
            overflow:hidden;
            box-shadow:0 4px 20px rgba(0,0,0,0.08);
        ">

            <!-- HEADER -->

            <div style="
                background:#9d0b0b;
                color:white;
                padding:30px;
                text-align:center;
            ">

                <h1 style="
                    margin:0;
                    font-size:28px;
                ">
                    Event Registration
                </h1>

                <p style="
                    margin:8px 0 0;
                    color:#f5d27a;
                    font-size:16px;
                ">
                    Payment Instructions
                </p>

            </div>


            <!-- CONTENT -->

            <div style="padding:30px;">

                <h2 style="
                    color:#9d0b0b;
                    margin-top:0;
                ">
                    Hello {fullname}!
                </h2>

                <p style="
                    color:#444;
                    line-height:1.7;
                ">
                    Thank you for registering for
                    <strong>{event.event_name}</strong>.
                </p>

                <p style="
                    color:#444;
                    line-height:1.7;
                ">
                    Your registration has been successfully
                    recorded. Your payment is currently
                    <strong>Pending</strong>.
                </p>


                <!-- REGISTRATION DETAILS -->

                <div style="
                    background:#fff8e5;
                    border-left:5px solid #d4af37;
                    padding:20px;
                    margin:25px 0;
                    border-radius:6px;
                ">

                    <h3 style="
                        margin-top:0;
                        color:#9d0b0b;
                    ">
                        Registration Details
                    </h3>

                    <p>
                        <strong>Registration Number:</strong><br>
                        {participant.registration_number}
                    </p>

                    <p>
                        <strong>Participant:</strong><br>
                        {fullname}
                    </p>

                    <p>
                        <strong>Event:</strong><br>
                        {event.event_name}
                    </p>

                    <p>
                        <strong>Amount Due:</strong><br>

                        <span style="
                            font-size:24px;
                            font-weight:bold;
                            color:#9d0b0b;
                        ">
                            {amount_display}
                        </span>
                    </p>

                </div>


                <!-- PAY BUTTON -->

                <div style="
                    text-align:center;
                    margin:35px 0;
                ">

                    <a href="{payment.checkout_url}"
                       style="
                            display:inline-block;
                            background:#9d0b0b;
                            color:white;
                            text-decoration:none;
                            padding:15px 30px;
                            border-radius:8px;
                            font-weight:bold;
                            font-size:16px;
                       ">

                        PAY NOW

                    </a>

                </div>


                <p style="
                    color:#666;
                    font-size:14px;
                    line-height:1.6;
                ">

                    Please click the
                    <strong>PAY NOW</strong>
                    button above to continue to the
                    secure PayMongo checkout page.

                </p>


                <!-- IMPORTANT -->

                <div style="
                    background:#f8f8f8;
                    padding:15px;
                    border-radius:6px;
                    margin-top:25px;
                ">

                    <p style="
                        margin:0;
                        font-size:13px;
                        color:#666;
                    ">

                        <strong>Important:</strong>
                        Your registration will remain pending
                        until the payment has been successfully
                        confirmed.

                    </p>

                </div>

            </div>


            <!-- FOOTER -->

            <div style="
                background:#9d0b0b;
                color:white;
                text-align:center;
                padding:20px;
                font-size:13px;
            ">

                <p style="margin:0;">
                    Event Registration System
                </p>

                <p style="
                    margin:8px 0 0;
                    color:#f5d27a;
                ">
                    Please keep your registration number
                    for future reference.
                </p>

            </div>

        </div>

    </body>

    </html>
    """
    # --------------------------------------------------
    # SEND THROUGH GMAIL API
    # --------------------------------------------------

    try:

        await send_gmail_async(
            participant.email,
            subject,
            html_body=html
        )

        print(
            f"Payment email sent to "
            f"{participant.email}"
        )

        return True

    except Exception as e:

        print(
            f"ERROR sending payment email: {e}"
        )

        return False

# ======================================================
# PAYMENT CONFIRMATION EMAIL
# ======================================================

async def send_payment_confirmation_email(
    participant,
    payment
):

    if not participant.email:

        print(
            "Participant has no email address."
        )

        return

    fullname = (
        f"{participant.fname} "
        f"{participant.mname or ''} "
        f"{participant.lname}"
    ).replace("  ", " ").strip()

    items = []

    if payment.tshirt_selected:

        items.append(
            "T-shirt - ₱350.00"
        )

    if payment.lanyard_selected:

        items.append(
            "Lanyard - ₱90.00"
        )

    item_html = ""

    for item in items:

        item_html += f"""
        <li style="
            margin-bottom:8px;
            color:#444;
        ">
            {item}
        </li>
        """

    amount_display = (
        f"₱{payment.amount / 100:,.2f}"
    )

    html_body = f"""
    <!DOCTYPE html>

    <html>

    <body style="
        margin:0;
        padding:0;
        background:#f5f5f5;
        font-family:Arial,sans-serif;
    ">

        <div style="
            max-width:650px;
            margin:30px auto;
            background:#ffffff;
            border-radius:12px;
            overflow:hidden;
        ">

            <div style="
                background:#9d0b0b;
                padding:30px;
                text-align:center;
                color:white;
            ">

                <h1 style="margin:0;">
                    Payment Confirmed
                </h1>

                <p style="
                    color:#f5d27a;
                    margin-bottom:0;
                ">
                    CYF Registration System
                </p>

            </div>

            <div style="
                padding:30px;
            ">

                <h2 style="
                    color:#9d0b0b;
                ">
                    Thank you, {fullname}!
                </h2>

                <p style="
                    color:#444;
                    line-height:1.7;
                ">
                    Your payment has been successfully
                    confirmed.
                </p>

                <div style="
                    background:#fff8e5;
                    border-left:5px solid #d4af37;
                    padding:20px;
                    border-radius:6px;
                    margin:25px 0;
                ">

                    <p>
                        <strong>
                            Registration Number
                        </strong>
                        <br>
                        {participant.registration_number}
                    </p>

                    <p>
                        <strong>
                            Amount Paid
                        </strong>
                        <br>

                        <span style="
                            font-size:24px;
                            color:#9d0b0b;
                            font-weight:bold;
                        ">
                            {amount_display}
                        </span>
                    </p>

                    <p>
                        <strong>
                            PayMongo Reference
                        </strong>
                        <br>
                        {payment.paymongo_reference or "N/A"}
                    </p>

                </div>

                <h3 style="
                    color:#9d0b0b;
                ">
                    Items Paid
                </h3>

                <ul>
                    {item_html}
                </ul>

                <h3 style="
                    color:#9d0b0b;
                    margin-top:30px;
                ">
                    Item Status
                </h3>

                <table style="
                    width:100%;
                    border-collapse:collapse;
                ">

                    <tr>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                        ">
                            T-shirt
                        </td>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            color:#16803c;
                        ">
                            {participant.tshirt_status}
                        </td>

                    </tr>

                    <tr>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                        ">
                            Lanyard
                        </td>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            color:#16803c;
                        ">
                            {participant.lanyard_status}
                        </td>

                    </tr>

                </table>

                <p style="
                    margin-top:30px;
                    color:#666;
                    line-height:1.6;
                ">
                    Please keep this email for your records.
                </p>

            </div>

            <div style="
                background:#9d0b0b;
                color:white;
                text-align:center;
                padding:20px;
                font-size:13px;
            ">

                CYF Registration System

            </div>

        </div>

    </body>

    </html>
    """
    # --------------------------------------------------
    # SEND THROUGH GMAIL API
    # --------------------------------------------------

    subject = (
        "Payment Confirmed - "
        f"{participant.registration_number}"
    )

    await send_gmail_async(
        participant.email,
        subject,
        html_body=html_body
    )

    print(
        f"Payment confirmation sent to "
        f"{participant.email}"
    )











# ============================================================
# ITEM SPONSORSHIP CONFIRMATION EMAIL
# ============================================================

async def send_item_sponsorship_confirmation_email(
    donation
):

    try:

        # ----------------------------------------------------
        # GET EMAIL
        # ----------------------------------------------------

        recipient_email = str(
            donation.email
        ).strip()

        if not recipient_email:

            print(
                "Item sponsorship email failed: "
                "Sponsor email is empty."
            )

            return False


        # ----------------------------------------------------
        # SPONSOR INFORMATION
        # ----------------------------------------------------

        sponsor_name = (
            donation.sponsor_name
            or "Sponsor"
        )

        item_name = (
            donation.item_name
            or "Item"
        )

        quantity = (
            donation.quantity
            or 0
        )

        unit = (
            getattr(
                donation,
                "unit",
                None
            )
            or "unit"
        )


        # ----------------------------------------------------
        # EMAIL SUBJECT
        # ----------------------------------------------------

        subject = (
            "Item Donation Sponsorship Confirmation "
            "| CYF Registration System"
        )


        # ----------------------------------------------------
        # EMAIL MESSAGE
        # ----------------------------------------------------

        body = f"""
Dear {sponsor_name},

Thank you for your generous support of the CYF ministry.

We are pleased to confirm that your item donation sponsorship
has been successfully recorded.

DONATION DETAILS
----------------------------------------

Sponsor Name:
{sponsor_name}

Local Church:
{getattr(donation, "local_church", "N/A")}

Contact Number:
{getattr(donation, "contact", "N/A")}

Sector:
{getattr(donation, "sector", "N/A")}

Item Donated:
{item_name}

Quantity:
{quantity} {unit}

Donation Status:
Confirmed

----------------------------------------

DELIVERY INFORMATION

Please deliver your donated item to:

Butuan Grace Baptist Church

You may also contact:

Pastor Edward Deligero
0911 252 3584

----------------------------------------

Thank you again for your generosity and willingness
to support CYF events.

Your contribution will help provide the necessary
resources and materials for our youth ministry activities.

We sincerely appreciate your support.

God bless you!

CYF Registration System
"""


        # ----------------------------------------------------
        # SEND THROUGH GMAIL SMTP
        # ----------------------------------------------------

        # ----------------------------------------------------
        # SEND THROUGH GMAIL SMTP
        # ----------------------------------------------------

        response = await send_gmail_smtp_async(
            recipient_email,
            subject,
            text_body=body
        )


        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        print(
            "Item sponsorship confirmation email sent to:",
            recipient_email
        )

        print(
            "Gmail SMTP response:",
            response
        )

        return True


    except Exception as e:

        print(
            "Item sponsorship confirmation email failed:",
            repr(e)
        )

        return False














# ============================================================
# INITIALIZE SPONSORSHIP TIERS
# ============================================================

def initialize_sponsorship_tiers():

    db = SessionLocal()

    try:

        existing = db.query(
            SponsorshipPackage
        ).count()

        if existing > 0:
            return

        tiers = [

            SponsorshipPackage(
                tier="1st (Bronze) Tier",
                minimum_amount=0,
                maximum_amount=999,
                description="Donation below ₱1,000"
            ),

            SponsorshipPackage(
                tier="2nd (Silver) Tier",
                minimum_amount=1000,
                maximum_amount=1999,
                description="Donation from ₱1,000 to below ₱2,000"
            ),

            SponsorshipPackage(
                tier="3rd (Gold) Tier",
                minimum_amount=2000,
                maximum_amount=2999,
                description="Donation from ₱2,000 to below ₱3,000"
            ),

            SponsorshipPackage(
                tier="4th (Diamond) Tier",
                minimum_amount=3000,
                maximum_amount=None,
                description="Donation of ₱3,000 and above"
            )

        ]

        db.add_all(tiers)

        db.commit()

    finally:

        db.close()




# ======================================================
# FINDING SPONSOR - PARTICIPANT EMAIL
# ======================================================
#
# Sent automatically when a cash donation successfully
# sponsors a Finding Sponsor participant.
#
# The email is sent to the PARTICIPANT.
#
# It informs them that:
#
# - Registration is complete
# - Sponsor review is approved
# - T-shirt is paid
# - Lanyard is paid
#
# ======================================================

async def send_sponsored_participant_confirmation_email(
    participant,
    sponsored_amount
):

    if not participant.email:

        print(
            "Finding Sponsor participant has no email address."
        )

        return False


    # ==================================================
    # FULL NAME
    # ==================================================

    fullname = (
        f"{participant.fname} "
        f"{participant.mname or ''} "
        f"{participant.lname}"
    ).replace(
        "  ",
        " "
    ).strip()


    # ==================================================
    # SPONSORED AMOUNT
    # ==================================================

    try:

        sponsored_amount = int(
            sponsored_amount or 0
        )

    except (
        ValueError,
        TypeError
    ):

        sponsored_amount = 0


    sponsored_amount_display = (
        f"₱{sponsored_amount:,.2f}"
    )


    # ==================================================
    # HTML EMAIL
    # ==================================================

    html_body = f"""
    <!DOCTYPE html>

    <html>

    <body style="
        margin:0;
        padding:0;
        background:#f5f5f5;
        font-family:Arial,sans-serif;
    ">

        <div style="
            max-width:650px;
            margin:30px auto;
            background:#ffffff;
            border-radius:12px;
            overflow:hidden;
        ">

            <!-- HEADER -->

            <div style="
                background:#9d0b0b;
                padding:30px;
                text-align:center;
                color:white;
            ">

                <h1 style="
                    margin:0;
                    font-size:28px;
                ">
                    Registration Completed
                </h1>

                <p style="
                    color:#f5d27a;
                    margin-bottom:0;
                    font-size:15px;
                ">
                    CYF Registration System
                </p>

            </div>


            <!-- CONTENT -->

            <div style="
                padding:30px;
            ">

                <h2 style="
                    color:#9d0b0b;
                ">
                    Congratulations, {fullname}!
                </h2>


                <p style="
                    color:#444;
                    line-height:1.7;
                ">

                    We are pleased to inform you that your
                    registration has been successfully completed
                    through our sponsorship program.

                </p>


                <!-- SUCCESS MESSAGE -->

                <div style="
                    background:#eefaf1;
                    border-left:5px solid #16803c;
                    padding:20px;
                    border-radius:6px;
                    margin:25px 0;
                ">

                    <h3 style="
                        margin-top:0;
                        color:#16803c;
                    ">
                        Sponsorship Approved
                    </h3>

                    <p style="
                        color:#444;
                        line-height:1.6;
                        margin-bottom:0;
                    ">

                        Your sponsor review has been approved,
                        and the sponsorship has been successfully
                        applied to your registration.

                    </p>

                </div>


                <!-- REGISTRATION DETAILS -->

                <h3 style="
                    color:#9d0b0b;
                    margin-top:30px;
                ">
                    Registration Details
                </h3>


                <table style="
                    width:100%;
                    border-collapse:collapse;
                ">

                    <tr>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            color:#555;
                        ">
                            Registration Number
                        </td>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            color:#9d0b0b;
                        ">
                            {participant.registration_number}
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            color:#555;
                        ">
                            Registration Status
                        </td>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            color:#16803c;
                        ">
                            COMPLETE
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            color:#555;
                        ">
                            Sponsor Review
                        </td>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            color:#16803c;
                        ">
                            APPROVED
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            color:#555;
                        ">
                            Sponsored Amount
                        </td>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            color:#9d0b0b;
                        ">
                            {sponsored_amount_display}
                        </td>

                    </tr>

                </table>


                <!-- MERCHANDISE -->

                <h3 style="
                    color:#9d0b0b;
                    margin-top:30px;
                ">
                    Merchandise Status
                </h3>


                <table style="
                    width:100%;
                    border-collapse:collapse;
                ">

                    <tr>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                        ">
                            T-shirt
                        </td>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            color:#16803c;
                        ">
                            PAID
                        </td>

                    </tr>


                    <tr>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                        ">
                            Lanyard
                        </td>

                        <td style="
                            padding:12px;
                            border-bottom:1px solid #ddd;
                            text-align:right;
                            font-weight:bold;
                            color:#16803c;
                        ">
                            PAID
                        </td>

                    </tr>

                </table>


                <!-- IMPORTANT NOTICE -->

                <div style="
                    background:#fff8e5;
                    border-left:5px solid #d4af37;
                    padding:20px;
                    border-radius:6px;
                    margin:30px 0;
                ">

                    <p style="
                        margin:0;
                        color:#444;
                        line-height:1.7;
                    ">

                        <strong>
                            No additional payment is required
                        </strong>
                        for the sponsored T-shirt and lanyard.

                        Your registration has already been
                        completed through sponsorship.

                    </p>

                </div>


                <p style="
                    color:#666;
                    line-height:1.7;
                ">

                    Please keep this email for your records.
                    We look forward to seeing you at the event!

                </p>

            </div>


            <!-- FOOTER -->

            <div style="
                background:#9d0b0b;
                color:white;
                text-align:center;
                padding:20px;
                font-size:13px;
            ">

                CYF Registration System

            </div>

        </div>

    </body>

    </html>
    """
    # ==================================================
    # SEND THROUGH GMAIL API
    # ==================================================

    subject = (
        "Registration Completed Through Sponsorship - "
        f"{participant.registration_number}"
    )

    await send_gmail_async(
        participant.email,
        subject,
        html_body=html_body
    )

    print(
        "Finding Sponsor participant email sent to",
        participant.email
    )

    return True




# ============================================================
# DETERMINE TIER
# ============================================================

def determine_sponsorship_tier(
    amount: Decimal
):

    if amount < Decimal("1000"):
        return "1st (Bronze) Tier"

    elif amount < Decimal("2000"):
        return "2nd (Silver) Tier"

    elif amount < Decimal("3000"):
        return "3rd (Gold) Tier"

    else:
        return "4th (Diamond) Tier"












# ======================================================
# SEND SPONSOR CONFIRMATION EMAIL
# ======================================================

async def send_sponsor_confirmation_email(
    sponsor,
    payment
):

    try:

        sponsor_name = (
            sponsor.fname
            or "Sponsor"
        )

        sponsor_email = (
            sponsor.email
            or ""
        ).strip()

        if not sponsor_email:

            print(
                "Sponsor confirmation email failed: "
                "Sponsor email is empty."
            )

            return False

        tier = (
            payment.sponsorship_tier
            or "Sponsorship"
        )

        amount = (
            payment.amount / 100
        )

        subject = (
            "CYF Sponsorship Donation Confirmation"
        )

        body = f"""
Dear {sponsor_name},

Thank you for your generous donation.

SPONSORSHIP DETAILS
----------------------------------------

Sponsorship Tier:
{tier}

Donation Amount:
₱{amount:,.2f}

Payment Status:
Successfully Received

----------------------------------------

Your sponsorship payment has been successfully received.

We sincerely appreciate your support.

Thank you,

CYF Registration Team
CYF Registration System
"""

        # --------------------------------------------------
        # SEND THROUGH GMAIL SMTP
        # --------------------------------------------------

        # --------------------------------------------------
        # SEND THROUGH GMAIL SMTP
        # --------------------------------------------------

        response = await send_gmail_smtp_async(
            sponsor_email,
            subject,
            text_body=body
        )

        print(
            "Sponsor confirmation email sent to:",
            sponsor_email
        )

        print(
            "Gmail SMTP response:",
            response
        )

        return True

    except Exception as e:

        print(
            "Sponsor confirmation email failed:",
            repr(e)
        )

        return False












# ============================================================
# PARTICIPANT PAYMENT CONFIRMATION EMAIL
# ============================================================

async def send_participant_payment_confirmation_email(
    participant,
    payment
):

    try:

        # ----------------------------------------------------
        # GET EMAIL
        # ----------------------------------------------------

        recipient_email = getattr(
            participant,
            "email",
            None
        )

        if not recipient_email:

            print(
                "Participant confirmation email failed: "
                "Participant email is empty."
            )

            return False

        recipient_email = str(
            recipient_email
        ).strip()

        # ----------------------------------------------------
        # PARTICIPANT NAME
        # ----------------------------------------------------

        fname = (
            getattr(
                participant,
                "fname",
                ""
            )
            or ""
        )

        lname = (
            getattr(
                participant,
                "lname",
                ""
            )
            or ""
        )

        participant_name = (
            f"{fname} {lname}"
        ).strip()

        if not participant_name:

            participant_name = "Participant"

        # ----------------------------------------------------
        # PAYMENT AMOUNT
        # ----------------------------------------------------

        try:

            amount = (
                Decimal(
                    str(
                        getattr(
                            payment,
                            "amount",
                            0
                        )
                    )
                )
                / Decimal("100")
            )

        except Exception:

            amount = Decimal("0.00")

        # ----------------------------------------------------
        # ITEMS
        # ----------------------------------------------------

        items = []

        if getattr(
            payment,
            "tshirt_selected",
            0
        ):

            tshirt_size = getattr(
                payment,
                "tshirt_size",
                None
            )

            if tshirt_size:

                items.append(
                    f"T-Shirt ({tshirt_size})"
                )

            else:

                items.append(
                    "T-Shirt"
                )

        if getattr(
            payment,
            "lanyard_selected",
            0
        ):

            items.append(
                "Lanyard"
            )

        if items:

            items_text = ", ".join(
                items
            )

        else:

            items_text = "Registration Payment"

        # ----------------------------------------------------
        # PAYMENT REFERENCE
        # ----------------------------------------------------

        reference = getattr(
            payment,
            "paymongo_reference",
            None
        )

        # ----------------------------------------------------
        # SUBJECT
        # ----------------------------------------------------

        subject = (
            "CYF Payment Confirmation "
            "- CYF Registration System"
        )

        # ----------------------------------------------------
        # EMAIL BODY
        # ----------------------------------------------------

        body = f"""
Dear {participant_name},

Thank you for your payment to the CYF Registration System.

We are pleased to confirm that your payment has been
successfully received.

PAYMENT DETAILS
----------------------------------------

Registration Number:
{getattr(participant, "registration_number", "N/A")}

Items:
{items_text}

Amount Paid:
₱{amount:,.2f}

Payment Status:
Paid
"""

        if reference:

            body += f"""
PayMongo Reference:
{reference}
"""

        body += """
----------------------------------------

Your selected items have been successfully recorded
in the CYF Registration System.

Thank you for your support.

God bless you!

CYF Registration Team
CYF Registration System
"""

        # ----------------------------------------------------
        # SEND THROUGH GMAIL SMTP
        # ----------------------------------------------------

        # ----------------------------------------------------
        # SEND THROUGH GMAIL SMTP
        # ----------------------------------------------------

        response = await send_gmail_smtp_async(
            recipient_email,
            subject,
            text_body=body
        )

        print("=" * 70)
        print(
            "PARTICIPANT CONFIRMATION EMAIL SENT"
        )
        print(
            "Recipient:",
            recipient_email
        )
        print(
            "Items:",
            items_text
        )
        print(
            "Amount:",
            f"₱{amount:,.2f}"
        )
        print(
            "Gmail SMTP Response:",
            response
        )
        print("=" * 70)

        return True

    except Exception as e:

        print("=" * 70)
        print(
            "PARTICIPANT CONFIRMATION EMAIL FAILED"
        )
        print(
            "Error:",
            repr(e)
        )
        print("=" * 70)

        return False






















# ======================================================
# CASH SPONSORSHIP CONFIRMATION EMAIL
# ======================================================

async def send_cash_sponsorship_confirmation_email(
    sponsorship,
    payment
):
    """
    Send confirmation email after a cash sponsorship
    has been successfully paid through PayMongo.
    """

    try:

        # --------------------------------------------------
        # GET SPONSOR EMAIL
        # --------------------------------------------------

        sponsor_email = getattr(
            sponsorship,
            "email",
            None
        )

        if not sponsor_email:

            print(
                "Cash sponsorship has no email address."
            )

            return False

        sponsor_email = str(
            sponsor_email
        ).strip()

        # --------------------------------------------------
        # GET INFORMATION
        # --------------------------------------------------

        sponsor_name = getattr(
            sponsorship,
            "sponsor_name",
            "Sponsor"
        )

        if not sponsor_name:

            sponsor_name = "Sponsor"


        tier = getattr(
            sponsorship,
            "selected_tier",
            None
        )

        if not tier:

            tier = getattr(
                sponsorship,
                "package_tier",
                "Sponsorship Package"
            )


        donation_amount = getattr(
            sponsorship,
            "donation_amount",
            0
        )

        # --------------------------------------------------
        # CONVERT CENTAVOS TO PHP
        # --------------------------------------------------

        try:

            donation_amount_php = (
                Decimal(
                    str(donation_amount)
                )
                /
                Decimal("100")
            )

        except Exception:

            donation_amount_php = Decimal(
                "0.00"
            )


        # --------------------------------------------------
        # PAYMENT STATUS
        # --------------------------------------------------

        payment_status = getattr(
            payment,
            "status",
            "Paid"
        )


        # --------------------------------------------------
        # PAYMONGO REFERENCE
        # --------------------------------------------------

        reference = getattr(
            sponsorship,
            "paymongo_reference",
            None
        )

        if not reference:

            reference = getattr(
                payment,
                "paymongo_reference",
                None
            )


        # --------------------------------------------------
        # EMAIL SUBJECT
        # --------------------------------------------------

        subject = (
            "Cash Sponsorship Payment Confirmation "
            "- CYF Registration System"
        )


        # --------------------------------------------------
        # EMAIL BODY
        # --------------------------------------------------

        body = f"""
Dear {sponsor_name},

Thank you for your generous support of the CYF ministry.

We are pleased to confirm that your cash sponsorship
payment has been successfully received.

SPONSORSHIP DETAILS
----------------------------------------
Name:
{sponsor_name}

Sponsorship Tier:
{tier}

Donation Amount:
₱{donation_amount_php:,.2f}

Payment Status:
{payment_status}
"""

        if reference:

            body += f"""
PayMongo Reference:
{reference}
"""

        body += """
----------------------------------------

Thank you for helping support our youth ministry
activities and CYF events.

Your generosity is greatly appreciated.

God bless you!

CYF Registration System
"""


        # --------------------------------------------------
        # SEND THROUGH GMAIL SMTP
        # --------------------------------------------------

        # --------------------------------------------------
        # SEND THROUGH GMAIL SMTP
        # --------------------------------------------------

        response = await send_gmail_smtp_async(
            sponsor_email,
            subject,
            text_body=body
        )


        # --------------------------------------------------
        # SUCCESS
        # --------------------------------------------------

        print(
            "Cash sponsorship confirmation email sent to:",
            sponsor_email
        )

        print(
            "Gmail SMTP response:",
            response
        )

        return True


    except Exception as e:

        print(
            "Cash sponsorship confirmation email failed:",
            repr(e)
        )

        return False





# ============================================================
# ADD SUCCESSFUL DONATION TO CASH DONATION TOTAL
# ============================================================

def add_cash_donation_to_total(
    db: Session,
    sponsorship: CashSponsorship
):

    # --------------------------------------------------------
    # ALREADY ADDED
    # --------------------------------------------------------

    if sponsorship.cash_total_added:

        return False

    # --------------------------------------------------------
    # CHECK PAYMENT STATUS
    # --------------------------------------------------------

    status = str(
        sponsorship.payment_status or ""
    ).strip().lower()

    if status not in [
        "paid",
        "success",
        "succeeded",
        "completed"
    ]:

        return False

    # --------------------------------------------------------
    # GET TOTAL RECORD
    # --------------------------------------------------------

    total_record = (
        db.query(
            CashDonationTotal
        )
        .first()
    )

    # --------------------------------------------------------
    # CREATE IF NEEDED
    # --------------------------------------------------------

    if not total_record:

        total_record = (
            CashDonationTotal(
                amount=0
            )
        )

        db.add(
            total_record
        )

        db.flush()

    # --------------------------------------------------------
    # ADD DONATION
    # --------------------------------------------------------

    total_record.amount = (
        int(
            total_record.amount or 0
        )
        +
        int(
            sponsorship.donation_amount or 0
        )
    )

    # --------------------------------------------------------
    # MARK AS ALREADY ADDED
    # --------------------------------------------------------

    sponsorship.cash_total_added = True

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    db.commit()

    db.refresh(
        total_record
    )

    return True













































# ======================================================
# STARTUP
# ======================================================

# ============================================================
# HTML PAGES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.get("/")
def home():
    return FileResponse(
        os.path.join(BASE_DIR, "home.html")
    )

@app.get("/styles.css")
async def styles_css():
    return FileResponse(
        os.path.join(BASE_DIR, "styles.css"),
        media_type="text/css"
    )
    

@app.get("/auth.js")
async def auth_js():
    return FileResponse(
        os.path.join(BASE_DIR, "auth.js"),
        media_type="application/javascript"
    )
    

@app.get("/home.html")
def home_html():
    return FileResponse(
        os.path.join(BASE_DIR, "home.html")
    )


@app.get("/store.html")
def store_html():
    return FileResponse(
        os.path.join(BASE_DIR, "store.html")
    )


@app.get("/register.html")
def register_html():
    return FileResponse(
        os.path.join(BASE_DIR, "register.html")
    )


@app.get("/sponsor.html")
def sponsor_html():
    return FileResponse(
        os.path.join(BASE_DIR, "sponsor.html")
    )

@app.get("/sponsor_rt.html")
def sponsor_html():
    return FileResponse(
        os.path.join(BASE_DIR, "sponsor_rt.html")
    )

@app.get("/cash-sponsor.html")
def cash_sponsor_html():
    return FileResponse(
        os.path.join(BASE_DIR, "cash-sponsor.html")
    )


@app.get("/item-sponsor.html")
def item_sponsor_html():
    return FileResponse(
        os.path.join(BASE_DIR, "item-sponsor.html")
    )


@app.get("/payment.html")
def payment_html():
    return FileResponse(
        os.path.join(BASE_DIR, "payment.html")
    )


@app.get("/contact.html")
def contact_html():
    return FileResponse(
        os.path.join(BASE_DIR, "contact.html")
    )


@app.get("/about.html")
def about_html():
    return FileResponse(
        os.path.join(BASE_DIR, "about.html")
    )


@app.get("/login.html")
def login_html():
    return FileResponse(
        os.path.join(BASE_DIR, "login.html")
    )


@app.get("/admin_dashboard.html")
def admin_dashboard_html():
    return FileResponse(
        os.path.join(BASE_DIR, "admin_dashboard.html")
    )


@app.get("/registration_dashboard.html")
def registration_dashboard_html():
    return FileResponse(
        os.path.join(BASE_DIR, "registration_dashboard.html")
    )

@app.get("/activity_event.html")
def activity_event():
    return FileResponse(
        os.path.join(BASE_DIR, "activity_event.html")
    )

@app.get("/activity_event_rt.html")
def activity_event():
    return FileResponse(
        os.path.join(BASE_DIR, "activity_event_rt.html")
    )
    
@app.get("/team_event.html")
def team_event():
    return FileResponse(
        os.path.join(BASE_DIR, "team_event.html")
    )        

@app.get("/team_event_rt.html")
def team_event():
    return FileResponse(
        os.path.join(BASE_DIR, "team_event_rt.html")
    )

@app.get("/program_event.html")
def program_event():
    return FileResponse(
        os.path.join(BASE_DIR, "program_event.html")
    )

@app.get("/program_event_rt.html")
def program_event():
    return FileResponse(
        os.path.join(BASE_DIR, "program_event_rt.html")
    )

@app.get("/finances_event.html")
def finances_event():
    return FileResponse(
        os.path.join(BASE_DIR, "finances_event.html")
    )

@app.get("/finances_event_rt.html")
def finances_event():
    return FileResponse(
        os.path.join(BASE_DIR, "finances_event_rt.html")
    )

@app.get("/report_event.html")
def report_event():
    return FileResponse(
        os.path.join(BASE_DIR, "report_event.html")
    )

@app.get("/report_event_rt.html")
def report_event():
    return FileResponse(
        os.path.join(BASE_DIR, "report_event_rt.html")
    )

@app.get("/event_event.html")
def event_event():
    return FileResponse(
        os.path.join(BASE_DIR, "event_event.html")
    )

@app.get("/event_event_rt.html")
def event_event():
    return FileResponse(
        os.path.join(BASE_DIR, "event_event_rt.html")
    )

@app.get("/participants.html")
def participants_page():
    return FileResponse(
        os.path.join(BASE_DIR, "participants.html")
    )

@app.get("/participants_rt.html")
def participants_page():
    return FileResponse(
        os.path.join(BASE_DIR, "participants_rt.html")
    )
    
@app.get("/staff.html")
def staff_page():
    return FileResponse(
        os.path.join(BASE_DIR, "staff.html")
    )

@app.get("/staff_rt.html")
def staff_page():
    return FileResponse(
        os.path.join(BASE_DIR, "staff_rt.html")
    )
    
@app.get("/chaperone.html")
def chaperone_page():
    return FileResponse(
        os.path.join(BASE_DIR, "chaperone.html")
    )

@app.get("/chaperone_rt.html")
def chaperone_page():
    return FileResponse(
        os.path.join(BASE_DIR, "chaperone_rt.html")
    )

@app.get("/store_items.html")
def store_items_page():
    return FileResponse(
        os.path.join(BASE_DIR, "store_items.html")
    )

@app.get("/store_items_rt.html")
def store_items_page():
    return FileResponse(
        os.path.join(BASE_DIR, "store_items_rt.html")
    )    

@app.get("/sponsor_management.html")
def sponsor_management_page():
    return FileResponse(
        os.path.join(BASE_DIR, "sponsor_management.html")
    )

@app.get("/sponsor_management_rt.html")
def sponsor_management_page():
    return FileResponse(
        os.path.join(BASE_DIR, "sponsor_management_rt.html")
    )

@app.get("/payment_management.html")
def payment_management_page():
    return FileResponse(
        os.path.join(BASE_DIR, "payment_management.html")
    )

@app.get("/payment_management_rt.html")
def payment_management_page():
    return FileResponse(
        os.path.join(BASE_DIR, "payment_management_rt.html")
    )

@app.get("/report.html")
def report_page():
    return FileResponse(
        os.path.join(BASE_DIR, "report.html")
    )

@app.get("/report_rt.html")
def report_page():
    return FileResponse(
        os.path.join(BASE_DIR, "report_rt.html")
    )

@app.get("/privacy")
def privacy_page():
    return FileResponse(
        os.path.join(BASE_DIR, "privacy.html")
    )

@app.get("/terms")
def terms_page():
    return FileResponse(
        os.path.join(BASE_DIR, "terms.html")
    )

@app.get("/sitemap.xml")
def sitemap_page():
    return FileResponse(
        os.path.join(BASE_DIR, "sitemap.xml")
    )

@app.get("/favicon.png")
def favicon_page():
    return FileResponse(
        os.path.join(BASE_DIR, "favicon.png"),
        media_type="image/png"
    )








    
# ======================================================
# AUTHENTICATION
# ======================================================

@app.post(
    "/auth_login_user",
    response_model=LoginResponseSchema
)
def auth_login_user(

    login: LoginSchema,

    db: Session = Depends(get_db)

):

    user = db.query(User).filter(

        User.username == login.username

    ).first()

    if not user:

        raise HTTPException(

            status_code=401,

            detail="Invalid username or password."

        )

    if not verify_password(

        login.password,

        user.password

    ):

        raise HTTPException(

            status_code=401,

            detail="Invalid username or password."

        )

    user.last_login = datetime.datetime.now()

    db.commit()

    fullname = f"{user.fname} {user.lname}"

    if user.role == "Admin":

        return {

            "message": "Login Successful",

            "role": user.role,

            "redirect": "/admin/dashboard",

            "fullname": fullname,

            "username": user.username

        }

    if user.role == "Registration Team":

        return {

            "message": "Login Successful",

            "role": user.role,

            "redirect": "/registration/dashboard",

            "fullname": fullname,

            "username": user.username

        }

    raise HTTPException(

        status_code=403,

        detail="Account role is invalid."

    )
    
@app.post("/auth_logout_user")
def auth_logout_user(

    logout: LogoutSchema

):

    return {

        "message": "Logout Successful",

        "username": logout.username

    }

# ======================================================
# USERS DASHBOARD
# ======================================================
    
    
@app.get("/admin/dashboard")
def dashboard_admin_home():

    return {

        "dashboard": "Admin Dashboard"

    }
    

@app.get("/registration/dashboard")
def dashboard_registration_team_home():

    return {

        "dashboard": "Registration Team Dashboard"

    }


# ======================================================
# ADMIN APIs
# ======================================================

    

@app.put("/admin_change_admin_credentials")
def admin_change_admin_credentials(

    data: AdminUpdateCredentialSchema,

    db: Session = Depends(get_db)

):

    admin = verify_admin(

        db,

        data.username

    )

    if not verify_password(

        data.old_password,

        admin.password

    ):

        raise HTTPException(

            status_code=400,

            detail="Old password is incorrect."

        )

    username_exist = db.query(User).filter(

        User.username == data.new_username,

        User.id != admin.id

    ).first()

    if username_exist:

        raise HTTPException(

            status_code=400,

            detail="Username already exists."

        )

    admin.username = data.new_username

    admin.password = hash_password(

        data.new_password

    )

    admin.updated_at = datetime.datetime.now()

    db.commit()

    return {

        "message": "Administrator credentials updated successfully."

    }
    

@app.post("/admin_create_registration_team_user")
def admin_create_registration_team_user(

    data: AdminCreateRegistrationTeamSchema,

    db: Session = Depends(get_db)

):

    # ======================================================
    # VERIFY ADMIN
    # ======================================================

    verify_admin(

        db,

        data.admin_username

    )

    # ======================================================
    # USERNAME VALIDATION
    # ======================================================

    username_exist = db.query(User).filter(

        User.username == data.username

    ).first()

    if username_exist:

        raise HTTPException(

            status_code=400,

            detail="Username already exists."

        )

    # ======================================================
    # EMAIL VALIDATION
    # ======================================================

    email_exist = db.query(User).filter(

        User.email == data.email

    ).first()

    if email_exist:

        raise HTTPException(

            status_code=400,

            detail="Email already exists."

        )

    # ======================================================
    # CONTACT NUMBER VALIDATION
    # ======================================================

    contact_exist = db.query(User).filter(

        User.contact_number == data.contact_number

    ).first()

    if contact_exist:

        raise HTTPException(

            status_code=400,

            detail="Contact number already exists."

        )
        
        

    # ======================================================
    # USERNAME FORMAT VALIDATION
    # ======================================================

    if len(data.username) < 5:

        raise HTTPException(

            status_code=400,

            detail="Username must be at least 5 characters."

        )

    # ======================================================
    # PASSWORD VALIDATION
    # ======================================================

    if len(data.password) < 8:

        raise HTTPException(

            status_code=400,

            detail="Password must be at least 8 characters."

        )

    # ======================================================
    # CONTACT NUMBER VALIDATION
    # ======================================================

    if len(data.contact_number) < 11:

        raise HTTPException(

            status_code=400,

            detail="Invalid contact number."

        )

    # ======================================================
    # CALCULATE AGE
    # ======================================================

    user_age = calculate_registration_age(

        data.birthday

    )

    # ======================================================
    # CREATE REGISTRATION TEAM ACCOUNT
    # ======================================================

    new_user = User(

        fname=data.fname,

        mname=data.mname,

        lname=data.lname,

        age=user_age,

        birthday=data.birthday,

        address=data.address,

        email=data.email,

        sex=data.sex,

        local_church=data.local_church,

        contact_number=data.contact_number,

        sector=data.sector,

        username=data.username,

        password=hash_password(

            data.password

        ),

        role="Registration Team",

        created_at=datetime.datetime.now(),

        updated_at=datetime.datetime.now()

    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    return {

        "message": "Registration Team account created successfully.",

        "user": {

            "user_id": new_user.id,

            "fullname": f"{new_user.fname} {new_user.mname} {new_user.lname}".strip(),

            "username": new_user.username,

            "email": new_user.email,

            "role": new_user.role,

            "age": new_user.age,

            "sector": new_user.sector,

            "local_church": new_user.local_church

        }

    }
    

# ======================================================
# REGISTER CHAPERONE
# ======================================================

@app.post("/register_chaperone")
def register_chaperone(
    data: ChaperoneCreateSchema,
    db: Session = Depends(get_db)
):

    # ======================================================
    # CHECK EVENT
    # ======================================================

    event = db.query(Event).filter(
        Event.id == data.event_id,
        Event.is_archived == 0
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found."
        )

    # ======================================================
    # DUPLICATE VALIDATION
    # ======================================================

    duplicate = db.query(Chaperone).filter(
        Chaperone.event_id == data.event_id,
        Chaperone.fname == data.fname,
        Chaperone.mname == data.mname,
        Chaperone.lname == data.lname,
        Chaperone.birthday == data.birthday,
        Chaperone.is_archived == 0
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail="Chaperone is already registered for this event."
        )

    # ======================================================
    # CREATE CHAPERONE
    # ======================================================

    chaperone = Chaperone(
        event_id=event.id,

        fname=data.fname,
        mname=data.mname,
        lname=data.lname,

        sex=data.sex,
        birthday=data.birthday,
        contact=data.contact_number,
        local_church=data.local_church,
        sector=data.sector,

        is_archived=0
    )

    db.add(chaperone)
    db.commit()
    db.refresh(chaperone)

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "message": "Chaperone registered successfully.",

        "chaperone": {
            "chaperone_id": chaperone.id,
            "event_id": chaperone.event_id,

            # Event name comes from Event table
            "event_name": event.event_name,

            "name": (
                f"{chaperone.fname} "
                f"{chaperone.mname or ''} "
                f"{chaperone.lname}"
            ).strip(),

            "sex": chaperone.sex,
            "birthday": chaperone.birthday,
            "contact": chaperone.contact,
            "local_church": chaperone.local_church,
            "sector": chaperone.sector
        }
    }


# ======================================================
# GET ALL CHAPERONES
# ======================================================

@app.get("/chaperones")
def get_all_chaperones(
    db: Session = Depends(get_db)
):

    chaperones = (
        db.query(Chaperone, Event)
        .join(
            Event,
            Chaperone.event_id == Event.id
        )
        .filter(
            Chaperone.is_archived == 0,
            Event.is_archived == 0
        )
        .order_by(
            Chaperone.id.desc()
        )
        .all()
    )

    result = []

    for chaperone, event in chaperones:

        result.append({
            "chaperone_id": chaperone.id,
            "event_id": chaperone.event_id,
            "event_name": event.event_name,

            "fname": chaperone.fname,
            "mname": chaperone.mname,
            "lname": chaperone.lname,

            "name": (
                f"{chaperone.fname} "
                f"{chaperone.mname or ''} "
                f"{chaperone.lname}"
            ).strip(),

            "sex": chaperone.sex,
            "birthday": chaperone.birthday,

            "contact": chaperone.contact,

            "local_church": chaperone.local_church,
            "sector": chaperone.sector,

            "is_archived": chaperone.is_archived,

            "created_at": chaperone.created_at,
            "updated_at": chaperone.updated_at
        })

    return {
        "message": "Chaperones retrieved successfully.",
        "count": len(result),
        "chaperones": result
    }


# ======================================================
# GET SINGLE CHAPERONE
# ======================================================

@app.get("/chaperone/{chaperone_id}")
def get_chaperone(
    chaperone_id: int,
    db: Session = Depends(get_db)
):

    result = (
        db.query(Chaperone, Event)
        .join(
            Event,
            Chaperone.event_id == Event.id
        )
        .filter(
            Chaperone.id == chaperone_id,
            Chaperone.is_archived == 0,
            Event.is_archived == 0
        )
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Chaperone not found."
        )

    chaperone, event = result

    return {
        "message": "Chaperone retrieved successfully.",

        "chaperone": {
            "chaperone_id": chaperone.id,
            "event_id": chaperone.event_id,
            "event_name": event.event_name,

            "fname": chaperone.fname,
            "mname": chaperone.mname,
            "lname": chaperone.lname,

            "name": (
                f"{chaperone.fname} "
                f"{chaperone.mname or ''} "
                f"{chaperone.lname}"
            ).strip(),

            "sex": chaperone.sex,
            "birthday": chaperone.birthday,

            "contact": chaperone.contact,

            "local_church": chaperone.local_church,
            "sector": chaperone.sector,

            "is_archived": chaperone.is_archived,

            "created_at": chaperone.created_at,
            "updated_at": chaperone.updated_at
        }
    }


# ======================================================
# ARCHIVE CHAPERONE
# ======================================================

@app.put("/archive_chaperone/{chaperone_id}")
def archive_chaperone(
    chaperone_id: int,
    db: Session = Depends(get_db)
):

    chaperone = db.query(Chaperone).filter(
        Chaperone.id == chaperone_id,
        Chaperone.is_archived == 0
    ).first()

    if not chaperone:
        raise HTTPException(
            status_code=404,
            detail="Chaperone not found."
        )

    # ==================================================
    # ARCHIVE
    # ==================================================

    chaperone.is_archived = 1

    db.commit()
    db.refresh(chaperone)

    return {
        "message": "Chaperone archived successfully.",

        "chaperone": {
            "chaperone_id": chaperone.id,
            "event_id": chaperone.event_id,

            "name": (
                f"{chaperone.fname} "
                f"{chaperone.mname or ''} "
                f"{chaperone.lname}"
            ).strip(),

            "is_archived": chaperone.is_archived
        }
    }


@app.put("/update_chaperone/{chaperone_id}")
def update_chaperone(
    chaperone_id: int,
    data: ChaperoneCreateSchema,
    db: Session = Depends(get_db)
):

    # ==================================================
    # FIND CHAPERONE
    # ==================================================

    chaperone = db.query(Chaperone).filter(
        Chaperone.id == chaperone_id,
        Chaperone.is_archived == 0
    ).first()

    if not chaperone:
        raise HTTPException(
            status_code=404,
            detail="Chaperone not found."
        )

    # ==================================================
    # CHECK EVENT
    # ==================================================

    event = db.query(Event).filter(
        Event.id == data.event_id,
        Event.is_archived == 0
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Event not found for event_id={data.event_id}."
        )

    # ==================================================
    # DUPLICATE VALIDATION
    # ==================================================

    duplicate = db.query(Chaperone).filter(
        Chaperone.id != chaperone_id,
        Chaperone.event_id == data.event_id,
        Chaperone.fname == data.fname,
        Chaperone.mname == data.mname,
        Chaperone.lname == data.lname,
        Chaperone.birthday == data.birthday,
        Chaperone.is_archived == 0
    ).first()

    if duplicate:
        raise HTTPException(
            status_code=400,
            detail=(
                "Another chaperone with the same "
                "information is already registered "
                "for this event."
            )
        )

    # ==================================================
    # UPDATE
    # ==================================================

    chaperone.event_id = data.event_id

    chaperone.fname = data.fname
    chaperone.mname = data.mname
    chaperone.lname = data.lname

    chaperone.sex = data.sex
    chaperone.birthday = data.birthday

    chaperone.contact = data.contact_number

    chaperone.local_church = data.local_church
    chaperone.sector = data.sector

    db.commit()
    db.refresh(chaperone)

    # ==================================================
    # RESPONSE
    # ==================================================

    return {
        "message": "Chaperone updated successfully.",
        "chaperone": {
            "chaperone_id": chaperone.id,
            "event_id": chaperone.event_id,
            "event_name": event.event_name,

            "fname": chaperone.fname,
            "mname": chaperone.mname,
            "lname": chaperone.lname,

            "name": (
                f"{chaperone.fname} "
                f"{chaperone.mname or ''} "
                f"{chaperone.lname}"
            ).strip(),

            "sex": chaperone.sex,
            "birthday": chaperone.birthday,
            "contact": chaperone.contact,
            "local_church": chaperone.local_church,
            "sector": chaperone.sector,

            "is_archived": chaperone.is_archived,
            "created_at": chaperone.created_at,
            "updated_at": chaperone.updated_at
        }
    }


# ======================================================
# REGISTER STAFF
# ======================================================

@app.post("/register_staff")
def register_staff(
    data: StaffCreateSchema,
    db: Session = Depends(get_db)
):

    event = db.query(Event).filter(
        Event.id == data.event_id,
        Event.is_archived == 0
    ).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    duplicate = db.query(Staff).filter(
        Staff.event_id == data.event_id,
        func.lower(Staff.fname) == data.fname.strip().lower(),
        func.lower(Staff.lname) == data.lname.strip().lower(),
        Staff.is_archived == 0
    ).first()

    if duplicate:
        raise HTTPException(status_code=400, detail="A staff member with the same name is already registered for this event.")

    staff = Staff(
        event_id=event.id,
        fname=data.fname.strip(),
        mname=(data.mname or "").strip(),
        lname=data.lname.strip(),
        position=data.position.strip(),
        sex=data.sex,
        birthday=data.birthday,
        contact=data.contact_number,
        local_church=data.local_church,
        sector=data.sector,
        is_archived=0
    )

    db.add(staff)
    db.commit()
    db.refresh(staff)

    return {
        "message": "Staff placeholder created successfully. The staff member can complete their profile later.",
        "staff": {
            "staff_id": staff.id,
            "event_id": staff.event_id,
            "event_name": event.event_name,
            "name": f"{staff.fname} {staff.mname} {staff.lname}".strip(),
            "position": staff.position,
            "profile_completed": bool(staff.sex and staff.birthday and staff.contact and staff.local_church and staff.sector)
        }
    }


@app.get("/register_view_all_staff")
def register_view_all_staff(
    event_id: int,
    db: Session = Depends(get_db)
):

    staff_members = db.query(Staff).filter(
        Staff.event_id == event_id,
        Staff.is_archived == 0
    ).all()

    event = db.query(Event).filter(
        Event.id == event_id,
        Event.is_archived == 0
    ).first()

    event_name = event.event_name if event else None

    return [
        {
            "staff_id": staff.id,
            "event_id": staff.event_id,
            "event_name": event_name,
            "fname": staff.fname,
            "mname": staff.mname,
            "lname": staff.lname,
            "position": staff.position,
            "sex": staff.sex,
            "birthday": staff.birthday,
            "contact": staff.contact,
            "local_church": staff.local_church,
            "sector": staff.sector
        }
        for staff in staff_members
    ]


@app.get("/register_view_staff/{staff_id}")
def register_view_staff(
    staff_id: int,
    db: Session = Depends(get_db)
):

    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.is_archived == 0
    ).first()

    if not staff:
        raise HTTPException(
            status_code=404,
            detail="Staff member not found."
        )

    event = db.query(Event).filter(
        Event.id == staff.event_id,
        Event.is_archived == 0
    ).first()

    return {
        "staff_id": staff.id,
        "event_id": staff.event_id,
        "event_name": event.event_name if event else None,
        "fname": staff.fname,
        "mname": staff.mname,
        "lname": staff.lname,
        "position": staff.position,
        "sex": staff.sex,
        "birthday": staff.birthday,
        "contact": staff.contact,
        "local_church": staff.local_church,
        "sector": staff.sector
    }


# ======================================================
# UPDATE STAFF
# ======================================================

@app.put("/register_update_staff/{staff_id}")
def register_update_staff(
    staff_id: int,
    data: StaffUpdateSchema,
    db: Session = Depends(get_db)
):

    staff = db.query(Staff).filter(
        Staff.id == staff_id,
        Staff.is_archived == 0
    ).first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found.")

    duplicate = db.query(Staff).filter(
        Staff.event_id == staff.event_id,
        func.lower(Staff.fname) == data.fname.strip().lower(),
        func.lower(Staff.lname) == data.lname.strip().lower(),
        Staff.id != staff_id,
        Staff.is_archived == 0
    ).first()

    if duplicate:
        raise HTTPException(status_code=400, detail="Another staff member with the same name already exists for this event.")

    staff.fname = data.fname.strip()
    staff.mname = (data.mname or "").strip()
    staff.lname = data.lname.strip()
    staff.position = data.position.strip()
    staff.sex = data.sex
    staff.birthday = data.birthday
    # IMPORTANT
    staff.contact = data.contact_number

    staff.local_church = data.local_church
    staff.sector = data.sector
    staff.updated_at = datetime.datetime.now()

    db.commit()
    db.refresh(staff)

    event = db.query(Event).filter(Event.id == staff.event_id).first()

    return {
        "message": "Staff member updated successfully.",
        "staff_id": staff.id,
        "event_id": staff.event_id,
        "event_name": event.event_name if event else None,
        "position": staff.position,
        "profile_completed": bool(staff.sex and staff.birthday and staff.contact and staff.local_church and staff.sector)
    }


# ======================================================
# FIND STAFF BY FULL NAME
# ======================================================

@app.get("/register_find_staff")
def register_find_staff(
    event_id: int,
    name: str,
    db: Session = Depends(get_db)
):
    """Find an active staff placeholder by exact full name for profile completion."""
    event = db.query(Event).filter(
        Event.id == event_id,
        Event.is_archived == 0
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")

    target = " ".join(name.split()).casefold()
    staff_members = db.query(Staff).filter(
        Staff.event_id == event_id,
        Staff.is_archived == 0
    ).all()

    matches = []
    for staff in staff_members:
        fullname = " ".join(f"{staff.fname} {staff.mname or ''} {staff.lname}".split())
        if fullname.casefold() == target:
            matches.append({
                "staff_id": staff.id,
                "event_id": staff.event_id,
                "event_name": event.event_name,
                "fname": staff.fname,
                "mname": staff.mname,
                "lname": staff.lname,
                "fullname": fullname,
                "position": staff.position,
                "sex": staff.sex,
                "birthday": staff.birthday,
                "contact": staff.contact,
                "local_church": staff.local_church,
                "sector": staff.sector,
                "profile_completed": bool(staff.sex and staff.birthday and staff.contact and staff.local_church and staff.sector)
            })

    if not matches:
        raise HTTPException(status_code=404, detail="No staff record matches that full name.")

    return matches


# ======================================================
# ARCHIVE STAFF
# ======================================================

@app.put("/register_archive_staff/{staff_id}")
def register_archive_staff(

    staff_id: int,

    db: Session = Depends(get_db)

):

    staff = db.query(Staff).filter(

        Staff.id == staff_id,

        Staff.is_archived == 0

    ).first()

    if not staff:

        raise HTTPException(

            status_code=404,

            detail="Staff member not found."

        )

    staff.is_archived = 1

    staff.updated_at = datetime.datetime.now()

    db.commit()

    return {

        "message": "Staff member archived successfully.",

        "staff_id": staff.id

    }


# ======================================================
# VIEW ARCHIVED STAFF
# ======================================================

@app.get("/register_view_archived_staff")
def register_view_archived_staff(

    event_id: int,

    db: Session = Depends(get_db)

):

    staff_members = db.query(Staff).filter(
        Staff.event_id == event_id,
        Staff.is_archived == 1
    ).all()

    event = db.query(Event).filter(Event.id == event_id).first()

    return [

        {

            "staff_id": staff.id,

            "event_id": staff.event_id,

            "event_name": event.event_name if event else None,

            "name": f"{staff.fname} {staff.mname} {staff.lname}".strip(),

            "position": staff.position,

            "sex": staff.sex,

            "birthday": staff.birthday,

            "contact": staff.contact,

            "local_church": staff.local_church,

            "sector": staff.sector

        }

        for staff in staff_members

    ]






@app.get("/admin_view_registration_team_users")
def admin_view_registration_team_users(

    admin_username: str,

    db: Session = Depends(get_db)

):

    verify_admin(

        db,

        admin_username

    )

    users = db.query(User).filter(

        User.role == "Registration Team"

    ).all()

    return [

        {

            "id":user.id,

            "fullname":f"{user.fname} {user.mname} {user.lname}",

            "username":user.username,

            "email":user.email,

            "sector":user.sector,

            "local_church":user.local_church,

            "contact_number":user.contact_number

        }

        for user in users

    ]
    




# ======================================================
# CREATE EVENT
# ======================================================

@app.post("/event_create_event")
def event_create_event(

    data: EventCreateSchema,

    db: Session = Depends(get_db)

):

    # ----------------------------------------
    # Allowed Event Types
    # ----------------------------------------

    allowed_events = [

        "Summer Youth Camp",

        "Youth Bible Conference"

    ]

    if data.event_name not in allowed_events:

        raise HTTPException(

            status_code=400,

            detail="Invalid event type."

        )

    # ----------------------------------------
    # Date Validations
    # ----------------------------------------

    if data.registration_start > data.registration_end:

        raise HTTPException(

            status_code=400,

            detail="Registration Start Date cannot be later than Registration End Date."

        )

    if data.registration_end > data.kickoff_date:

        raise HTTPException(

            status_code=400,

            detail="Registration End Date must be on or before the Kickoff Date."

        )

    if data.kickoff_date > data.wrapup_date:

        raise HTTPException(

            status_code=400,

            detail="Kickoff Date cannot be later than Wrap-up Date."

        )

    # ----------------------------------------
    # Duplicate Event Validation
    # ----------------------------------------

    duplicate = db.query(Event).filter(

        Event.event_name == data.event_name,

        Event.registration_start == data.registration_start,

        Event.registration_end == data.registration_end,

        Event.kickoff_date == data.kickoff_date,

        Event.wrapup_date == data.wrapup_date,

        Event.is_archived == 0

    ).first()

    if duplicate:

        raise HTTPException(

            status_code=400,

            detail="This active event already exists."

        )

    # ----------------------------------------
    # Create Event
    # ----------------------------------------

    new_event = Event(

        event_name=data.event_name,

        registration_start=data.registration_start,

        registration_end=data.registration_end,

        kickoff_date=data.kickoff_date,

        wrapup_date=data.wrapup_date,

        is_archived=0

    )

    db.add(new_event)

    db.commit()

    db.refresh(new_event)

    return {

        "message": "Event created successfully.",

        "event_id": new_event.id,

        "event_name": new_event.event_name,

        "registration_period": {

            "start": new_event.registration_start,

            "end": new_event.registration_end

        },

        "event_schedule": {

            "kickoff": new_event.kickoff_date,

            "wrapup": new_event.wrapup_date

        }

    }

# ======================================================
# VIEW ALL EVENTS
# ======================================================

@app.get("/event_view_all_events")
def event_view_all_events(

    db: Session = Depends(get_db)

):

    events = db.query(Event).filter(

        Event.is_archived == 0

    ).all()

    today = datetime.date.today()

    results = []

    for event in events:

        # ==========================================
        # PARTICIPANT COUNTS
        # ==========================================

        total_participants = db.query(Participant).filter(

            Participant.event_id == event.id,

            Participant.is_archived == 0

        ).count()

        early_bird = db.query(Participant).filter(

            Participant.event_id == event.id,

            Participant.registration_phase == "Early-bird",

            Participant.is_archived == 0

        ).count()

        walk_in = db.query(Participant).filter(

            Participant.event_id == event.id,

            Participant.registration_phase == "Walk-in",

            Participant.is_archived == 0

        ).count()

        completed = db.query(Participant).filter(

            Participant.event_id == event.id,

            Participant.registration_status == "Completed",

            Participant.is_archived == 0

        ).count()

        pending = db.query(Participant).filter(

            Participant.event_id == event.id,

            Participant.registration_status == "Pending",

            Participant.is_archived == 0

        ).count()

        # ==========================================
        # EVENT STATUS
        # ==========================================

        if today < event.registration_start:

            event_status = "Upcoming"

        elif event.registration_start <= today <= event.registration_end:

            event_status = "Registration Open"

        elif event.registration_end < today < event.kickoff_date:

            event_status = "Walk-in Registration"

        elif event.kickoff_date <= today <= event.wrapup_date:

            event_status = "Ongoing"

        else:

            event_status = "Finished"

        # ==========================================
        # REGISTRATION PHASE
        # ==========================================

        registration_phase = get_registration_phase(event)

        # ==========================================
        # APPEND RESULT
        # ==========================================

        results.append({

            "event_id": event.id,

            "event_name": event.event_name,

            "registration_start": event.registration_start,

            "registration_end": event.registration_end,

            "kickoff_date": event.kickoff_date,

            "wrapup_date": event.wrapup_date,

            "registration_phase": registration_phase,

            "event_status": event_status,

            "participants": {

                "total": total_participants,

                "early_bird": early_bird,

                "walk_in": walk_in,

                "completed": completed,

                "pending": pending

            },

            "is_archived": bool(event.is_archived)

        })

    return results



# ======================================================
# RESTORE ARCHIVED EVENT
# ======================================================

@app.put("/event_restore_event")
def event_restore_event(

    event_id: int,

    db: Session = Depends(get_db)

):

    event = db.query(Event).filter(

        Event.id == event_id,

        Event.is_archived == 1

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="Archived event not found."

        )

    duplicate = db.query(Event).filter(

        Event.event_name == event.event_name,

        Event.kickoff_date == event.kickoff_date,

        Event.is_archived == 0,

        Event.id != event.id

    ).first()

    if duplicate:

        raise HTTPException(

            status_code=400,

            detail="Another active event with the same name and kickoff date already exists."

        )

    event.is_archived = 0

    event.updated_at = datetime.datetime.now()

    db.commit()

    db.refresh(event)

    return {

        "message": "Event restored successfully.",

        "event_id": event.id,

        "event_name": event.event_name

    }


# ======================================================
# VIEW SINGLE EVENT
# ======================================================

@app.get("/event_view_single_event")
def event_view_single_event(

    event_id: int,

    db: Session = Depends(get_db)

):

    event = db.query(Event).filter(

        Event.id == event_id

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="Event not found."

        )

    total_participants = db.query(Participant).filter(

        Participant.event_id == event.id,

        Participant.is_archived == 0

    ).count()

    return {

        "event_id": event.id,

        "event_name": event.event_name,

        "registration_start": event.registration_start,

        "registration_end": event.registration_end,

        "kickoff_date": event.kickoff_date,

        "wrapup_date": event.wrapup_date,

        "registration_phase": get_registration_phase(event),

        "is_archived": bool(event.is_archived),

        "total_participants": total_participants,

        "created_at": event.created_at,

        "updated_at": event.updated_at

    }


# ======================================================
# VIEW CURRENT ACTIVE EVENT
# ======================================================

@app.get("/event_view_current_active_event")
def event_view_current_active_event(

    db: Session = Depends(get_db)

):

    today = datetime.date.today()

    event = db.query(Event).filter(

        Event.is_archived == 0,

        Event.registration_start <= today,

        Event.wrapup_date >= today

    ).order_by(

        Event.kickoff_date.asc()

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="No active event found."

        )

    total_participants = db.query(Participant).filter(

        Participant.event_id == event.id,

        Participant.is_archived == 0

    ).count()

    early_bird = db.query(Participant).filter(

        Participant.event_id == event.id,

        Participant.registration_phase == "Early-bird",

        Participant.is_archived == 0

    ).count()

    walk_in = db.query(Participant).filter(

        Participant.event_id == event.id,

        Participant.registration_phase == "Walk-in",

        Participant.is_archived == 0

    ).count()

    return {

        "event_id": event.id,

        "event_name": event.event_name,

        "registration_start": event.registration_start,

        "registration_end": event.registration_end,

        "kickoff_date": event.kickoff_date,

        "wrapup_date": event.wrapup_date,

        "registration_phase": get_registration_phase(event),

        "participants": {

            "total": total_participants,

            "early_bird": early_bird,

            "walk_in": walk_in

        }

    }

# ======================================================
# UPDATE EVENTS
# ======================================================


@app.put("/event_update_event")
def event_update_event(

    event_id: int,

    data: EventUpdateSchema,

    db: Session = Depends(get_db)

):

    event = db.query(Event).filter(

        Event.id == event_id,

        Event.is_archived == 0

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="Event not found."

        )

    allowed_events = [

        "Summer Youth Camp",

        "Youth Bible Conference"

    ]

    if data.event_name not in allowed_events:

        raise HTTPException(

            status_code=400,

            detail="Invalid event name."

        )

    if data.registration_start > data.registration_end:

        raise HTTPException(

            status_code=400,

            detail="Registration start cannot be later than registration end."

        )

    if data.registration_end > data.kickoff_date:

        raise HTTPException(

            status_code=400,

            detail="Registration must end on or before the Kickoff date."

        )

    if data.kickoff_date > data.wrapup_date:

        raise HTTPException(

            status_code=400,

            detail="Kickoff date cannot be later than Wrap-up date."

        )

    duplicate = db.query(Event).filter(

        Event.event_name == data.event_name,

        Event.kickoff_date == data.kickoff_date,

        Event.id != event_id,

        Event.is_archived == 0

    ).first()

    if duplicate:

        raise HTTPException(

            status_code=400,

            detail="Another active event with the same name and kickoff date already exists."

        )

    event.event_name = data.event_name

    event.registration_start = data.registration_start

    event.registration_end = data.registration_end

    event.kickoff_date = data.kickoff_date

    event.wrapup_date = data.wrapup_date

    event.updated_at = datetime.datetime.now()

    db.commit()

    return {

        "message":"Event updated successfully."

    }
    
    
# ======================================================
# DELETE EVENTS
# ======================================================    


@app.delete("/event_delete_event")
def event_delete_event(

    event_id: int,

    db: Session = Depends(get_db)

):

    # ======================================================
    # CHECK EVENT
    # ======================================================

    event = db.query(Event).filter(

        Event.id == event_id

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="Event not found."

        )

    # ======================================================
    # CHECK REGISTERED PARTICIPANTS
    # ======================================================

    participant = db.query(Participant).filter(

        Participant.event_id == event_id,

        Participant.is_archived == 0

    ).first()

    if participant:

        raise HTTPException(

            status_code=400,

            detail="This event cannot be deleted because it already has registered participants."

        )

    # ======================================================
    # DELETE EVENT
    # ======================================================

    db.delete(event)

    db.commit()

    return {

        "message": "Event deleted successfully."

    }


# ======================================================
# ARCHIVE EVENT
# ======================================================

@app.put("/event_archive_event")
def event_archive_event(

    event_id: int,

    db: Session = Depends(get_db)

):

    # ======================================================
    # CHECK EVENT
    # ======================================================

    event = db.query(Event).filter(

        Event.id == event_id,

        Event.is_archived == 0

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="Event not found."

        )

    # ======================================================
    # CHECK EVENT HAS ENDED
    # ======================================================

    today = datetime.date.today()

    if today <= event.wrapup_date:

        raise HTTPException(

            status_code=400,

            detail="This event cannot be archived until the event has ended."

        )

    # ======================================================
    # CHECK INCOMPLETE REGISTRATIONS
    # ======================================================

    incomplete_registration = db.query(Participant).filter(

        Participant.event_id == event.id,

        Participant.is_archived == 0,

        Participant.registration_status != "Completed"

    ).first()

    if incomplete_registration:

        raise HTTPException(

            status_code=400,

            detail="This event cannot be archived because there are participants with incomplete registrations."

        )

    # ======================================================
    # ARCHIVE EVENT
    # ======================================================

    event.is_archived = 1

    event.updated_at = datetime.datetime.now()

    db.commit()

    db.refresh(event)

    # ======================================================
    # RETURN RESULT
    # ======================================================

    return {

        "message": "Event archived successfully.",

        "event": {

            "event_id": event.id,

            "event_name": event.event_name,

            "registration_start": event.registration_start,

            "registration_end": event.registration_end,

            "kickoff_date": event.kickoff_date,

            "wrapup_date": event.wrapup_date,

            "is_archived": bool(event.is_archived),

            "archived_at": event.updated_at

        }

    }


# ======================================================
# VIEW ARCHIVE EVENT
# ======================================================  
    

@app.get("/event_view_archived_events")
def event_view_archived_events(

    db: Session = Depends(get_db)

):

    events = db.query(Event).filter(

        Event.is_archived == 1

    ).all()

    result = []

    for event in events:

        result.append({

            "id":event.id,

            "event_name":event.event_name,

            "kickoff_date":event.kickoff_date,

            "wrapup_date":event.wrapup_date

        })

    return result


# ======================================================
# CREATE PARTICIPANT
# ======================================================  


@app.post("/registration_create_participant")
def registration_create_participant(

    data: ParticipantCreateSchema,

    db: Session = Depends(get_db)

):

    # ======================================================
    # CHECK EVENT
    # ======================================================

    event = db.query(Event).filter(

        Event.id == data.event_id,

        Event.is_archived == 0

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="Event not found."

        )

    # ======================================================
    # CHECK PARTICIPANT TYPE
    # ======================================================

    allowed_participant_types = [

        "Regular Participants",

        "Finding Sponsor"

    ]

    if data.participant_type not in allowed_participant_types:

        raise HTTPException(

            status_code=400,

            detail="Invalid participant type. Choose either Regular Participants or Finding Sponsor."

        )

    # ======================================================
    # CHECK REGISTRATION PERIOD
    # ======================================================

    today = datetime.date.today()

    if today < event.registration_start:

        raise HTTPException(

            status_code=400,

            detail="Event registration has not started yet."

        )

    # ======================================================
    # CHECK EVENT KICKOFF
    # ======================================================

    if today > event.kickoff_date:

        raise HTTPException(

            status_code=400,

            detail="Registration is already closed because the event has started."

        )

    # ======================================================
    # DUPLICATE VALIDATION
    # ======================================================

    duplicate = registration_duplicate_validation(

        db,

        data.event_id,

        data.fname,

        data.mname,

        data.lname,

        data.birthdate

    )

    if duplicate:

        raise HTTPException(

            status_code=400,

            detail="Participant is already registered for this event."

        )

    # ======================================================
    # REGISTRATION PHASE
    # ======================================================

    registration_phase = registration_phase_validation(

        event

    )

    # ======================================================
    # CALCULATE REGISTRATION AGE
    # ======================================================

    registration_age = calculate_registration_age(

        data.birthdate

    )

    # ======================================================
    # GENERATE REGISTRATION NUMBER
    # ======================================================

    registration_number = registration_number_generator(

        db,

        event

    )

    # ======================================================
    # CREATE PARTICIPANT
    # ======================================================

    participant = Participant(

        # -----------------------------
        # Event Reference
        # -----------------------------

        event_id=event.id,

        # -----------------------------
        # Event Snapshot
        # -----------------------------

        event_name=event.event_name,

        registration_start=event.registration_start,

        registration_end=event.registration_end,

        kickoff_date=event.kickoff_date,

        wrapup_date=event.wrapup_date,

        # -----------------------------
        # Registration Information
        # -----------------------------

        registration_number=registration_number,

        registration_date=today,

        registration_phase=registration_phase,

        registration_status="Pending",

        participant_type=data.participant_type,

        registration_age=registration_age,

        # -----------------------------
        # Participant Information
        # -----------------------------

        fname=data.fname,

        mname=data.mname,

        lname=data.lname,

        sex=data.sex,

        birthdate=data.birthdate,

        address=data.address,

        contact_number=data.contact_number,

        emergency_contact=data.emergency_contact,

        email=data.email,

        local_church=data.local_church,

        sector=data.sector

    )

    # ======================================================
    # SAVE PARTICIPANT
    # ======================================================

    db.add(participant)

    db.commit()

    db.refresh(participant)

    # ======================================================
    # RESPONSE
    # ======================================================

    return {

        "message": "Participant registered successfully.",

        "participant": {

            "participant_id": participant.id,

            "registration_number": participant.registration_number,

            "participant_type": participant.participant_type,

            "registration_phase": participant.registration_phase,

            "registration_status": participant.registration_status,

            "registration_age": participant.registration_age

        },

        "event": {

            "event_id": participant.event_id,

            "event_name": participant.event_name,

            "registration_start": participant.registration_start,

            "registration_end": participant.registration_end,

            "kickoff_date": participant.kickoff_date,

            "wrapup_date": participant.wrapup_date

        }

    }











# ======================================================
# SEARCH PARTICIPANT
# ======================================================

@app.get("/registration_search_participant")
def registration_search_participant(
    keyword: str,
    db: Session = Depends(get_db)
):

    # ==================================================
    # CLEAN SEARCH KEYWORD
    # ==================================================

    keyword = (keyword or "").strip().lower()

    # ==================================================
    # PREVENT SINGLE-LETTER SEARCH
    # ==================================================
    #
    # Example:
    # "c"  -> no results
    # "cy" -> search
    #
    # ==================================================

    if len(keyword) < 2:
        return []

    # ==================================================
    # GET ACTIVE PARTICIPANTS
    # ==================================================

    participants = db.query(Participant).filter(
        Participant.is_archived == 0
    ).all()

    result = []

    for participant in participants:

        # ==================================================
        # FULL NAME
        # ==================================================

        fullname = " ".join(
            part for part in [
                participant.fname,
                participant.mname,
                participant.lname
            ]
            if part
        ).strip()

        fullname_lower = fullname.lower()

        # ==================================================
        # SEARCHABLE VALUES
        # ==================================================
        #
        # SEARCH ONLY:
        #   1. Name
        #   2. Event name
        #   3. Registration ID
        #
        # DO NOT SEARCH:
        #   - Paid
        #   - Unpaid
        #   - Partial
        #   - T-shirt status
        #   - Lanyard status
        #   - Email
        #   - Contact number
        #   - Registration phase
        #   - Registration status
        #   - Participant type
        #   - Sponsorship status
        #   - Participant tier
        #
        # ==================================================

        registration_number = str(
            participant.registration_number or ""
        ).strip().lower()

        event_name = str(
            participant.event_name or ""
        ).strip().lower()

        searchable_values = [
            fullname_lower,
            event_name,
            registration_number
        ]

        # ==================================================
        # MATCH SEARCH
        # ==================================================

        matched = any(
            keyword in value
            for value in searchable_values
        )

        if not matched:
            continue

        # ==================================================
        # PARTICIPANT TYPE
        # ==================================================

        participant_type = str(
            participant.participant_type or ""
        ).strip()

        is_sponsor_participant = (
            participant_type.lower()
            == "finding sponsor"
        )

        # ==================================================
        # PAYMENT STATUS
        # ==================================================
        #
        # This is returned to the frontend for display
        # only. It is NOT searchable.
        #
        # ==================================================

        tshirt_status = str(
            participant.tshirt_status or "Unpaid"
        )

        lanyard_status = str(
            participant.lanyard_status or "Unpaid"
        )

        tshirt_status_lower = tshirt_status.lower()
        lanyard_status_lower = lanyard_status.lower()

        if (
            tshirt_status_lower == "paid"
            and lanyard_status_lower == "paid"
        ):

            payment_status = "Paid"

        elif (
            tshirt_status_lower == "paid"
            or lanyard_status_lower == "paid"
        ):

            payment_status = "Partial"

        else:

            payment_status = "Unpaid"

        # ==================================================
        # SPONSORSHIP STATUS
        # ==================================================

        if is_sponsor_participant:

            sponsorship_status = "Sponsored in Review"

            if (
                tshirt_status_lower == "paid"
                and lanyard_status_lower == "paid"
            ):

                merchandise_status = "Sponsored Confirmed"

            elif (
                tshirt_status_lower == "paid"
                or lanyard_status_lower == "paid"
            ):

                merchandise_status = "Sponsored - Partial"

            else:

                merchandise_status = "Sponsored in Review"

            payment_status = sponsorship_status

        else:

            sponsorship_status = None
            merchandise_status = payment_status

        # ==================================================
        # PARTICIPANT TIER / EVALUATION
        # ==================================================

        evaluation = db.query(
            ParticipantEvaluation
        ).filter(
            ParticipantEvaluation.participant_id
            == participant.id
        ).first()

        participant_tier = (
            evaluation.participant_tier
            if evaluation
            else None
        )

        # ==================================================
        # RESULT
        # ==================================================

        result.append({

            # ----------------------------------------------
            # PARTICIPANT
            # ----------------------------------------------

            "participant_id":
                participant.id,

            "registration_number":
                participant.registration_number,

            "fullname":
                fullname,

            # ----------------------------------------------
            # EVENT
            # ----------------------------------------------

            "event_name":
                participant.event_name,

            # ----------------------------------------------
            # PARTICIPANT TYPE
            # ----------------------------------------------

            "participant_type":
                participant_type,

            "is_sponsor_participant":
                is_sponsor_participant,

            # ----------------------------------------------
            # REGISTRATION
            # ----------------------------------------------

            "registration_phase":
                participant.registration_phase,

            "registration_status":
                participant.registration_status,

            # ----------------------------------------------
            # PAYMENT
            # ----------------------------------------------
            #
            # Returned for display only.
            # NOT used for search.
            #
            # ----------------------------------------------

            "payment_status":
                payment_status,

            # ----------------------------------------------
            # SPONSORSHIP
            # ----------------------------------------------

            "sponsorship_status":
                sponsorship_status,

            # ----------------------------------------------
            # MERCHANDISE
            # ----------------------------------------------

            "merchandise_status":
                merchandise_status,

            "tshirt_status":
                participant.tshirt_status or "Unpaid",

            "lanyard_status":
                participant.lanyard_status or "Unpaid",

            # ----------------------------------------------
            # EVALUATION
            # ----------------------------------------------

            "participant_tier":
                participant_tier

        })

    return result











# ======================================================
# FILTER REGISTRATION PHASE
# ======================================================  

@app.get("/registration_filter_registration_phase")
def registration_filter_registration_phase(

    registration_phase: str,

    db: Session = Depends(get_db)

):

    participants = db.query(Participant).filter(

        Participant.registration_phase == registration_phase,

        Participant.is_archived == 0

    ).all()

    return participants


# ======================================================
# FILTER REGISTRATION STATUS
# ======================================================  

@app.get("/registration_filter_registration_status")
def registration_filter_registration_status(

    registration_status: str,

    db: Session = Depends(get_db)

):

    participants = db.query(Participant).filter(

        Participant.registration_status == registration_status,

        Participant.is_archived == 0

    ).all()

    return participants

# ======================================================
# FILTER PARTICIPANTS BY EVENT
# ======================================================  

@app.get("/registration_filter_event")
def registration_filter_event(

    event_id: int,

    db: Session = Depends(get_db)

):

    participants = db.query(Participant).filter(

        Participant.event_id == event_id,

        Participant.is_archived == 0

    ).all()

    return participants

# ======================================================
# FILTER PARTICIPANT TIER
# ======================================================  

@app.get("/registration_filter_participant_tier")
def registration_filter_participant_tier(

    participant_tier: str,

    db: Session = Depends(get_db)

):

    evaluations = db.query(

        ParticipantEvaluation

    ).filter(

        ParticipantEvaluation.participant_tier == participant_tier

    ).all()

    result = []

    for evaluation in evaluations:

        participant = db.query(Participant).filter(

            Participant.id == evaluation.participant_id,

            Participant.is_archived == 0

        ).first()

        if participant:

            result.append({

                "participant_id": participant.id,

                "registration_number": participant.registration_number,

                "fullname": f"{participant.fname} {participant.mname} {participant.lname}",

                "event_name": participant.event_name,

                "participant_tier": evaluation.participant_tier,

                "spiritual_score": evaluation.spiritual_score,

                "influence_score": evaluation.influence_score

            })

    return result
    
# ======================================================
# VIEW ALL PARTICIPANTS
# ======================================================  

@app.get("/registration_view_all_participants")
def registration_view_all_participants(

    db: Session = Depends(get_db)

):

    participants = db.query(Participant).filter(

        Participant.is_archived == 0

    ).all()

    return participants


# ======================================================
# VIEW PARTICIPANT DETAILS
# ======================================================  

@app.get("/registration_view_participant_details/{participant_id}")
def registration_view_participant_details(

    participant_id: int,

    db: Session = Depends(get_db)

):

    participant = db.query(Participant).filter(

        Participant.id == participant_id,

        Participant.is_archived == 0

    ).first()

    if not participant:

        raise HTTPException(

            status_code=404,

            detail="Participant not found."

        )

    return participant


# ======================================================
# UPDATE PARTICIPANT
# ======================================================

@app.put("/registration_update_participant/{participant_id}")
def registration_update_participant(

    participant_id: int,

    data: ParticipantUpdateSchema,

    db: Session = Depends(get_db)

):

    # ======================================================
    # CHECK PARTICIPANT
    # ======================================================

    participant = db.query(Participant).filter(

        Participant.id == participant_id,

        Participant.is_archived == 0

    ).first()

    if not participant:

        raise HTTPException(

            status_code=404,

            detail="Participant not found."

        )

    # ======================================================
    # CHECK PARTICIPANT TYPE
    # ======================================================

    allowed_participant_types = [

        "Regular Participants",

        "Finding Sponsor"

    ]

    if data.participant_type not in allowed_participant_types:

        raise HTTPException(

            status_code=400,

            detail="Invalid participant type. Choose either Regular Participants or Finding Sponsor."

        )

    # ======================================================
    # CHECK EVENT
    # ======================================================

    event = db.query(Event).filter(

        Event.id == data.event_id,

        Event.is_archived == 0

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="Event not found."

        )

    # ======================================================
    # DUPLICATE VALIDATION
    # ======================================================

    duplicate = db.query(Participant).filter(

        Participant.event_id == data.event_id,

        Participant.fname == data.fname,

        Participant.mname == data.mname,

        Participant.lname == data.lname,

        Participant.birthdate == data.birthdate,

        Participant.id != participant_id,

        Participant.is_archived == 0

    ).first()

    if duplicate:

        raise HTTPException(

            status_code=400,

            detail="Another participant with the same name and birthdate is already registered for this event."

        )

    # ======================================================
    # UPDATE EVENT REFERENCE
    # ======================================================

    participant.event_id = event.id

    # ======================================================
    # UPDATE EVENT SNAPSHOT
    # ======================================================

    participant.event_name = event.event_name

    participant.registration_start = event.registration_start

    participant.registration_end = event.registration_end

    participant.kickoff_date = event.kickoff_date

    participant.wrapup_date = event.wrapup_date

    # ======================================================
    # UPDATE PARTICIPANT TYPE
    # ======================================================

    participant.participant_type = data.participant_type

    # ======================================================
    # UPDATE PARTICIPANT INFORMATION
    # ======================================================

    participant.fname = data.fname

    participant.mname = data.mname

    participant.lname = data.lname

    participant.sex = data.sex

    participant.birthdate = data.birthdate

    participant.registration_age = calculate_registration_age(

        data.birthdate

    )

    participant.address = data.address

    participant.contact_number = data.contact_number

    participant.emergency_contact = data.emergency_contact

    participant.email = data.email

    participant.local_church = data.local_church

    participant.sector = data.sector

    # ======================================================
    # UPDATE TIMESTAMP
    # ======================================================

    participant.updated_at = datetime.datetime.now()

    # ======================================================
    # SAVE CHANGES
    # ======================================================

    db.commit()

    db.refresh(participant)

    # ======================================================
    # RESPONSE
    # ======================================================

    return {

        "message": "Participant updated successfully.",

        "participant": {

            "participant_id": participant.id,

            "registration_number": participant.registration_number,

            "participant_type": participant.participant_type,

            "registration_age": participant.registration_age,

            "registration_phase": participant.registration_phase,

            "registration_status": participant.registration_status

        },

        "event": {

            "event_id": participant.event_id,

            "event_name": participant.event_name,

            "registration_start": participant.registration_start,

            "registration_end": participant.registration_end,

            "kickoff_date": participant.kickoff_date,

            "wrapup_date": participant.wrapup_date

        }

    }
    

# ======================================================
# ARCHIVE PARTICIPANT
# ======================================================  


@app.put("/registration_archive_participant/{participant_id}")
def registration_archive_participant(

    participant_id: int,

    db: Session = Depends(get_db)

):

    participant = db.query(Participant).filter(

        Participant.id == participant_id,

        Participant.is_archived == 0

    ).first()

    if not participant:

        raise HTTPException(

            status_code=404,

            detail="Participant not found."

        )

    participant.is_archived = 1

    participant.updated_at = datetime.datetime.now()

    db.commit()

    return {

        "message":"Participant archived successfully."

    }
    



# ======================================================
# RESTORE PARTICIPANT
# ======================================================  

@app.put("/registration_restore_participant/{participant_id}")
def registration_restore_participant(

    participant_id: int,

    db: Session = Depends(get_db)

):

    participant = db.query(Participant).filter(

        Participant.id == participant_id,

        Participant.is_archived == 1

    ).first()

    if not participant:

        raise HTTPException(

            status_code=404,

            detail="Archived participant not found."

        )

    participant.is_archived = 0

    participant.updated_at = datetime.datetime.now()

    db.commit()

    return {

        "message":"Participant restored successfully."

    }

# ======================================================
# VIEW ARCHIVED PARTICIPANTS
# ======================================================      

@app.get("/registration_view_archived_participants")
def registration_view_archived_participants(

    db: Session = Depends(get_db)

):

    participants = db.query(Participant).filter(

        Participant.is_archived == 1

    ).all()

    return participants


# ======================================================
# Questionnaire
# ====================================================== 


@app.post("/questionnaire_submit_answers")
def questionnaire_submit_answers(

    data: QuestionnaireSchema,

    db: Session = Depends(get_db)

):

    participant = db.query(Participant).filter(

        Participant.id == data.participant_id,

        Participant.is_archived == 0

    ).first()

    if not participant:

        raise HTTPException(

            status_code=404,

            detail="Participant not found."

        )

    duplicate = questionnaire_duplicate_validation(

        db,

        data.participant_id

    )

    if duplicate:

        raise HTTPException(

            status_code=400,

            detail="Questionnaire already submitted."

        )

    questionnaire = Questionnaire(

        participant_id=data.participant_id,

        camp_attendance=data.camp_attendance,

        leadership_position=data.leadership_position,

        church_involvement=data.church_involvement,

        primary_strength=data.primary_strength,

        ministry_skill=data.ministry_skill,

        salvation_assurance=data.salvation_assurance,

        daily_devotion=data.daily_devotion,

        ministry_involvement=data.ministry_involvement,

        sermon_notes=data.sermon_notes,

        small_group=data.small_group,

        gospel_sharing=data.gospel_sharing,

        temptation_response=data.temptation_response

    )

    db.add(questionnaire)

    db.commit()

    db.refresh(questionnaire)

    return {

        "message":"Questionnaire submitted successfully.",

        "questionnaire_id":questionnaire.id

    }
    

# ======================================================
# View Questionnaire
# ====================================================== 


@app.get("/questionnaire_view_answers/{participant_id}")
def questionnaire_view_answers(

    participant_id: int,

    db: Session = Depends(get_db)

):

    questionnaire = db.query(Questionnaire).filter(

        Questionnaire.participant_id == participant_id

    ).first()

    if not questionnaire:

        raise HTTPException(

            status_code=404,

            detail="Questionnaire not found."

        )

    return questionnaire


# ======================================================
# Update Questionnaire
# ======================================================     

@app.put("/questionnaire_update_answers/{participant_id}")
def questionnaire_update_answers(

    participant_id: int,

    data: QuestionnaireSchema,

    db: Session = Depends(get_db)

):

    questionnaire = db.query(Questionnaire).filter(

        Questionnaire.participant_id == participant_id

    ).first()

    if not questionnaire:

        raise HTTPException(

            status_code=404,

            detail="Questionnaire not found."

        )

    questionnaire.camp_attendance = data.camp_attendance
    questionnaire.leadership_position = data.leadership_position
    questionnaire.church_involvement = data.church_involvement
    questionnaire.primary_strength = data.primary_strength
    questionnaire.ministry_skill = data.ministry_skill
    questionnaire.salvation_assurance = data.salvation_assurance
    questionnaire.daily_devotion = data.daily_devotion
    questionnaire.ministry_involvement = data.ministry_involvement
    questionnaire.sermon_notes = data.sermon_notes
    questionnaire.small_group = data.small_group
    questionnaire.gospel_sharing = data.gospel_sharing
    questionnaire.temptation_response = data.temptation_response
    questionnaire.updated_at = datetime.datetime.now()

    db.commit()

    return {

        "message":"Questionnaire updated successfully."

    }
    
    

# ======================================================
# Accept Rules
# ======================================================    

@app.post("/rules_accept_event_agreement")
def rules_accept_event_agreement(

    data: EventRulesAgreementSchema,

    db: Session = Depends(get_db)

):

    participant = db.query(Participant).filter(

        Participant.id == data.participant_id,

        Participant.is_archived == 0

    ).first()

    if not participant:

        raise HTTPException(

            status_code=404,

            detail="Participant not found."

        )

    agreement = db.query(EventRulesAgreement).filter(

        EventRulesAgreement.participant_id == data.participant_id

    ).first()

    if agreement:

        agreement.agreed = data.agreed
        agreement.agreed_at = datetime.datetime.now()

    else:

        agreement = EventRulesAgreement(

            participant_id=data.participant_id,

            agreed=data.agreed,

            agreed_at=datetime.datetime.now() if data.agreed else None

        )

        db.add(agreement)

    db.commit()

    db.refresh(agreement)

    return {

        "message":"Rules agreement saved successfully.",

        "agreed":bool(agreement.agreed)

    }
    
      
# ======================================================
# View Agreement
# ======================================================  

@app.get("/rules_view_event_agreement/{participant_id}")
def rules_view_event_agreement(

    participant_id:int,

    db:Session=Depends(get_db)

):

    agreement=db.query(EventRulesAgreement).filter(

        EventRulesAgreement.participant_id==participant_id

    ).first()

    if not agreement:

        raise HTTPException(

            status_code=404,

            detail="Agreement not found."

        )

    return agreement
    
    
# ======================================================
# COMPLETE REGISTRATION VALIDATION
# ======================================================

@app.post("/registration_complete_registration")
def registration_complete_registration(

    participant_id: int,

    db: Session = Depends(get_db)

):

    # ======================================================
    # CHECK PARTICIPANT
    # ======================================================

    participant = db.query(Participant).filter(

        Participant.id == participant_id,

        Participant.is_archived == 0

    ).first()

    if not participant:

        raise HTTPException(

            status_code=404,

            detail="Participant not found."

        )

    # ======================================================
    # PREVENT DUPLICATE COMPLETION
    # ======================================================

    if participant.registration_status == "Completed":

        raise HTTPException(

            status_code=400,

            detail="Participant registration is already completed."

        )

    # ======================================================
    # CHECK QUESTIONNAIRE
    # ======================================================

    questionnaire = db.query(Questionnaire).filter(

        Questionnaire.participant_id == participant_id

    ).first()

    if not questionnaire:

        raise HTTPException(

            status_code=400,

            detail="Questionnaire has not been completed."

        )

    # ======================================================
    # CHECK RULES AGREEMENT
    # ======================================================

    agreement = registration_rules_validation(

        db,

        participant_id

    )

    if not agreement:

        raise HTTPException(

            status_code=400,

            detail="Participant must accept the Event Rules & Regulations."

        )

    # ======================================================
    # GET EVENT
    # ======================================================

    event = db.query(Event).filter(

        Event.id == participant.event_id,

        Event.is_archived == 0

    ).first()

    if not event:

        raise HTTPException(

            status_code=404,

            detail="Event not found."

        )

    # ======================================================
    # CALCULATE SCORES
    # ======================================================

    influence_score = influence_score_calculator(

        questionnaire

    )

    spiritual_score = spiritual_score_calculator(

        questionnaire

    )

    creative_status = creative_identifier(

        questionnaire

    )

    participant_tier = tier_assignment(

        influence_score,

        spiritual_score,

        creative_status

    )

    # ======================================================
    # SAVE / UPDATE EVALUATION
    # ======================================================

    evaluation = db.query(ParticipantEvaluation).filter(

        ParticipantEvaluation.participant_id == participant_id

    ).first()

    if evaluation:

        evaluation.influence_score = influence_score

        evaluation.spiritual_score = spiritual_score

        evaluation.creative_status = creative_status

        evaluation.participant_tier = participant_tier

        evaluation.updated_at = datetime.datetime.now()

    else:

        evaluation = ParticipantEvaluation(

            participant_id=participant_id,

            influence_score=influence_score,

            spiritual_score=spiritual_score,

            creative_status=creative_status,

            participant_tier=participant_tier

        )

        db.add(evaluation)

    # ======================================================
    # UPDATE PARTICIPANT STATUS
    # ======================================================

    participant.registration_status = "Completed"

    participant.updated_at = datetime.datetime.now()

    db.commit()

    db.refresh(participant)

    db.refresh(evaluation)

    # ======================================================
    # RETURN COMPLETE SUMMARY
    # ======================================================

    return {

        "message":
            "Registration completed successfully.",

        "participant": {

            "participant_id":
                participant.id,

            "registration_number":
                participant.registration_number,

            "fullname":
                f"{participant.fname} "
                f"{participant.mname or ''} "
                f"{participant.lname}"
                .replace("  ", " ")
                .strip(),

            "registration_age":
                participant.registration_age,

            "registration_date":
                participant.registration_date,

            "registration_phase":
                participant.registration_phase,

            "registration_status":
                participant.registration_status

        },

        "event": {

            "event_id":
                event.id,

            "event_name":
                event.event_name,

            "registration_start":
                event.registration_start,

            "registration_end":
                event.registration_end,

            "kickoff_date":
                event.kickoff_date,

            "wrapup_date":
                event.wrapup_date

        },

        "evaluation": {

            "influence_score":
                evaluation.influence_score,

            "spiritual_score":
                evaluation.spiritual_score,

            "creative_status":
                evaluation.creative_status,

            "participant_tier":
                evaluation.participant_tier

        },

        "completed_at":
            participant.updated_at

    }



















# ======================================================
# VIEW PARTICIPANT PAYMENT STATUS
# ======================================================

@app.get("/payment_status/{participant_id}")
def payment_status(
    participant_id: int,
    db: Session = Depends(get_db)
):

    print("=" * 70)
    print("PAYMENT STATUS CHECK")
    print("Participant ID:", participant_id)
    print("=" * 70)

    # ==================================================
    # 1. FIND PARTICIPANT
    # ==================================================

    participant = (
        db.query(Participant)
        .filter(
            Participant.id == participant_id,
            Participant.is_archived == 0
        )
        .first()
    )

    if not participant:

        raise HTTPException(
            status_code=404,
            detail="Participant not found."
        )

    # ==================================================
    # 2. FULL NAME
    # ==================================================

    fullname = " ".join(
        part
        for part in [
            participant.fname,
            participant.mname,
            participant.lname
        ]
        if part and str(part).strip()
    ).strip()

    # ==================================================
    # 3. ACTIVE REGISTRATION ITEMS
    # ==================================================

    registration_items = (
        db.query(RegistrationItem)
        .filter(
            RegistrationItem.is_active == True
        )
        .all()
    )

    # ==================================================
    # 4. FIND T-SHIRT
    # ==================================================

    tshirt_item = next(
        (
            item
            for item in registration_items
            if item.item_name
            and item.item_name.strip().lower()
            == "t-shirt"
        ),
        None
    )

    # ==================================================
    # 5. FIND LANYARD
    # ==================================================

    lanyard_item = next(
        (
            item
            for item in registration_items
            if item.item_name
            and item.item_name.strip().lower()
            == "lanyard"
        ),
        None
    )

    # ==================================================
    # 6. PRICES
    # ==================================================

    tshirt_price = (
        tshirt_item.price
        if tshirt_item
        else 0
    )

    lanyard_price = (
        lanyard_item.price
        if lanyard_item
        else 0
    )

    # ==================================================
    # 7. GET ALL PAYMENTS
    # ==================================================

    payments = (
        db.query(Payment)
        .filter(
            Payment.participant_id ==
            participant.id
        )
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    # ==================================================
    # 8. SUCCESSFUL PAYMENT STATUSES
    # ==================================================

    successful_statuses = {
        "paid",
        "success",
        "succeeded",
        "completed"
    }

    # ==================================================
    # 9. CHECK T-SHIRT PAYMENT
    # ==================================================

    tshirt_paid = any(
        bool(
            getattr(
                p,
                "tshirt_selected",
                False
            )
        )
        and
        str(
            getattr(
                p,
                "status",
                ""
            )
            or ""
        ).strip().lower()
        in successful_statuses

        for p in payments
    )

    # ==================================================
    # 10. CHECK LANYARD PAYMENT
    # ==================================================

    lanyard_paid = any(
        bool(
            getattr(
                p,
                "lanyard_selected",
                False
            )
        )
        and
        str(
            getattr(
                p,
                "status",
                ""
            )
            or ""
        ).strip().lower()
        in successful_statuses

        for p in payments
    )

    # ==================================================
    # 11. FALLBACK TO PARTICIPANT ITEM STATUS
    # ==================================================

    participant_tshirt_status = str(
        getattr(
            participant,
            "tshirt_status",
            ""
        )
        or ""
    ).strip().lower()

    participant_lanyard_status = str(
        getattr(
            participant,
            "lanyard_status",
            ""
        )
        or ""
    ).strip().lower()

    if participant_tshirt_status == "paid":

        tshirt_paid = True

    if participant_lanyard_status == "paid":

        lanyard_paid = True

    # ==================================================
    # 12. UPDATE ITEM STATUS
    # ==================================================

    if hasattr(
        participant,
        "tshirt_status"
    ):

        participant.tshirt_status = (
            "Paid"
            if tshirt_paid
            else "Unpaid"
        )

    if hasattr(
        participant,
        "lanyard_status"
    ):

        participant.lanyard_status = (
            "Paid"
            if lanyard_paid
            else "Unpaid"
        )

    # ==================================================
    # 13. MANDATORY PAYMENT STATUS
    #
    # IMPORTANT:
    #
    # The Lanyard is mandatory.
    #
    # Therefore:
    #
    #     Lanyard Paid = mandatory payment complete
    #
    # The T-shirt does NOT affect this.
    # ==================================================

    mandatory_payment_complete = (
        lanyard_paid
        if lanyard_item
        else True
    )

    # ==================================================
    # 14. REGISTRATION STATUS
    # ==================================================

    if mandatory_payment_complete:

        if hasattr(
            participant,
            "registration_status"
        ):

            participant.registration_status = (
                "Confirmed"
            )

    # ==================================================
    # 15. UPDATED TIMESTAMP
    # ==================================================

    if hasattr(
        participant,
        "updated_at"
    ):

        participant.updated_at = (
            datetime.datetime.now()
        )

    db.commit()

    # ==================================================
    # 16. PAID ITEMS
    # ==================================================

    paid_items = []

    if tshirt_paid:

        paid_items.append(
            "T-Shirt"
        )

    if lanyard_paid:

        paid_items.append(
            "Lanyard"
        )

    # ==================================================
    # 17. REQUESTED ITEMS
    # ==================================================

    requested_items = []

    for p in payments:

        if bool(
            getattr(
                p,
                "tshirt_selected",
                False
            )
        ):

            requested_items.append(
                "T-Shirt"
            )

        if bool(
            getattr(
                p,
                "lanyard_selected",
                False
            )
        ):

            requested_items.append(
                "Lanyard"
            )

    requested_items = list(
        dict.fromkeys(
            requested_items
        )
    )

    # ==================================================
    # 18. ALL REQUESTED ITEMS PAID
    #
    # This is NOT the same as mandatory payment complete.
    #
    # Example:
    #
    # Lanyard = Paid
    # T-Shirt  = Unpaid
    #
    # mandatory_payment_complete = True
    # all_items_paid = False
    # ==================================================

    all_items_paid = (
        len(requested_items) > 0
        and
        all(
            item in paid_items
            for item in requested_items
        )
    )

    # ==================================================
    # 19. PAYMENT SUCCESS
    #
    # IMPORTANT:
    #
    # Payment success for registration is based on
    # the mandatory Lanyard.
    #
    # T-shirt is optional.
    # ==================================================

    payment_success = (
        mandatory_payment_complete
    )

    # ==================================================
    # 20. REGISTRATION STATUS
    # ==================================================

    registration_status = getattr(
        participant,
        "registration_status",
        None
    )

    # ==================================================
    # 21. DEBUG LOGGING
    # ==================================================

    print(
        "Participant T-Shirt Status:",
        getattr(
            participant,
            "tshirt_status",
            None
        )
    )

    print(
        "Participant Lanyard Status:",
        getattr(
            participant,
            "lanyard_status",
            None
        )
    )

    print(
        "T-Shirt Paid:",
        tshirt_paid
    )

    print(
        "Lanyard Paid:",
        lanyard_paid
    )

    print(
        "Mandatory Payment Complete:",
        mandatory_payment_complete
    )

    print(
        "Payment Success:",
        payment_success
    )

    print(
        "All Items Paid:",
        all_items_paid
    )

    print(
        "Registration Status:",
        registration_status
    )

    print("=" * 70)

    # ==================================================
    # 22. RETURN RESPONSE
    # ==================================================

    return {

        # ==================================================
        # PARTICIPANT
        # ==================================================

        "participant_id":
            participant.id,

        "registration_number":
            participant.registration_number,

        "fullname":
            fullname,

        "participant_type":
            participant.participant_type,

        # ==================================================
        # MAIN PAYMENT FLAGS
        # ==================================================

        # Mandatory Lanyard payment is complete.
        "mandatory_payment_complete":
            mandatory_payment_complete,

        # Registration payment is successful when
        # the mandatory Lanyard is paid.
        "payment_success":
            payment_success,

        # True only when every requested item is paid.
        "all_items_paid":
            all_items_paid,

        "paid_items":
            paid_items,

        "requested_items":
            requested_items,

        # ==================================================
        # EXPLICIT LANYARD FLAG
        # ==================================================

        "lanyard_paid":
            lanyard_paid,

        # ==================================================
        # EXPLICIT T-SHIRT FLAG
        # ==================================================

        "tshirt_paid":
            tshirt_paid,

        # ==================================================
        # T-SHIRT
        # ==================================================

        "tshirt": {

            "item_id":
                tshirt_item.id
                if tshirt_item
                else None,

            "item_name":
                tshirt_item.item_name
                if tshirt_item
                else "T-Shirt",

            "price":
                tshirt_price,

            "price_display":
                f"₱{tshirt_price / 100:,.2f}",

            "status":
                "Paid"
                if tshirt_paid
                else "Unpaid",

            "paid":
                tshirt_paid

        },

        # ==================================================
        # LANYARD
        # ==================================================

        "lanyard": {

            "item_id":
                lanyard_item.id
                if lanyard_item
                else None,

            "item_name":
                lanyard_item.item_name
                if lanyard_item
                else "Lanyard",

            "price":
                lanyard_price,

            "price_display":
                f"₱{lanyard_price / 100:,.2f}",

            "status":
                "Paid"
                if lanyard_paid
                else "Unpaid",

            "paid":
                lanyard_paid

        },

        # ==================================================
        # PARTICIPANT ITEM STATUS
        # ==================================================

        "tshirt_status":
            getattr(
                participant,
                "tshirt_status",
                None
            ),

        "lanyard_status":
            getattr(
                participant,
                "lanyard_status",
                None
            ),

        # ==================================================
        # REGISTRATION STATUS
        # ==================================================

        "registration_status":
            registration_status,

        # ==================================================
        # PAYMENT HISTORY
        # ==================================================

        "payments": [

            {

                "payment_id":
                    p.id,

                "amount":
                    p.amount,

                "amount_display":
                    f"₱{p.amount / 100:,.2f}",

                "status":
                    p.status,

                "tshirt_selected":
                    bool(
                        getattr(
                            p,
                            "tshirt_selected",
                            False
                        )
                    ),

                "lanyard_selected":
                    bool(
                        getattr(
                            p,
                            "lanyard_selected",
                            False
                        )
                    ),

                "tshirt_size":
                    getattr(
                        p,
                        "tshirt_size",
                        None
                    ),

                "checkout_url":
                    getattr(
                        p,
                        "checkout_url",
                        None
                    ),

                "paymongo_reference":
                    getattr(
                        p,
                        "paymongo_reference",
                        None
                    ),

                "paymongo_payment_id":
                    getattr(
                        p,
                        "paymongo_payment_id",
                        None
                    ),

                "paymongo_link_id":
                    getattr(
                        p,
                        "paymongo_link_id",
                        None
                    ),

                "created_at":
                    p.created_at,

                "paid_at":
                    getattr(
                        p,
                        "paid_at",
                        None
                    )

            }

            for p in payments

        ]
    }




    

































# ======================================================
# COMPLETE ONLINE REGISTRATION
# ======================================================

@app.post("/registration_submit_all")
def registration_submit_all(
    data: OnlineRegistrationSchema,
    db: Session = Depends(get_db)
):

    try:

        # ==================================================
        # CHECK EVENT
        # ==================================================

        event = db.query(Event).filter(
            Event.id == data.participant.event_id,
            Event.is_archived == 0
        ).first()

        if not event:

            raise HTTPException(
                status_code=404,
                detail="Event not found."
            )

        # ==================================================
        # CHECK PARTICIPANT TYPE
        # ==================================================

        allowed_participant_types = [
            "Regular Participants",
            "Finding Sponsor"
        ]

        if (
            data.participant.participant_type
            not in allowed_participant_types
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid participant type."
            )

        # ==================================================
        # CHECK REGISTRATION PERIOD
        # ==================================================

        today = datetime.date.today()

        if today < event.registration_start:

            raise HTTPException(
                status_code=400,
                detail="Event registration has not started yet."
            )

        if today > event.kickoff_date:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Registration is already closed "
                    "because the event has started."
                )
            )

        # ==================================================
        # CHECK RULES AGREEMENT
        # ==================================================

        if not data.rules_agreed:

            raise HTTPException(
                status_code=400,
                detail=(
                    "You must accept the "
                    "Event Rules & Regulations."
                )
            )

        # ==================================================
        # CHECK DATA CONFIDENTIALITY
        # ==================================================

        if not data.confidentiality_agreed:

            raise HTTPException(
                status_code=400,
                detail=(
                    "You must agree to the "
                    "Data Confidentiality clause."
                )
            )

        # ==================================================
        # VALIDATE QUESTIONNAIRE
        # ==================================================

        questionnaire_fields = [

            "camp_attendance",
            "leadership_position",
            "church_involvement",
            "primary_strength",
            "ministry_skill",
            "salvation_assurance",
            "daily_devotion",
            "ministry_involvement",
            "sermon_notes",
            "small_group",
            "gospel_sharing",
            "temptation_response"

        ]

        for field in questionnaire_fields:

            value = data.questionnaire.get(field)

            if not value or not str(value).strip():

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Questionnaire field "
                        f"'{field}' is required."
                    )
                )

        # ==================================================
        # DUPLICATE VALIDATION
        # ==================================================

        duplicate = registration_duplicate_validation(

            db,

            data.participant.event_id,

            data.participant.fname,

            data.participant.mname,

            data.participant.lname,

            data.participant.birthdate

        )

        if duplicate:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Participant is already registered "
                    "for this event."
                )
            )

        # ==================================================
        # REGISTRATION PHASE
        # ==================================================

        registration_phase = (
            registration_phase_validation(event)
        )

        # ==================================================
        # CALCULATE AGE
        # ==================================================

        registration_age = (
            calculate_registration_age(
                data.participant.birthdate
            )
        )

        # ==================================================
        # GENERATE REGISTRATION NUMBER
        # ==================================================

        registration_number = (
            registration_number_generator(
                db,
                event
            )
        )

        # ==================================================
        # CREATE PARTICIPANT
        # ==================================================

        participant = Participant(

            event_id=event.id,

            event_name=event.event_name,

            registration_start=event.registration_start,

            registration_end=event.registration_end,

            kickoff_date=event.kickoff_date,

            wrapup_date=event.wrapup_date,

            registration_number=registration_number,

            registration_date=today,

            registration_phase=registration_phase,

            registration_status="Pending",

            participant_type=(
                data.participant.participant_type
            ),

            registration_age=registration_age,

            fname=data.participant.fname,

            mname=data.participant.mname,

            lname=data.participant.lname,

            sex=data.participant.sex,

            birthdate=data.participant.birthdate,

            address=data.participant.address,

            contact_number=data.participant.contact_number,

            emergency_contact=data.participant.emergency_contact,

            email=str(data.participant.email),

            local_church=data.participant.local_church,

            sector=data.participant.sector,

            tshirt_status="Unpaid",

            lanyard_status="Unpaid",

            is_archived=0
        )

        db.add(participant)

        # ==================================================
        # FLUSH PARTICIPANT
        # ==================================================

        db.flush()

        # ==================================================
        # CREATE QUESTIONNAIRE
        # ==================================================

        questionnaire = Questionnaire(

            participant_id=participant.id,

            camp_attendance=(
                data.questionnaire[
                    "camp_attendance"
                ]
            ),

            leadership_position=(
                data.questionnaire[
                    "leadership_position"
                ]
            ),

            church_involvement=(
                data.questionnaire[
                    "church_involvement"
                ]
            ),

            primary_strength=(
                data.questionnaire[
                    "primary_strength"
                ]
            ),

            ministry_skill=(
                data.questionnaire[
                    "ministry_skill"
                ]
            ),

            salvation_assurance=(
                data.questionnaire[
                    "salvation_assurance"
                ]
            ),

            daily_devotion=(
                data.questionnaire[
                    "daily_devotion"
                ]
            ),

            ministry_involvement=(
                data.questionnaire[
                    "ministry_involvement"
                ]
            ),

            sermon_notes=(
                data.questionnaire[
                    "sermon_notes"
                ]
            ),

            small_group=(
                data.questionnaire[
                    "small_group"
                ]
            ),

            gospel_sharing=(
                data.questionnaire[
                    "gospel_sharing"
                ]
            ),

            temptation_response=(
                data.questionnaire[
                    "temptation_response"
                ]
            )
        )

        db.add(questionnaire)

        # ==================================================
        # CREATE RULES AGREEMENT
        # ==================================================

        agreement = EventRulesAgreement(

            participant_id=participant.id,

            agreed=1,

            agreed_at=datetime.datetime.now()

        )

        db.add(agreement)

        # ==================================================
        # GET REGISTRATION ITEMS FROM DATABASE
        # ==================================================

        registration_items = (
            db.query(RegistrationItem)
            .filter(
                RegistrationItem.is_active == True
            )
            .order_by(
                RegistrationItem.id.asc()
            )
            .all()
        )

        # ==================================================
        # PREPARE REQUIRED / OPTIONAL ITEMS
        # ==================================================

        required_items = []

        optional_items = []

        for item in registration_items:

            item_data = {

                "id":
                    item.id,

                "name":
                    item.item_name,

                "price":
                    item.price

            }

            if getattr(item, "is_required", False):

                required_items.append(
                    item_data
                )

            else:

                optional_items.append(
                    item_data
                )

        # ==================================================
        # SAVE EVERYTHING
        # ==================================================

        db.commit()

        db.refresh(participant)

        db.refresh(questionnaire)

        db.refresh(agreement)

        # ==================================================
        # RESPONSE
        # ==================================================

        return {

            "message":
                "Registration submitted successfully.",

            "participant": {

                "participant_id":
                    participant.id,

                "registration_number":
                    participant.registration_number,

                "fullname":
                    (
                        f"{participant.fname} "
                        f"{participant.mname or ''} "
                        f"{participant.lname}"
                    ).replace(
                        "  ",
                        " "
                    ).strip(),

                "registration_status":
                    participant.registration_status,

                "registration_phase":
                    participant.registration_phase,

                "event_id":
                    participant.event_id,

                "event_name":
                    participant.event_name

            },

            "payment_required":
                len(required_items) > 0,

            "required_items":
                required_items,

            "optional_items":
                optional_items

        }

    except HTTPException:

        db.rollback()

        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=(
                "Registration could not be completed: "
                f"{str(e)}"
            )

        )



    
# ======================================================
# REGISTRATION SUMMARY DASHBOARD
# ======================================================  

@app.get("/dashboard_registration_summary")
def dashboard_registration_summary(

    db: Session = Depends(get_db)

):

    total_participants = db.query(Participant).filter(

        Participant.is_archived == 0

    ).count()

    pending = db.query(Participant).filter(

        Participant.registration_status == "Pending",

        Participant.is_archived == 0

    ).count()

    completed = db.query(Participant).filter(

        Participant.registration_status == "Completed",

        Participant.is_archived == 0

    ).count()

    early_bird = db.query(Participant).filter(

        Participant.registration_phase == "Early-bird",

        Participant.is_archived == 0

    ).count()

    walk_in = db.query(Participant).filter(

        Participant.registration_phase == "Walk-in",

        Participant.is_archived == 0

    ).count()

    archived = db.query(Participant).filter(

        Participant.is_archived == 1

    ).count()

    return {

        "total_participants": total_participants,

        "pending_registration": pending,

        "completed_registration": completed,

        "early_bird": early_bird,

        "walk_in": walk_in,

        "archived_participants": archived

    }


# ======================================================
# EVENT SUMMARY DASHBOARD
# ======================================================  

@app.get("/dashboard_event_summary")
def dashboard_event_summary(

    db: Session = Depends(get_db)

):

    total_events = db.query(Event).filter(

        Event.is_archived == 0

    ).count()

    archived_events = db.query(Event).filter(

        Event.is_archived == 1

    ).count()

    today = datetime.date.today()

    active_events = db.query(Event).filter(

        Event.is_archived == 0,

        Event.registration_start <= today,

        Event.wrapup_date >= today

    ).count()

    upcoming_events = db.query(Event).filter(

        Event.is_archived == 0,

        Event.registration_start > today

    ).count()

    finished_events = db.query(Event).filter(

        Event.is_archived == 0,

        Event.wrapup_date < today

    ).count()

    return {

        "total_events": total_events,

        "active_events": active_events,

        "upcoming_events": upcoming_events,

        "finished_events": finished_events,

        "archived_events": archived_events

    }


# ======================================================
# RECALCULATE PARTICIPANT SCORES
# ======================================================   

@app.post("/questionnaire_recalculate_scores")
def questionnaire_recalculate_scores(

    participant_id: int,

    db: Session = Depends(get_db)

):

    questionnaire = db.query(Questionnaire).filter(

        Questionnaire.participant_id == participant_id

    ).first()

    if not questionnaire:

        raise HTTPException(

            status_code=404,

            detail="Questionnaire not found."

        )

    influence_score = influence_score_calculator(

        questionnaire

    )

    spiritual_score = spiritual_score_calculator(

        questionnaire

    )

    creative_status = creative_identifier(

        questionnaire

    )

    participant_tier = tier_assignment(

        influence_score,

        spiritual_score,

        creative_status

    )

    evaluation = db.query(

        ParticipantEvaluation

    ).filter(

        ParticipantEvaluation.participant_id == participant_id

    ).first()

    if evaluation:

        evaluation.influence_score = influence_score

        evaluation.spiritual_score = spiritual_score

        evaluation.creative_status = creative_status

        evaluation.participant_tier = participant_tier

        evaluation.updated_at = datetime.datetime.now()

    else:

        evaluation = ParticipantEvaluation(

            participant_id=participant_id,

            influence_score=influence_score,

            spiritual_score=spiritual_score,

            creative_status=creative_status,

            participant_tier=participant_tier

        )

        db.add(evaluation)

    db.commit()

    db.refresh(evaluation)

    return {

        "message": "Participant evaluation recalculated successfully.",

        "participant_id": participant_id,

        "participant_tier": evaluation.participant_tier,

        "spiritual_score": evaluation.spiritual_score,

        "influence_score": evaluation.influence_score,

        "creative_status": evaluation.creative_status

    }

# ======================================================
# VIEW PARTICIPANT EVALUATION
# ======================================================      

@app.get("/evaluation_view_participant_evaluation")
def evaluation_view_participant_evaluation(

    participant_id: int,

    db: Session = Depends(get_db)

):

    participant = db.query(Participant).filter(

        Participant.id == participant_id

    ).first()

    if not participant:

        raise HTTPException(

            status_code=404,

            detail="Participant not found."

        )

    evaluation = db.query(

        ParticipantEvaluation

    ).filter(

        ParticipantEvaluation.participant_id == participant_id

    ).first()

    if not evaluation:

        raise HTTPException(

            status_code=404,

            detail="Participant has not yet been evaluated."

        )

    return {

        "participant": {

            "participant_id": participant.id,

            "registration_number": participant.registration_number,

            "fullname": f"{participant.fname} {participant.mname} {participant.lname}",

            "event_name": participant.event_name,

            "registration_phase": participant.registration_phase,

            "registration_status": participant.registration_status

        },

        "evaluation": {

            "participant_tier": evaluation.participant_tier,

            "spiritual_score": evaluation.spiritual_score,

            "influence_score": evaluation.influence_score,

            "creative_status": evaluation.creative_status

        }

    }
    

# ======================================================
# DASHBOARD TOTALS
# ======================================================

@app.get("/dashboard_totals")
def dashboard_totals(
    db: Session = Depends(get_db)
):
    """
    Return live totals used by the Admin and Registration Team dashboards.
    Only non-archived records are included.
    """

    total_participants = db.query(Participant).filter(
        Participant.is_archived == 0
    ).count()

    total_staff = db.query(Staff).filter(
        Staff.is_archived == 0
    ).count()

    total_chaperones = db.query(Chaperone).filter(
        Chaperone.is_archived == 0
    ).count()

    total_events = db.query(Event).filter(
        Event.is_archived == 0
    ).count()

    return {
        "participants": total_participants,
        "staff": total_staff,
        "chaperones": total_chaperones,
        "events": total_events
    }


# ======================================================
# ACTIVE EVENT PARTICIPANT COUNT
# ======================================================

@app.get("/event_participant_count")
def event_participant_count(

    db: Session = Depends(get_db)

):

    events = db.query(Event).filter(

        Event.is_archived == 0

    ).all()

    result = []

    for event in events:

        participant_count = db.query(Participant).filter(

            Participant.event_id == event.id,

            Participant.is_archived == 0

        ).count()

        result.append({

            "event_id": event.id,

            "event_name": event.event_name,

            "participant_count": participant_count

        })

    return {

        "events": result

    }    
    
    






# ======================================================
# CREATE PAYMONGO PAYMENT
# SUPPORTS SINGLE + BULK PARTICIPANTS
# ======================================================

@app.post("/create_payment")
def create_payment(
    data: PaymentCreateSchema,
    db: Session = Depends(get_db)
):
    print()
    print("=" * 70)
    print("CREATE PAYMENT REQUEST")
    print("=" * 70)

    # ==================================================
    # DETERMINE PARTICIPANT IDS
    # ==================================================

    participant_ids = []

    if data.participant_ids:
        for pid in data.participant_ids:
            try:
                participant_id = int(pid)

                if participant_id > 0:
                    participant_ids.append(participant_id)

            except (ValueError, TypeError):
                continue

    elif data.participant_id is not None:
        try:
            participant_id = int(data.participant_id)

            if participant_id > 0:
                participant_ids = [participant_id]

        except (ValueError, TypeError):
            participant_ids = []

    # ==================================================
    # VALIDATE PARTICIPANTS
    # ==================================================

    if not participant_ids:
        raise HTTPException(
            status_code=400,
            detail="At least one participant is required for payment."
        )

    # Remove duplicates but preserve order
    participant_ids = list(dict.fromkeys(participant_ids))

    is_bulk_payment = (
        len(participant_ids) > 1
        or bool(getattr(data, "bulk", False))
    )

    # ==================================================
    # LOAD PARTICIPANTS
    # ==================================================

    participants = (
        db.query(Participant)
        .filter(
            Participant.id.in_(participant_ids),
            Participant.is_archived == 0
        )
        .all()
    )

    found_ids = {
        participant.id
        for participant in participants
    }

    missing_ids = [
        pid
        for pid in participant_ids
        if pid not in found_ids
    ]

    if missing_ids:
        db.rollback()

        raise HTTPException(
            status_code=404,
            detail={
                "message": "One or more participants were not found.",
                "missing_participant_ids": missing_ids
            }
        )

    # Preserve requested order
    participant_map = {
        participant.id: participant
        for participant in participants
    }

    participants = [
        participant_map[pid]
        for pid in participant_ids
    ]

    # ==================================================
    # NORMALIZE BOOLEAN
    # ==================================================

    def normalize_bool(value):

        if isinstance(value, bool):
            return value

        if value is None:
            return False

        if isinstance(value, int):
            return value != 0

        if isinstance(value, str):
            return value.strip().lower() in {
                "true",
                "1",
                "yes",
                "on",
                "selected",
                "checked"
            }

        return bool(value)

    # ==================================================
    # GLOBAL REQUEST ITEM VALUES
    # ==================================================

    tshirt_value = getattr(data, "tshirt", None)

    if tshirt_value is None:
        tshirt_value = getattr(
            data,
            "tshirt_selected",
            False
        )

    lanyard_value = getattr(data, "lanyard", None)

    if lanyard_value is None:
        lanyard_value = getattr(
            data,
            "lanyard_selected",
            False
        )

    tshirt_requested = normalize_bool(
        tshirt_value
    )

    lanyard_requested = normalize_bool(
        lanyard_value
    )

    # ==================================================
    # VALIDATE ITEM SELECTION
    # ==================================================

    if not tshirt_requested and not lanyard_requested:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="Please select at least one registration item."
        )

    # ==================================================
    # T-SHIRT SIZE
    # ==================================================

    tshirt_size = None

    if tshirt_requested:

        requested_size = getattr(
            data,
            "tshirt_size",
            None
        )

        if not requested_size:
            db.rollback()

            raise HTTPException(
                status_code=400,
                detail="Please select a T-shirt size."
            )

        tshirt_size = (
            str(requested_size)
            .strip()
            .upper()
        )

        allowed_sizes = {
            "M",
            "L",
            "XL"
        }

        if tshirt_size not in allowed_sizes:
            db.rollback()

            raise HTTPException(
                status_code=400,
                detail="Invalid T-shirt size. Please select M, L, or XL."
            )

    # ==================================================
    # PRICES
    # STORED IN CENTAVOS
    #
    # ₱350 = 35000
    # ₱90  = 9000
    # ==================================================

    TSHIRT_PRICE = 35000
    LANYARD_PRICE = 9000

    successful_statuses = {
        "paid",
        "success",
        "succeeded",
        "completed"
    }

    payment_rows = []
    total_amount = 0

    all_participant_items = []
    participant_payment_summary = []

    # ==================================================
    # PROCESS EACH PARTICIPANT
    # ==================================================

    for participant in participants:

        print()
        print("-" * 70)
        print(
            "PROCESSING PARTICIPANT:",
            participant.id
        )
        print(
            "Registration:",
            participant.registration_number
        )
        print("-" * 70)

        # ==================================================
        # LOAD EXISTING PAYMENTS
        # ==================================================

        payments = (
            db.query(Payment)
            .filter(
                Payment.participant_id ==
                participant.id
            )
            .order_by(
                Payment.created_at.desc()
            )
            .all()
        )

        # ==================================================
        # DETERMINE WHETHER T-SHIRT WAS ALREADY PAID
        # ==================================================

        tshirt_paid = False

        for payment in payments:

            payment_status = str(
                payment.status or ""
            ).strip().lower()

            if (
                bool(
                    getattr(
                        payment,
                        "tshirt_selected",
                        False
                    )
                )
                and
                payment_status in successful_statuses
            ):
                tshirt_paid = True
                break

        # ==================================================
        # DETERMINE WHETHER LANYARD WAS ALREADY PAID
        # ==================================================

        lanyard_paid = False

        for payment in payments:

            payment_status = str(
                payment.status or ""
            ).strip().lower()

            if (
                bool(
                    getattr(
                        payment,
                        "lanyard_selected",
                        False
                    )
                )
                and
                payment_status in successful_statuses
            ):
                lanyard_paid = True
                break

        # ==================================================
        # FALLBACK TO PARTICIPANT STATUS
        # ==================================================

        if not payments:

            existing_tshirt_status = str(
                getattr(
                    participant,
                    "tshirt_status",
                    ""
                ) or ""
            ).strip().lower()

            if existing_tshirt_status == "paid":
                tshirt_paid = True

            existing_lanyard_status = str(
                getattr(
                    participant,
                    "lanyard_status",
                    ""
                ) or ""
            ).strip().lower()

            if existing_lanyard_status == "paid":
                lanyard_paid = True

        # ==================================================
        # PARTICIPANT-SPECIFIC REQUEST
        # ==================================================

        participant_tshirt_requested = (
            tshirt_requested
        )

        participant_lanyard_requested = (
            lanyard_requested
        )

        # ==================================================
        # REMOVE ALREADY PAID T-SHIRT
        # ==================================================

        if (
            participant_tshirt_requested
            and tshirt_paid
        ):
            participant_tshirt_requested = False

        # ==================================================
        # REMOVE ALREADY PAID LANYARD
        # ==================================================

        if (
            participant_lanyard_requested
            and lanyard_paid
        ):
            participant_lanyard_requested = False

        # ==================================================
        # CALCULATE PARTICIPANT AMOUNT
        # ==================================================

        participant_amount = 0
        participant_items = []

        if participant_tshirt_requested:

            participant_amount += TSHIRT_PRICE

            participant_items.append(
                f"T-Shirt ({tshirt_size})"
            )

        if participant_lanyard_requested:

            participant_amount += LANYARD_PRICE

            participant_items.append(
                "Lanyard"
            )

        # ==================================================
        # NOTHING LEFT TO PAY
        # ==================================================

        if participant_amount <= 0:
            db.rollback()

            raise HTTPException(
                status_code=400,
                detail=(
                    "Participant "
                    f"{participant.registration_number} "
                    "has no remaining items to pay."
                )
            )

        # ==================================================
        # CHECK EXISTING PENDING PAYMENT
        # ==================================================

        existing_payment = (
            db.query(Payment)
            .filter(
                Payment.participant_id ==
                participant.id,

                Payment.status ==
                "Pending",

                Payment.tshirt_selected ==
                int(
                    participant_tshirt_requested
                ),

                Payment.lanyard_selected ==
                int(
                    participant_lanyard_requested
                )
            )
            .order_by(
                Payment.created_at.desc()
            )
            .first()
        )

        if existing_payment:

            if existing_payment.checkout_url:

                db.rollback()

                raise HTTPException(
                    status_code=400,
                    detail={
                        "message": (
                            "A pending payment already "
                            "exists for participant "
                            f"{participant.registration_number}."
                        ),

                        "participant_id":
                            participant.id,

                        "payment_id":
                            existing_payment.id,

                        "checkout_url":
                            existing_payment.checkout_url
                    }
                )

        # ==================================================
        # ADD TO TOTAL
        # ==================================================

        total_amount += participant_amount

        # ==================================================
        # FULL NAME
        # ==================================================

        fullname = (
            f"{participant.fname or ''} "
            f"{participant.mname or ''} "
            f"{participant.lname or ''}"
        ).strip()

        # ==================================================
        # PARTICIPANT DETAILS
        # ==================================================

        all_participant_items.append({
            "participant_id":
                participant.id,

            "registration_number":
                participant.registration_number,

            "fullname":
                fullname,

            "items":
                participant_items,

            "amount":
                participant_amount,

            "amount_display":
                f"₱{participant_amount / 100:,.2f}"
        })

        participant_payment_summary.append({
            "participant_id":
                participant.id,

            "registration_number":
                participant.registration_number,

            "tshirt_selected":
                int(
                    participant_tshirt_requested
                ),

            "lanyard_selected":
                int(
                    participant_lanyard_requested
                ),

            "tshirt_size":
                tshirt_size,

            "amount":
                participant_amount
        })

        # ==================================================
        # CREATE LOCAL PAYMENT ROW
        #
        # IMPORTANT:
        # These flags belong to THIS participant.
        # ==================================================

        payment = Payment(
            participant_id =
                participant.id,

            amount =
                participant_amount,

            currency =
                "PHP",

            status =
                "Pending",

            payment_type =
                "Participant",

            tshirt_selected =
                int(
                    participant_tshirt_requested
                ),

            lanyard_selected =
                int(
                    participant_lanyard_requested
                ),

            tshirt_size =
                tshirt_size
        )

        db.add(payment)

        payment_rows.append(
            payment
        )

    # ==================================================
    # VALIDATE TOTAL
    # ==================================================

    if total_amount <= 0:

        db.rollback()

        raise HTTPException(
            status_code=400,
            detail="There is no remaining amount to pay."
        )

    # ==================================================
    # FLUSH SO PAYMENT IDS EXIST
    # ==================================================

    try:

        db.flush()

    except Exception as e:

        db.rollback()

        print(
            "PAYMENT ROW FLUSH FAILED:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to create local payment records."
        )

    # ==================================================
    # CREATE INTERNAL BULK REFERENCE
    # ==================================================

    if is_bulk_payment:

        local_bulk_reference = (
            "CYF-BULK-"
            f"{uuid.uuid4().hex[:12].upper()}"
        )

    else:

        local_bulk_reference = (
            "CYF-SINGLE-"
            f"{uuid.uuid4().hex[:12].upper()}"
        )

    # ==================================================
    # EVENT NAME
    # ==================================================

    event_names = list(
        dict.fromkeys(
            participant.event_name
            for participant in participants
            if participant.event_name
        )
    )

    event_name = (
        event_names[0]
        if len(event_names) == 1
        else "Multiple Events"
    )

    # ==================================================
    # DESCRIPTION
    # ==================================================

    if is_bulk_payment:

        description = (
            "CYF Bulk Merchandise Payment - "
            f"{len(participants)} Participants"
        )

    else:

        description = (
            "CYF Merchandise Payment - "
            f"{participants[0].registration_number}"
        )

    # ==================================================
    # REMARKS
    # ==================================================

    participant_remarks = []

    for item in all_participant_items:

        participant_remarks.append(
            (
                f"{item['registration_number']} | "
                f"{item['fullname']} | "
                f"{', '.join(item['items'])} | "
                f"₱{item['amount'] / 100:,.2f}"
            )
        )

    remarks = (
        "CYF Registration Payment | "
        f"Participants: {len(participants)} | "
        f"Bulk Reference: {local_bulk_reference} | "
        f"{' || '.join(participant_remarks)}"
    )

    # ==================================================
    # PAYMONGO IDS FOR METADATA
    # ==================================================

    participant_ids_metadata = ",".join(
        str(pid)
        for pid in participant_ids
    )

    payment_ids_metadata = ",".join(
        str(payment.id)
        for payment in payment_rows
    )

    # ==================================================
    # PAYMONGO PAYMENT LINK
    # ==================================================

    url = (
        f"{PAYMONGO_API_URL}"
        "/v1/payment_links"
    )

    # ==================================================
    # PAYMONGO PAYLOAD
    # ==================================================

    payload = {

        "amount":
            total_amount,

        "currency":
            "PHP",

        "description":
            description,

        "remarks":
            remarks,

        "metadata": {

            # ------------------------------------------------
            # INTERNAL PAYMENT TYPE
            # ------------------------------------------------

            "payment_type":
                (
                    "bulk"
                    if is_bulk_payment
                    else "single"
                ),

            # ------------------------------------------------
            # INTERNAL REFERENCE
            # ------------------------------------------------

            "bulk_reference":
                local_bulk_reference,

            # ------------------------------------------------
            # PARTICIPANT COUNT
            # ------------------------------------------------

            "participant_count":
                str(len(participants)),

            # ------------------------------------------------
            # ALL PARTICIPANT IDS
            # ------------------------------------------------

            "participant_ids":
                participant_ids_metadata,

            # ------------------------------------------------
            # ALL LOCAL PAYMENT IDS
            #
            # THIS IS CRITICAL FOR BULK WEBHOOKS.
            # ------------------------------------------------

            "payment_ids":
                payment_ids_metadata,

            # ------------------------------------------------
            # EVENT
            # ------------------------------------------------

            "event_name":
                event_name,

            # ------------------------------------------------
            # GLOBAL REQUEST VALUES
            #
            # These are informational only.
            # The webhook MUST use the Payment row
            # for the actual participant-specific flags.
            # ------------------------------------------------

            "tshirt":
                str(
                    int(tshirt_requested)
                ),

            "lanyard":
                str(
                    int(lanyard_requested)
                ),

            "tshirt_size":
                tshirt_size or ""
        }
    }

    # ==================================================
    # IDEMPOTENCY KEY
    # ==================================================

    idempotency_key = (
        "cyf-payment-"
        f"{local_bulk_reference}-"
        f"{uuid.uuid4()}"
    )

    # ==================================================
    # CREATE PAYMONGO LINK
    # ==================================================

    try:

        response = requests.post(
            url,

            auth=(
                PAYMONGO_SECRET_KEY,
                ""
            ),

            headers={
                "Content-Type":
                    "application/json",

                "Accept":
                    "application/json",

                "Idempotency-Key":
                    idempotency_key
            },

            json=payload,

            timeout=30
        )

    except requests.RequestException as e:

        for payment in payment_rows:
            payment.status = "Failed"

        db.commit()

        print(
            "PAYMONGO CONNECTION ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "PayMongo connection failed: "
                f"{str(e)}"
            )
        )

    # ==================================================
    # PAYMONGO ERROR
    # ==================================================

    if not response.ok:

        for payment in payment_rows:
            payment.status = "Failed"

        db.commit()

        try:
            error_data = response.json()

        except Exception:
            error_data = {
                "error":
                    response.text
            }

        raise HTTPException(
            status_code=502,
            detail=error_data
        )

    # ==================================================
    # PARSE PAYMONGO RESPONSE
    # ==================================================

    try:

        paymongo_data = response.json()

    except Exception:

        for payment in payment_rows:
            payment.status = "Failed"

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "PayMongo returned an invalid JSON response."
            )
        )

    # ==================================================
    # LINK DATA
    # ==================================================

    link_data = paymongo_data.get(
        "data",
        {}
    )

    if not link_data:

        for payment in payment_rows:
            payment.status = "Failed"

        db.commit()

        raise HTTPException(
            status_code=502,
            detail={
                "message":
                    "PayMongo returned an empty data object.",

                "paymongo_response":
                    paymongo_data
            }
        )

    # ==================================================
    # LINK ID
    # ==================================================

    paymongo_link_id = link_data.get(
        "id"
    )

    # ==================================================
    # LINK ATTRIBUTES
    # ==================================================

    link_attributes = link_data.get(
        "attributes",
        {}
    )

    if not isinstance(
        link_attributes,
        dict
    ):
        link_attributes = {}

    # ==================================================
    # CHECKOUT URL
    # ==================================================

    checkout_url = (
        link_attributes.get(
            "checkout_url"
        )
        or
        link_attributes.get(
            "url"
        )
        or
        link_data.get(
            "checkout_url"
        )
        or
        link_data.get(
            "url"
        )
    )

    # ==================================================
    # PAYMONGO REFERENCE
    # ==================================================

    paymongo_reference = (
        link_attributes.get(
            "reference_number"
        )
        or
        link_data.get(
            "reference_number"
        )
    )

    # ==================================================
    # VALIDATE LINK ID
    # ==================================================

    if not paymongo_link_id:

        for payment in payment_rows:
            payment.status = "Failed"

        db.commit()

        raise HTTPException(
            status_code=502,
            detail={
                "message":
                    "PayMongo did not return a payment link ID.",

                "paymongo_response":
                    paymongo_data
            }
        )

    # ==================================================
    # VALIDATE CHECKOUT URL
    # ==================================================

    if not checkout_url:

        for payment in payment_rows:
            payment.status = "Failed"

        db.commit()

        raise HTTPException(
            status_code=502,
            detail={
                "message":
                    "PayMongo did not return a checkout URL.",

                "paymongo_response":
                    paymongo_data
            }
        )

    # ==================================================
    # SAVE PAYMONGO DATA TO EVERY LOCAL PAYMENT ROW
    #
    # BULK:
    #
    # Payment 101 -> Participant 27
    # Payment 102 -> Participant 28
    # Payment 103 -> Participant 29
    #
    # ALL share the SAME payment-link ID.
    # ==================================================

    for payment in payment_rows:

        if hasattr(
            payment,
            "paymongo_link_id"
        ):
            payment.paymongo_link_id = (
                paymongo_link_id
            )

        if hasattr(
            payment,
            "paymongo_reference"
        ):
            payment.paymongo_reference = (
                paymongo_reference
            )

        payment.checkout_url = (
            checkout_url
        )

        payment.status = "Pending"

    # ==================================================
    # COMMIT
    # ==================================================

    try:

        db.commit()

    except Exception as e:

        db.rollback()

        print(
            "PAYMENT COMMIT FAILED:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Payment was created but "
                "could not be saved locally."
            )
        )

    # ==================================================
    # REFRESH
    # ==================================================

    for payment in payment_rows:

        try:
            db.refresh(payment)

        except Exception as e:

            print(
                "Payment refresh failed:",
                repr(e)
            )

    # ==================================================
    # RETURN
    # ==================================================

    return {

        "message":
            (
                "Bulk payment link created successfully."
                if is_bulk_payment
                else
                "Payment link created successfully."
            ),

        "payment_type":
            (
                "bulk"
                if is_bulk_payment
                else "single"
            ),

        "participant_count":
            len(participants),

        "participant_ids":
            participant_ids,

        "participants":
            all_participant_items,

        "payment_ids":
            [
                payment.id
                for payment in payment_rows
            ],

        "participant_payment_summary":
            participant_payment_summary,

        "items":
            list(
                dict.fromkeys(
                    item
                    for participant_item
                    in all_participant_items
                    for item
                    in participant_item["items"]
                )
            ),

        "tshirt_selected":
            tshirt_requested,

        "lanyard_selected":
            lanyard_requested,

        "tshirt_size":
            tshirt_size,

        "amount":
            total_amount,

        "amount_display":
            f"₱{total_amount / 100:,.2f}",

        "paymongo_link_id":
            paymongo_link_id,

        "checkout_url":
            checkout_url,

        "paymongo_reference":
            paymongo_reference,

        "bulk_reference":
            local_bulk_reference
    }


















    
    

    
# ============================================================
# FINDING SPONSOR QUEUE PROCESSING LOGIC
# ============================================================
#
# This is the REAL sponsorship-processing logic.
#
# It can be called from:
#
# 1. POST /process_finding_sponsor_queue
# 2. PayMongo webhook
#
# DO NOT call the FastAPI endpoint internally.
#
# IMPORTANT:
#
# RegistrationItem.price
#     = STORED IN CENTAVOS
#
# CashDonationTotal.total_amount
#     = STORED IN PESOS
#
# Example:
#
# T-shirt:
#     35000 = ₱350.00
#
# Lanyard:
#     9000 = ₱90.00
#
# Required:
#     ₱350 + ₱90 = ₱440
#
# ============================================================


async def process_finding_sponsor_queue_logic(
    db: Session
):

    print("\n")
    print("=" * 70)
    print("FINDING SPONSOR QUEUE PROCESSING")
    print("=" * 70)

    # ========================================================
    # GET T-SHIRT PRICE
    # ========================================================

    tshirt_item = (
        db.query(
            RegistrationItem
        )
        .filter(
            RegistrationItem.item_name.ilike("T-Shirt"),
            RegistrationItem.is_active == True
        )
        .first()
    )

    if not tshirt_item:

        raise Exception(
            "T-shirt registration item was not found."
        )

    # ========================================================
    # GET LANYARD PRICE
    # ========================================================

    lanyard_item = (
        db.query(
            RegistrationItem
        )
        .filter(
            RegistrationItem.item_name.ilike("Lanyard"),
            RegistrationItem.is_active == True
        )
        .first()
    )

    if not lanyard_item:

        raise Exception(
            "Lanyard registration item was not found."
        )

    # ========================================================
    # GET PRICES
    #
    # RegistrationItem.price = CENTAVOS
    #
    # Example:
    #
    # 35000 = ₱350.00
    # 9000  = ₱90.00
    #
    # ========================================================

    try:

        tshirt_price_centavos = int(
            tshirt_item.price or 0
        )

    except (
        ValueError,
        TypeError
    ):

        tshirt_price_centavos = 0

    try:

        lanyard_price_centavos = int(
            lanyard_item.price or 0
        )

    except (
        ValueError,
        TypeError
    ):

        lanyard_price_centavos = 0

    # ========================================================
    # CONVERT CENTAVOS TO PESOS
    # ========================================================

    tshirt_price = (
        tshirt_price_centavos / 100
    )

    lanyard_price = (
        lanyard_price_centavos / 100
    )

    # ========================================================
    # REQUIRED SPONSORSHIP AMOUNT
    #
    # Stored/compared in PESOS because
    # CashDonationTotal.total_amount is in PESOS.
    # ========================================================

    required_amount = (
        tshirt_price +
        lanyard_price
    )

    if required_amount <= 0:

        raise Exception(
            "Merchandise prices must be greater than zero."
        )

    print(
        "T-shirt Price:",
        f"₱{tshirt_price:,.2f}"
    )

    print(
        "Lanyard Price:",
        f"₱{lanyard_price:,.2f}"
    )

    print(
        "Required Per Participant:",
        f"₱{required_amount:,.2f}"
    )

    # ========================================================
    # GET CASH DONATION TOTAL
    # ========================================================

    donation_total = (
        db.query(
            CashDonationTotal
        )
        .order_by(
            CashDonationTotal.id.asc()
        )
        .first()
    )

    if not donation_total:

        print(
            "No CashDonationTotal record exists."
        )

        return {

            "success":
                True,

            "status":
                "Queued",

            "message":
                "No cash donation total is available.",

            "tshirt_price":
                tshirt_price,

            "tshirt_price_display":
                f"₱{tshirt_price:,.2f}",

            "lanyard_price":
                lanyard_price,

            "lanyard_price_display":
                f"₱{lanyard_price:,.2f}",

            "required_amount_per_participant":
                required_amount,

            "required_amount_display":
                f"₱{required_amount:,.2f}",

            "cash_donation_total":
                0,

            "cash_donation_total_display":
                "₱0.00",

            "initial_queue_count":
                0,

            "sponsored_count":
                0,

            "remaining_queue_count":
                0,

            "participant_emails_sent":
                0,

            "participant_email_errors":
                [],

            "participants":
                []

        }

    # ========================================================
    # CURRENT BALANCE
    #
    # CashDonationTotal.total_amount = PESOS
    # ========================================================

    try:

        current_balance = float(
            donation_total.total_amount or 0
        )

    except (
        ValueError,
        TypeError
    ):

        current_balance = 0.0

    initial_balance = current_balance

    print(
        "Current Sponsorship Fund:",
        f"₱{current_balance:,.2f}"
    )

    # ========================================================
    # FIND FINDING SPONSOR PARTICIPANTS
    #
    # FIFO:
    #
    # Oldest Finding Sponsor participant
    # gets sponsored first.
    #
    # IMPORTANT:
    #
    # Use:
    #
    #     func.lower()
    #     func.coalesce()
    #     or_()
    #
    # NOT:
    #
    #     db.func
    #     db.or_
    #
    # ========================================================

    finding_sponsors = (
        db.query(
            Participant
        )
        .filter(

            Participant.is_archived == 0,

            Participant.participant_type.ilike(
                "Finding Sponsor"
            ),

            or_(

                func.lower(
                    func.coalesce(
                        Participant.tshirt_status,
                        "Unpaid"
                    )
                ) != "paid",

                func.lower(
                    func.coalesce(
                        Participant.lanyard_status,
                        "Unpaid"
                    )
                ) != "paid"

            )

        )
        .order_by(

            Participant.created_at.asc(),

            Participant.id.asc()

        )
        .all()
    )

    # ========================================================
    # QUEUE COUNT
    # ========================================================

    initial_queue_count = len(
        finding_sponsors
    )

    print(
        "Finding Sponsor Queue:",
        initial_queue_count
    )

    # ========================================================
    # NOTHING TO SPONSOR
    # ========================================================

    if initial_queue_count == 0:

        print(
            "No Finding Sponsor participants waiting."
        )

        return {

            "success":
                True,

            "status":
                "Completed",

            "message":
                "No Finding Sponsor participants are waiting for sponsorship.",

            "tshirt_price":
                tshirt_price,

            "tshirt_price_display":
                f"₱{tshirt_price:,.2f}",

            "lanyard_price":
                lanyard_price,

            "lanyard_price_display":
                f"₱{lanyard_price:,.2f}",

            "required_amount_per_participant":
                required_amount,

            "required_amount_display":
                f"₱{required_amount:,.2f}",

            "cash_donation_total":
                current_balance,

            "cash_donation_total_display":
                f"₱{current_balance:,.2f}",

            "initial_queue_count":
                0,

            "sponsored_count":
                0,

            "remaining_queue_count":
                0,

            "participant_emails_sent":
                0,

            "participant_email_errors":
                [],

            "participants":
                []

        }

    # ========================================================
    # PROCESS FIFO
    # ========================================================

    sponsored_participants = []

    try:

        for participant in finding_sponsors:

            # =================================================
            # STOP IF NOT ENOUGH MONEY
            # =================================================

            if current_balance < required_amount:

                print(
                    "Insufficient sponsorship fund."
                )

                print(
                    "Current:",
                    f"₱{current_balance:,.2f}"
                )

                print(
                    "Needed:",
                    f"₱{required_amount:,.2f}"
                )

                print(
                    "Still Needed:",
                    f"₱{required_amount - current_balance:,.2f}"
                )

                break

            # =================================================
            # FULL NAME
            # =================================================

            fullname = " ".join(

                part

                for part in [

                    getattr(
                        participant,
                        "fname",
                        None
                    ),

                    getattr(
                        participant,
                        "mname",
                        None
                    ),

                    getattr(
                        participant,
                        "lname",
                        None
                    )

                ]

                if part

            ).strip()

            # =================================================
            # DEDUCT SPONSORSHIP COST
            # =================================================

            current_balance -= (
                required_amount
            )

            # =================================================
            # MARK T-SHIRT PAID
            # =================================================

            if hasattr(
                participant,
                "tshirt_status"
            ):

                participant.tshirt_status = (
                    "Paid"
                )

            # =================================================
            # MARK LANYARD PAID
            # =================================================

            if hasattr(
                participant,
                "lanyard_status"
            ):

                participant.lanyard_status = (
                    "Paid"
                )

            # =================================================
            # COMPLETE REGISTRATION
            # =================================================

            if hasattr(
                participant,
                "registration_status"
            ):

                participant.registration_status = (
                    "Confirmed"
                )

            # =================================================
            # SPONSOR REVIEW APPROVED
            #
            # Supports either:
            #
            # sponsor_review_status
            #
            # OR:
            #
            # sponsorship_review_status
            # =================================================

            sponsor_review_status = "Approved"

            if hasattr(
                participant,
                "sponsor_review_status"
            ):

                participant.sponsor_review_status = (
                    "Approved"
                )

            elif hasattr(
                participant,
                "sponsorship_review_status"
            ):

                participant.sponsorship_review_status = (
                    "Approved"
                )

            # =================================================
            # UPDATE TIMESTAMP
            # =================================================

            if hasattr(
                participant,
                "updated_at"
            ):

                participant.updated_at = (
                    datetime.datetime.now()
                )

            # =================================================
            # RECORD RESULT
            # =================================================

            sponsored_participants.append({

                "participant_id":
                    participant.id,

                "registration_number":
                    getattr(
                        participant,
                        "registration_number",
                        None
                    ),

                "fullname":
                    fullname,

                "participant_type":
                    getattr(
                        participant,
                        "participant_type",
                        None
                    ),

                "tshirt_status":
                    getattr(
                        participant,
                        "tshirt_status",
                        "Paid"
                    ),

                "lanyard_status":
                    getattr(
                        participant,
                        "lanyard_status",
                        "Paid"
                    ),

                "registration_status":
                    getattr(
                        participant,
                        "registration_status",
                        None
                    ),

                "sponsor_review_status":
                    getattr(
                        participant,
                        "sponsor_review_status",
                        getattr(
                            participant,
                            "sponsorship_review_status",
                            sponsor_review_status
                        )
                    ),

                "sponsored_amount":
                    required_amount,

                "sponsored_amount_display":
                    f"₱{required_amount:,.2f}"

            })

            # =================================================
            # LOG
            # =================================================

            print("=" * 50)

            print(
                "PARTICIPANT SPONSORED"
            )

            print(
                "Participant ID:",
                participant.id
            )

            print(
                "Registration:",
                getattr(
                    participant,
                    "registration_number",
                    None
                )
            )

            print(
                "Name:",
                fullname
            )

            print(
                "Sponsored:",
                f"₱{required_amount:,.2f}"
            )

            print(
                "T-shirt:",
                getattr(
                    participant,
                    "tshirt_status",
                    None
                )
            )

            print(
                "Lanyard:",
                getattr(
                    participant,
                    "lanyard_status",
                    None
                )
            )

            print(
                "Registration:",
                getattr(
                    participant,
                    "registration_status",
                    None
                )
            )

            print(
                "Sponsor Review:",
                getattr(
                    participant,
                    "sponsor_review_status",
                    getattr(
                        participant,
                        "sponsorship_review_status",
                        "Approved"
                    )
                )
            )

            print(
                "Remaining Fund:",
                f"₱{current_balance:,.2f}"
            )

            print("=" * 50)

        # ====================================================
        # SAVE REMAINING BALANCE
        # ====================================================

        donation_total.total_amount = (
            current_balance
        )

        if hasattr(
            donation_total,
            "updated_at"
        ):

            donation_total.updated_at = (
                datetime.datetime.now()
            )

        # ====================================================
        # COMMIT DATABASE CHANGES
        # ====================================================

        db.commit()

        db.refresh(
            donation_total
        )

    except Exception as e:

        db.rollback()

        print("=" * 70)

        print(
            "FINDING SPONSOR PROCESSING ERROR"
        )

        print(
            "Error:",
            repr(e)
        )

        print("=" * 70)

        raise

    # ========================================================
    # GET REMAINING QUEUE
    #
    # Re-query AFTER commit so participants that were
    # marked Paid are no longer counted.
    # ========================================================

    remaining_queue = (
        db.query(
            Participant
        )
        .filter(

            Participant.is_archived == 0,

            Participant.participant_type.ilike(
                "Finding Sponsor"
            ),

            or_(

                func.lower(
                    func.coalesce(
                        Participant.tshirt_status,
                        "Unpaid"
                    )
                ) != "paid",

                func.lower(
                    func.coalesce(
                        Participant.lanyard_status,
                        "Unpaid"
                    )
                ) != "paid"

            )

        )
        .order_by(

            Participant.created_at.asc(),

            Participant.id.asc()

        )
        .all()
    )

    remaining_queue_count = len(
        remaining_queue
    )

    # ========================================================
    # DETERMINE QUEUE STATUS
    # ========================================================

    if remaining_queue_count == 0:

        queue_status = "Completed"

    elif current_balance >= required_amount:

        queue_status = "Ready"

    else:

        queue_status = "Queued"

    # ========================================================
    # SEND PARTICIPANT SPONSORSHIP EMAILS
    #
    # Email function signature:
    #
    # send_sponsored_participant_confirmation_email(
    #     participant,
    #     sponsored_amount
    # )
    #
    # IMPORTANT:
    #
    # The function is async.
    # Therefore we MUST use await.
    # ========================================================

    participant_emails_sent = 0

    participant_email_errors = []

    email_function = globals().get(
        "send_sponsored_participant_confirmation_email"
    )

    if not email_function:

        print(
            "WARNING:"
        )

        print(
            "send_sponsored_participant_confirmation_email "
            "is not defined."
        )

    else:

        for sponsored in sponsored_participants:

            try:

                sponsored_participant = (
                    db.query(
                        Participant
                    )
                    .filter(
                        Participant.id ==
                        sponsored[
                            "participant_id"
                        ]
                    )
                    .first()
                )

                if not sponsored_participant:

                    print(
                        "Sponsored participant not found:",
                        sponsored[
                            "participant_id"
                        ]
                    )

                    continue

                participant_email = getattr(
                    sponsored_participant,
                    "email",
                    None
                )

                if participant_email:

                    participant_email = str(
                        participant_email
                    ).strip()

                if not participant_email:

                    print(
                        "Sponsored participant has no email:",
                        sponsored[
                            "participant_id"
                        ]
                    )

                    continue

                # ==========================================
                # SEND EMAIL
                #
                # PASS BOTH:
                #
                # participant
                # sponsored_amount
                # ==========================================

                print(
                    "Sending sponsored participant email to:",
                    participant_email
                )

                await email_function(

                    sponsored_participant,

                    sponsored[
                        "sponsored_amount"
                    ]

                )

                participant_emails_sent += 1

                print(
                    "Sponsored participant email sent:",
                    participant_email
                )

            except Exception as e:

                print(
                    "Sponsored participant email failed:"
                )

                print(
                    "Participant ID:",
                    sponsored[
                        "participant_id"
                    ]
                )

                print(
                    "Error:",
                    repr(e)
                )

                participant_email_errors.append({

                    "participant_id":
                        sponsored[
                            "participant_id"
                        ],

                    "email":
                        getattr(
                            sponsored_participant,
                            "email",
                            None
                        ),

                    "error":
                        str(e)

                })

    # ========================================================
    # TOTAL SPONSORED AMOUNT
    # ========================================================

    total_sponsored_amount = (
        len(
            sponsored_participants
        ) *
        required_amount
    )

    # ========================================================
    # FINAL LOG
    # ========================================================

    print("=" * 70)

    print(
        "FINDING SPONSOR PROCESSING COMPLETE"
    )

    print("=" * 70)

    print(
        "Initial Fund:",
        f"₱{initial_balance:,.2f}"
    )

    print(
        "Total Sponsored:",
        f"₱{total_sponsored_amount:,.2f}"
    )

    print(
        "Remaining Fund:",
        f"₱{current_balance:,.2f}"
    )

    print(
        "Sponsored Participants:",
        len(
            sponsored_participants
        )
    )

    print(
        "Remaining Queue:",
        remaining_queue_count
    )

    print(
        "Emails Sent:",
        participant_emails_sent
    )

    print(
        "Email Errors:",
        len(
            participant_email_errors
        )
    )

    print("=" * 70)

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "success":
            True,

        "status":
            queue_status,

        "message":
            "Finding Sponsor queue processed successfully.",

        # ====================================================
        # PRICES
        # ====================================================

        "tshirt_price":
            tshirt_price,

        "tshirt_price_display":
            f"₱{tshirt_price:,.2f}",

        "tshirt_price_centavos":
            tshirt_price_centavos,

        "lanyard_price":
            lanyard_price,

        "lanyard_price_display":
            f"₱{lanyard_price:,.2f}",

        "lanyard_price_centavos":
            lanyard_price_centavos,

        "required_amount_per_participant":
            required_amount,

        "required_amount_display":
            f"₱{required_amount:,.2f}",

        # ====================================================
        # FUND
        # ====================================================

        "initial_cash_donation_total":
            initial_balance,

        "initial_cash_donation_total_display":
            f"₱{initial_balance:,.2f}",

        "total_sponsored_amount":
            total_sponsored_amount,

        "total_sponsored_amount_display":
            f"₱{total_sponsored_amount:,.2f}",

        "cash_donation_total":
            current_balance,

        "cash_donation_total_display":
            f"₱{current_balance:,.2f}",

        # ====================================================
        # QUEUE
        # ====================================================

        "initial_queue_count":
            initial_queue_count,

        "sponsored_count":
            len(
                sponsored_participants
            ),

        "remaining_queue_count":
            remaining_queue_count,

        # ====================================================
        # EMAIL
        # ====================================================

        "participant_emails_sent":
            participant_emails_sent,

        "participant_email_errors":
            participant_email_errors,

        # ====================================================
        # PARTICIPANTS
        # ====================================================

        "participants":
            sponsored_participants

    }


























@app.get("/webhooks/paymongo")
async def paymongo_webhook_test():
    print("PAYMONGO WEBHOOK GET TEST HIT")
    return {
        "ok": True,
        "message": "PayMongo webhook endpoint is reachable"
    }


# ======================================================
# PAYMONGO WEBHOOK
#
# SUPPORTS:
# - PARTICIPANT PAYMENTS
# - CASH SPONSORSHIPS
# - STORE PURCHASES
#
# STORE PURCHASES:
# - 1 item
# - 2 items
# - 3 items
# - 10 items
# - Up to the cart limit configured in /store/purchase
#
# ONE STORE CART = ONE PAYMONGO PAYMENT LINK
# ONE STORE CART ITEM = ONE PAYMENT DATABASE ROW
#
# ALL STORE PAYMENT ROWS SHARE:
#     store_order_id
#     paymongo_link_id
#
# When the webhook confirms payment:
#
#     ALL pending rows belonging to the same
#     store_order_id are processed.
#
# Inventory is reduced for EVERY unpaid cart item.
# ======================================================

# ======================================================
# PAYMONGO WEBHOOK
# ======================================================
#
# Handles:
#
# 1. Participant payments
# 2. Bulk participant payments
# 3. Store payments
# 4. Cash sponsorship payments
#
# IMPORTANT PARTICIPANT PAYMENT RULE:
#
# Payment.status being "Paid" does NOT mean that the
# Participant merchandise statuses are already synchronized.
#
# Therefore, participant payment rows are ALWAYS synchronized
# when payment.paid is received.
#
# This fixes cases such as:
#
# Payment.status       = Paid
# Participant.lanyard_status = Pending
#
# The webhook will repair the participant status.
#
# ======================================================

# ============================================================
# PAYMONGO WEBHOOK
# ============================================================
#
# SUPPORTS:
#   1. Normal participant payments
#   2. Bulk participant payments
#   3. Cash sponsorship payments
#   4. Store/cart payments
#
# IMPORTANT:
#
# Participant bulk payment:
#
#   Payment #101 -> Participant 27 -> Lanyard
#   Payment #102 -> Participant 28 -> Lanyard
#   Payment #103 -> Participant 29 -> Lanyard
#
# All rows share ONE PayMongo payment link.
#
# When PayMongo confirms payment, ALL participant rows
# belonging to that link are marked Paid and each participant
# is updated independently.
#
# ============================================================

@app.post("/webhooks/paymongo")
async def paymongo_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    print("\n")
    print("=" * 80)
    print("PAYMONGO WEBHOOK RECEIVED")
    print("=" * 80)

    # ========================================================
    # 1. READ RAW BODY
    # ========================================================

    try:
        raw_body = await request.body()

    except Exception as e:

        print(
            "Webhook body read failed:",
            repr(e)
        )

        return JSONResponse(
            status_code=400,
            content={
                "received": False,
                "processed": False,
                "message": "Unable to read webhook body."
            }
        )

    if not raw_body:

        print(
            "Webhook body is empty."
        )

        return JSONResponse(
            status_code=400,
            content={
                "received": False,
                "processed": False,
                "message": "Empty webhook body."
            }
        )

    print(
        "Body Length:",
        len(raw_body)
    )

    # ========================================================
    # 2. PAYMONGO SIGNATURE
    # ========================================================

    signature_header = request.headers.get(
        "Paymongo-Signature"
    )

    if not signature_header:

        print(
            "Missing Paymongo-Signature."
        )

        return JSONResponse(
            status_code=401,
            content={
                "received": False,
                "processed": False,
                "message": "Missing PayMongo signature."
            }
        )

    # ========================================================
    # 3. VERIFY SIGNATURE
    # ========================================================

    try:

        parts = {}

        for item in signature_header.split(","):

            if "=" not in item:
                continue

            key, value = item.split(
                "=",
                1
            )

            parts[
                key.strip()
            ] = value.strip()

        timestamp = parts.get("t")

        test_signature = parts.get(
            "te",
            ""
        )

        live_signature = parts.get(
            "li",
            ""
        )

        if not timestamp:

            return JSONResponse(
                status_code=401,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Missing webhook timestamp."
                }
            )

        timestamp_int = int(
            timestamp
        )

        current_timestamp = int(
            time.time()
        )

        difference = abs(
            current_timestamp -
            timestamp_int
        )

        print(
            "Webhook Timestamp Difference:",
            difference,
            "seconds"
        )

        if difference > 300:

            print(
                "Webhook timestamp expired."
            )

            return JSONResponse(
                status_code=401,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Webhook timestamp expired."
                }
            )

        if not PAYMONGO_WEBHOOK_SECRET:

            print(
                "PAYMONGO_WEBHOOK_SECRET is missing."
            )

            return JSONResponse(
                status_code=500,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Webhook secret is not configured."
                }
            )

        signed_payload = (
            f"{timestamp}."
        ).encode(
            "utf-8"
        ) + raw_body

        expected_signature = hmac.new(
            PAYMONGO_WEBHOOK_SECRET.encode(
                "utf-8"
            ),
            signed_payload,
            hashlib.sha256
        ).hexdigest()

        provided_signature = (
            live_signature
            if live_signature
            else test_signature
        )

        if not provided_signature:

            return JSONResponse(
                status_code=401,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Missing signature value."
                }
            )

        if not hmac.compare_digest(
            expected_signature,
            provided_signature
        ):

            print(
                "Invalid PayMongo signature."
            )

            return JSONResponse(
                status_code=401,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Invalid PayMongo webhook signature."
                }
            )

        print(
            "Webhook signature verified."
        )

    except Exception as e:

        print(
            "Webhook signature verification failed:",
            repr(e)
        )

        return JSONResponse(
            status_code=401,
            content={
                "received": False,
                "processed": False,
                "message": "Invalid PayMongo webhook signature."
            }
        )

    # ========================================================
    # 4. PARSE JSON
    # ========================================================

    try:

        payload = json.loads(
            raw_body.decode(
                "utf-8"
            )
        )

    except Exception as e:

        print(
            "JSON parse failed:",
            repr(e)
        )

        return JSONResponse(
            status_code=400,
            content={
                "received": False,
                "processed": False,
                "message": "Invalid JSON payload."
            }
        )

    # ========================================================
    # 5. EVENT
    # ========================================================

    event_data = payload.get(
        "data",
        {}
    )

    if not isinstance(
        event_data,
        dict
    ):
        event_data = {}

    event_id = event_data.get(
        "id"
    )

    event_attributes = event_data.get(
        "attributes",
        {}
    )

    if not isinstance(
        event_attributes,
        dict
    ):
        event_attributes = {}

    event_type = event_attributes.get(
        "type"
    )

    livemode = event_attributes.get(
        "livemode"
    )

    print("=" * 80)
    print("PAYMONGO EVENT")
    print("=" * 80)
    print(
        "Event ID:",
        event_id
    )
    print(
        "Event Type:",
        event_type
    )
    print(
        "Live Mode:",
        livemode
    )
    print("=" * 80)

    # ========================================================
    # 6. ONLY SUCCESSFUL EVENTS
    # ========================================================

    if event_type not in {
        "payment.paid",
        "link.payment.paid"
    }:

        print(
            "Event ignored:",
            event_type
        )

        return {
            "received": True,
            "processed": False,
            "event_id": event_id,
            "event_type": event_type,
            "message": "Event ignored."
        }

    # ========================================================
    # 7. PAYMONGO RESOURCE
    # ========================================================

    resource = event_attributes.get(
        "data",
        {}
    )

    if not isinstance(
        resource,
        dict
    ):
        resource = {}

    resource_id = resource.get(
        "id"
    )

    resource_type = resource.get(
        "type"
    )

    resource_attributes = resource.get(
        "attributes",
        {}
    )

    if not isinstance(
        resource_attributes,
        dict
    ):
        resource_attributes = {}

    print(
        "Resource ID:",
        resource_id
    )

    print(
        "Resource Type:",
        resource_type
    )

    # ========================================================
    # 8. METADATA
    # ========================================================

    metadata = resource_attributes.get(
        "metadata",
        {}
    )

    if not isinstance(
        metadata,
        dict
    ):
        metadata = {}

    print(
        "Metadata:",
        metadata
    )

    # ========================================================
    # 9. IDENTIFIERS
    # ========================================================

    # --------------------------------------------------------
    # SPONSORSHIP ID
    # --------------------------------------------------------

    sponsorship_id = metadata.get(
        "sponsorship_id"
    )

    if sponsorship_id:

        sponsorship_id = str(
            sponsorship_id
        ).strip()

    # --------------------------------------------------------
    # STORE ORDER ID
    # --------------------------------------------------------

    store_order_id = (
        metadata.get(
            "store_order_id"
        )
        or metadata.get(
            "order_id"
        )
    )

    if store_order_id:

        store_order_id = str(
            store_order_id
        ).strip()

    # --------------------------------------------------------
    # INTERNAL PAYMENT ID
    # --------------------------------------------------------

    internal_payment_id = metadata.get(
        "payment_id"
    )

    if internal_payment_id:

        internal_payment_id = str(
            internal_payment_id
        ).strip()

    # --------------------------------------------------------
    # BULK PAYMENT IDS
    #
    # create_payment sends:
    #
    #   "payment_ids": "101,102,103"
    #
    # --------------------------------------------------------

    raw_payment_ids = metadata.get(
        "payment_ids"
    )

    payment_ids = []

    if isinstance(
        raw_payment_ids,
        list
    ):

        for value in raw_payment_ids:

            try:

                payment_ids.append(
                    int(value)
                )

            except (
                ValueError,
                TypeError
            ):

                pass

    elif raw_payment_ids:

        raw_payment_ids_string = str(
            raw_payment_ids
        ).strip()

        # ----------------------------------------------------
        # JSON ARRAY
        # ----------------------------------------------------

        if (
            raw_payment_ids_string.startswith("[")
            and
            raw_payment_ids_string.endswith("]")
        ):

            try:

                decoded_payment_ids = json.loads(
                    raw_payment_ids_string
                )

                if isinstance(
                    decoded_payment_ids,
                    list
                ):

                    for value in decoded_payment_ids:

                        try:

                            payment_ids.append(
                                int(value)
                            )

                        except (
                            ValueError,
                            TypeError
                        ):

                            pass

            except Exception:

                pass

        # ----------------------------------------------------
        # COMMA-SEPARATED
        # ----------------------------------------------------

        else:

            for value in raw_payment_ids_string.split(","):

                value = value.strip()

                if not value:
                    continue

                try:

                    payment_ids.append(
                        int(value)
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    pass

    # Remove duplicates
    payment_ids = list(
        dict.fromkeys(
            payment_ids
        )
    )

    # --------------------------------------------------------
    # PAYMONGO REFERENCE
    # --------------------------------------------------------

    paymongo_reference = (
        metadata.get(
            "pm_reference_number"
        )
        or metadata.get(
            "reference_number"
        )
        or resource_attributes.get(
            "external_reference_number"
        )
        or resource_attributes.get(
            "reference_number"
        )
    )

    if paymongo_reference:

        paymongo_reference = str(
            paymongo_reference
        ).strip()

    else:

        paymongo_reference = None

    # --------------------------------------------------------
    # PAYMONGO PAYMENT ID
    # --------------------------------------------------------

    paymongo_payment_id = None

    if event_type == "payment.paid":

        paymongo_payment_id = resource_id

    if not paymongo_payment_id:

        paymongo_payment_id = metadata.get(
            "paymongo_payment_id"
        )

    if paymongo_payment_id:

        paymongo_payment_id = str(
            paymongo_payment_id
        ).strip()

    # --------------------------------------------------------
    # PAYMONGO LINK ID
    # --------------------------------------------------------

    paymongo_link_id = None

    if event_type == "link.payment.paid":

        paymongo_link_id = resource_id

    if not paymongo_link_id:

        paymongo_link_id = metadata.get(
            "paymongo_link_id"
        )

    if not paymongo_link_id:

        paymongo_link_id = resource_attributes.get(
            "link_id"
        )

    if paymongo_link_id:

        paymongo_link_id = str(
            paymongo_link_id
        ).strip()

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    paymongo_amount = resource_attributes.get(
        "amount"
    )

    try:

        paymongo_amount = int(
            paymongo_amount or 0
        )

    except (
        ValueError,
        TypeError
    ):

        paymongo_amount = 0

    print("=" * 80)
    print("PAYMENT IDENTIFIERS")
    print("=" * 80)
    print(
        "Store Order ID:",
        store_order_id
    )
    print(
        "Internal Payment ID:",
        internal_payment_id
    )
    print(
        "Bulk Payment IDs:",
        payment_ids
    )
    print(
        "PayMongo Reference:",
        paymongo_reference
    )
    print(
        "PayMongo Payment ID:",
        paymongo_payment_id
    )
    print(
        "PayMongo Link ID:",
        paymongo_link_id
    )
    print(
        "PayMongo Amount:",
        paymongo_amount
    )
    print("=" * 80)

    # ========================================================
    # 10. CASH SPONSORSHIP MATCHING
    # ========================================================

    cash_sponsorship = None

    # --------------------------------------------------------
    # BY SPONSORSHIP ID
    # --------------------------------------------------------

    if sponsorship_id:

        try:

            cash_sponsorship = (
                db.query(
                    CashSponsorship
                )
                .filter(
                    CashSponsorship.id ==
                    int(
                        sponsorship_id
                    )
                )
                .first()
            )

        except (
            ValueError,
            TypeError
        ):

            cash_sponsorship = None

    # --------------------------------------------------------
    # BY REFERENCE
    # --------------------------------------------------------

    if (
        not cash_sponsorship
        and paymongo_reference
        and hasattr(
            CashSponsorship,
            "paymongo_reference"
        )
    ):

        cash_sponsorship = (
            db.query(
                CashSponsorship
            )
            .filter(
                CashSponsorship.paymongo_reference ==
                paymongo_reference
            )
            .first()
        )

    # --------------------------------------------------------
    # BY PAYMONGO PAYMENT ID
    # --------------------------------------------------------

    if (
        not cash_sponsorship
        and paymongo_payment_id
        and hasattr(
            CashSponsorship,
            "paymongo_payment_id"
        )
    ):

        cash_sponsorship = (
            db.query(
                CashSponsorship
            )
            .filter(
                CashSponsorship.paymongo_payment_id ==
                paymongo_payment_id
            )
            .first()
        )

    # --------------------------------------------------------
    # BY PAYMONGO LINK ID
    # --------------------------------------------------------

    if (
        not cash_sponsorship
        and paymongo_link_id
        and hasattr(
            CashSponsorship,
            "paymongo_link_id"
        )
    ):

        cash_sponsorship = (
            db.query(
                CashSponsorship
            )
            .filter(
                CashSponsorship.paymongo_link_id ==
                paymongo_link_id
            )
            .first()
        )

    # ========================================================
    # 11. CASH SPONSORSHIP
    # ========================================================

    if cash_sponsorship:

        print("=" * 80)
        print(
            "CASH SPONSORSHIP FOUND"
        )
        print(
            "Sponsorship ID:",
            cash_sponsorship.id
        )
        print("=" * 80)

        # ----------------------------------------------------
        # SAVE PAYMONGO INFORMATION
        # ----------------------------------------------------

        if (
            paymongo_reference
            and hasattr(
                cash_sponsorship,
                "paymongo_reference"
            )
        ):

            cash_sponsorship.paymongo_reference = (
                paymongo_reference
            )

        if (
            paymongo_payment_id
            and hasattr(
                cash_sponsorship,
                "paymongo_payment_id"
            )
        ):

            cash_sponsorship.paymongo_payment_id = (
                paymongo_payment_id
            )

        if (
            paymongo_link_id
            and hasattr(
                cash_sponsorship,
                "paymongo_link_id"
            )
        ):

            cash_sponsorship.paymongo_link_id = (
                paymongo_link_id
            )

        # ----------------------------------------------------
        # CURRENT STATUS
        # ----------------------------------------------------

        current_status = str(
            getattr(
                cash_sponsorship,
                "payment_status",
                ""
            )
            or ""
        ).strip().lower()

        # ----------------------------------------------------
        # ALREADY PAID
        # ----------------------------------------------------

        if current_status == "paid":

            try:
                db.commit()
            except Exception:
                db.rollback()

            print(
                "Sponsorship already Paid."
            )

            return {
                "received": True,
                "processed": True,
                "already_processed": True,
                "payment_type": "sponsor_package",
                "event_id": event_id,
                "sponsorship_id": cash_sponsorship.id,
                "payment_status": "Paid"
            }

        # ----------------------------------------------------
        # DONATION AMOUNT
        # ----------------------------------------------------

        try:

            donation_amount = int(
                getattr(
                    cash_sponsorship,
                    "donation_amount",
                    0
                )
                or 0
            )

        except (
            ValueError,
            TypeError
        ):

            donation_amount = 0

        if donation_amount <= 0:

            db.rollback()

            return {
                "received": True,
                "processed": False,
                "payment_type": "sponsor_package",
                "sponsorship_id": cash_sponsorship.id,
                "message": "Invalid sponsorship amount."
            }

        # ----------------------------------------------------
        # VERIFY AMOUNT
        # ----------------------------------------------------

        if (
            paymongo_amount > 0
            and
            paymongo_amount != donation_amount
        ):

            print(
                "SPONSORSHIP AMOUNT MISMATCH"
            )

            db.rollback()

            return {
                "received": True,
                "processed": False,
                "payment_type": "sponsor_package",
                "sponsorship_id": cash_sponsorship.id,
                "paymongo_amount": paymongo_amount,
                "expected_amount": donation_amount,
                "message":
                    "Payment amount does not match sponsorship amount."
            }

        donation_pesos = (
            donation_amount / 100
        )

        # ----------------------------------------------------
        # CASH DONATION TOTAL
        # ----------------------------------------------------

        donation_total = (
            db.query(
                CashDonationTotal
            )
            .order_by(
                CashDonationTotal.id.asc()
            )
            .first()
        )

        if not donation_total:

            donation_total = CashDonationTotal(
                total_amount=0
            )

            db.add(
                donation_total
            )

            db.flush()

        try:

            current_total = float(
                donation_total.total_amount
                or 0
            )

        except (
            ValueError,
            TypeError
        ):

            current_total = 0.0

        new_total = (
            current_total +
            donation_pesos
        )

        donation_total.total_amount = (
            new_total
        )

        if hasattr(
            donation_total,
            "updated_at"
        ):

            donation_total.updated_at = (
                datetime.datetime.now()
            )

        # ----------------------------------------------------
        # MARK SPONSORSHIP PAID
        # ----------------------------------------------------

        cash_sponsorship.payment_status = (
            "Paid"
        )

        if hasattr(
            cash_sponsorship,
            "donation_status"
        ):

            cash_sponsorship.donation_status = (
                "Paid"
            )

        if hasattr(
            cash_sponsorship,
            "paid_at"
        ):

            cash_sponsorship.paid_at = (
                datetime.datetime.now()
            )

        if hasattr(
            cash_sponsorship,
            "updated_at"
        ):

            cash_sponsorship.updated_at = (
                datetime.datetime.now()
            )

        if hasattr(
            cash_sponsorship,
            "cash_total_added"
        ):

            cash_sponsorship.cash_total_added = (
                donation_pesos
            )

        # ----------------------------------------------------
        # COMMIT SPONSORSHIP
        # ----------------------------------------------------

        try:

            db.commit()

        except Exception as e:

            db.rollback()

            print(
                "Sponsorship commit failed:",
                repr(e)
            )

            return JSONResponse(
                status_code=500,
                content={
                    "received": True,
                    "processed": False,
                    "message":
                        "Sponsorship database update failed."
                }
            )

        # ----------------------------------------------------
        # SPONSORSHIP EMAIL
        # ----------------------------------------------------

        gmail_success = False

        try:

            sponsor_email = getattr(
                cash_sponsorship,
                "email",
                None
            )

            if sponsor_email:

                gmail_success = bool(
                    await send_cash_sponsorship_confirmation_email(
                        cash_sponsorship,
                        cash_sponsorship
                    )
                )

                print(
                    "Sponsorship Gmail:",
                    gmail_success
                )

        except Exception as e:

            print(
                "Sponsorship Gmail failed:",
                repr(e)
            )

        return {
            "received": True,
            "processed": True,
            "payment_type": "sponsor_package",
            "event_id": event_id,
            "sponsorship_id": cash_sponsorship.id,
            "payment_status": "Paid",
            "donation_amount": donation_pesos,
            "donation_amount_display":
                f"₱{donation_pesos:,.2f}",
            "cash_donation_total": new_total,
            "cash_donation_total_display":
                f"₱{new_total:,.2f}",
            "paymongo_reference":
                paymongo_reference,
            "paymongo_payment_id":
                paymongo_payment_id,
            "paymongo_link_id":
                paymongo_link_id,
            "gmail_sent":
                gmail_success
        }

    # ========================================================
    # 12. FIND PAYMENT ROW
    #
    # For participant bulk payments, payment_ids is the
    # strongest identifier.
    # ========================================================

    payment = None

    # --------------------------------------------------------
    # BY PAYMENT IDS
    # --------------------------------------------------------

    if payment_ids:

        payment = (
            db.query(
                Payment
            )
            .filter(
                Payment.id.in_(
                    payment_ids
                )
            )
            .order_by(
                Payment.id.asc()
            )
            .first()
        )

    # --------------------------------------------------------
    # BY STORE ORDER
    # --------------------------------------------------------

    if (
        not payment
        and store_order_id
    ):

        payment = (
            db.query(
                Payment
            )
            .filter(
                Payment.store_order_id ==
                store_order_id
            )
            .order_by(
                Payment.id.asc()
            )
            .first()
        )

    # --------------------------------------------------------
    # BY INTERNAL PAYMENT ID
    # --------------------------------------------------------

    if (
        not payment
        and internal_payment_id
    ):

        try:

            payment = (
                db.query(
                    Payment
                )
                .filter(
                    Payment.id ==
                    int(
                        internal_payment_id
                    )
                )
                .first()
            )

        except (
            ValueError,
            TypeError
        ):

            payment = None

    # --------------------------------------------------------
    # BY REFERENCE
    # --------------------------------------------------------

    if (
        not payment
        and paymongo_reference
        and hasattr(
            Payment,
            "paymongo_reference"
        )
    ):

        payment = (
            db.query(
                Payment
            )
            .filter(
                Payment.paymongo_reference ==
                paymongo_reference
            )
            .order_by(
                Payment.id.asc()
            )
            .first()
        )

    # --------------------------------------------------------
    # BY PAYMONGO PAYMENT ID
    # --------------------------------------------------------

    if (
        not payment
        and paymongo_payment_id
        and hasattr(
            Payment,
            "paymongo_payment_id"
        )
    ):

        payment = (
            db.query(
                Payment
            )
            .filter(
                Payment.paymongo_payment_id ==
                paymongo_payment_id
            )
            .order_by(
                Payment.id.asc()
            )
            .first()
        )

    # --------------------------------------------------------
    # BY PAYMONGO LINK ID
    # --------------------------------------------------------

    if (
        not payment
        and paymongo_link_id
        and hasattr(
            Payment,
            "paymongo_link_id"
        )
    ):

        payment = (
            db.query(
                Payment
            )
            .filter(
                Payment.paymongo_link_id ==
                paymongo_link_id
            )
            .order_by(
                Payment.id.asc()
            )
            .first()
        )

    # ========================================================
    # PAYMENT NOT FOUND
    # ========================================================

    if not payment:

        print("=" * 80)
        print(
            "NO LOCAL PAYMENT FOUND"
        )
        print("=" * 80)

        return {
            "received": True,
            "processed": False,
            "event_id": event_id,
            "payment_ids": payment_ids,
            "paymongo_reference":
                paymongo_reference,
            "paymongo_payment_id":
                paymongo_payment_id,
            "paymongo_link_id":
                paymongo_link_id,
            "message":
                "No matching local payment found."
        }

    print("=" * 80)
    print(
        "LOCAL PAYMENT FOUND"
    )
    print(
        "Payment ID:",
        payment.id
    )
    print(
        "Payment Type:",
        getattr(
            payment,
            "payment_type",
            None
        )
    )
    print("=" * 80)

    # ========================================================
    # 13. DETERMINE PAYMENT TYPE
    # ========================================================

    payment_type = str(
        getattr(
            payment,
            "payment_type",
            ""
        )
        or ""
    ).strip().lower()

    # ========================================================
    # ========================================================
    # PARTICIPANT / BULK PARTICIPANT PAYMENT
    # ========================================================
    #
    # IMPORTANT:
    #
    # BOTH "participant" AND "bulk" MUST ENTER THIS BLOCK.
    #
    # /create_payment uses:
    #
    #   payment_type = "bulk"
    #
    # for multiple participants.
    #
    # ========================================================

    if payment_type in {
        "participant",
        "bulk",
        "single"
    }:

        print("=" * 80)
        print(
            "PROCESSING PARTICIPANT PAYMENT"
        )
        print(
            "Payment Type:",
            payment_type
        )
        print("=" * 80)

        # ----------------------------------------------------
        # FIND ALL PARTICIPANT PAYMENT ROWS
        # ----------------------------------------------------

        participant_payments = []

        # ----------------------------------------------------
        # FIRST: EXACT PAYMENT IDS FROM METADATA
        # ----------------------------------------------------

        if payment_ids:

            participant_payments = (
                db.query(
                    Payment
                )
                .filter(
                    Payment.id.in_(
                        payment_ids
                    ),
                    Payment.payment_type.ilike(
                        "Participant"
                    )
                )
                .order_by(
                    Payment.id.asc()
                )
                .with_for_update()
                .all()
            )

            print(
                "Participant rows found by payment_ids:",
                len(
                    participant_payments
                )
            )

        # ----------------------------------------------------
        # FALLBACK: SHARED PAYMONGO LINK
        # ----------------------------------------------------

        if (
            not participant_payments
            and paymongo_link_id
        ):

            participant_payments = (
                db.query(
                    Payment
                )
                .filter(
                    Payment.paymongo_link_id ==
                    paymongo_link_id,
                    Payment.payment_type.ilike(
                        "Participant"
                    )
                )
                .order_by(
                    Payment.id.asc()
                )
                .with_for_update()
                .all()
            )

            print(
                "Participant rows found by PayMongo Link ID:",
                len(
                    participant_payments
                )
            )

        # ----------------------------------------------------
        # FALLBACK: REFERENCE
        # ----------------------------------------------------

        if (
            not participant_payments
            and paymongo_reference
        ):

            participant_payments = (
                db.query(
                    Payment
                )
                .filter(
                    Payment.paymongo_reference ==
                    paymongo_reference,
                    Payment.payment_type.ilike(
                        "Participant"
                    )
                )
                .order_by(
                    Payment.id.asc()
                )
                .with_for_update()
                .all()
            )

            print(
                "Participant rows found by reference:",
                len(
                    participant_payments
                )
            )

        # ----------------------------------------------------
        # FALLBACK: SINGLE PAYMENT
        # ----------------------------------------------------

        if (
            not participant_payments
            and payment
            and getattr(
                payment,
                "participant_id",
                None
            )
        ):

            participant_payments = [
                payment
            ]

        # ----------------------------------------------------
        # NO PARTICIPANT ROWS
        # ----------------------------------------------------

        if not participant_payments:

            db.rollback()

            return {
                "received": True,
                "processed": False,
                "payment_type":
                    payment_type,
                "message":
                    "No participant payment rows found."
            }

        # ----------------------------------------------------
        # REMOVE DUPLICATES
        # ----------------------------------------------------

        unique_payments = {}

        for participant_payment in participant_payments:

            unique_payments[
                participant_payment.id
            ] = participant_payment

        participant_payments = list(
            unique_payments.values()
        )

        participant_payments.sort(
            key=lambda p: p.id
        )

        print("=" * 80)
        print(
            "PARTICIPANT PAYMENT ROWS:"
        )
        print("=" * 80)

        for participant_payment in participant_payments:

            print(
                "Payment ID:",
                participant_payment.id,
                "| Participant ID:",
                getattr(
                    participant_payment,
                    "participant_id",
                    None
                ),
                "| Amount:",
                getattr(
                    participant_payment,
                    "amount",
                    None
                ),
                "| T-Shirt:",
                getattr(
                    participant_payment,
                    "tshirt_selected",
                    0
                ),
                "| Lanyard:",
                getattr(
                    participant_payment,
                    "lanyard_selected",
                    0
                ),
                "| Status:",
                getattr(
                    participant_payment,
                    "status",
                    None
                )
            )

        print("=" * 80)

        # ----------------------------------------------------
        # VERIFY PAYMENT IDS
        #
        # If create_payment explicitly supplied payment_ids,
        # do not silently process only part of the bulk payment.
        # ----------------------------------------------------

        if payment_ids:

            found_ids = {
                p.id
                for p in participant_payments
            }

            missing_ids = [
                pid
                for pid in payment_ids
                if pid not in found_ids
            ]

            if missing_ids:

                print(
                    "Missing participant payment IDs:",
                    missing_ids
                )

                # Try shared PayMongo link as recovery.
                if paymongo_link_id:

                    fallback_payments = (
                        db.query(
                            Payment
                        )
                        .filter(
                            Payment.paymongo_link_id ==
                            paymongo_link_id,
                            Payment.payment_type.ilike(
                                "Participant"
                            )
                        )
                        .order_by(
                            Payment.id.asc()
                        )
                        .with_for_update()
                        .all()
                    )

                    fallback_ids = {
                        p.id
                        for p in fallback_payments
                    }

                    if all(
                        pid in fallback_ids
                        for pid in payment_ids
                    ):

                        participant_payments = (
                            fallback_payments
                        )

                    else:

                        db.rollback()

                        return {
                            "received": True,
                            "processed": False,
                            "payment_type":
                                payment_type,
                            "payment_ids":
                                payment_ids,
                            "missing_payment_ids":
                                missing_ids,
                            "message":
                                "Not all bulk participant payment rows were found."
                        }

        # ----------------------------------------------------
        # VERIFY TOTAL
        #
        # /create_payment creates one Payment row per
        # participant, but ONE PayMongo link contains the
        # combined amount.
        # ----------------------------------------------------

        expected_participant_amount = 0

        for participant_payment in participant_payments:

            try:

                row_amount = int(
                    getattr(
                        participant_payment,
                        "amount",
                        0
                    )
                    or 0
                )

            except (
                ValueError,
                TypeError
            ):

                row_amount = 0

            if row_amount <= 0:

                db.rollback()

                return {
                    "received": True,
                    "processed": False,
                    "payment_type":
                        payment_type,
                    "payment_id":
                        participant_payment.id,
                    "message":
                        "Invalid participant payment amount."
                }

            expected_participant_amount += (
                row_amount
            )

        print("=" * 80)
        print(
            "PARTICIPANT AMOUNT VERIFICATION"
        )
        print(
            "PayMongo Amount:",
            paymongo_amount
        )
        print(
            "Expected Amount:",
            expected_participant_amount
        )
        print("=" * 80)

        if (
            paymongo_amount > 0
            and
            paymongo_amount !=
            expected_participant_amount
        ):

            print(
                "PARTICIPANT PAYMENT AMOUNT MISMATCH"
            )

            db.rollback()

            return {
                "received": True,
                "processed": False,
                "payment_type":
                    payment_type,
                "paymongo_amount":
                    paymongo_amount,
                "expected_amount":
                    expected_participant_amount,
                "payment_ids":
                    [
                        p.id
                        for p in participant_payments
                    ],
                "message":
                    "Payment amount does not match participant payment total."
            }

        # ----------------------------------------------------
        # PROCESS EACH PARTICIPANT
        # ----------------------------------------------------

        processed_participants = []

        now = datetime.datetime.now()

        for participant_payment in participant_payments:

            participant_id = getattr(
                participant_payment,
                "participant_id",
                None
            )

            print("=" * 80)
            print(
                "PROCESSING PARTICIPANT"
            )
            print(
                "Payment ID:",
                participant_payment.id
            )
            print(
                "Participant ID:",
                participant_id
            )
            print("=" * 80)

            if not participant_id:

                db.rollback()

                return {
                    "received": True,
                    "processed": False,
                    "payment_type":
                        payment_type,
                    "payment_id":
                        participant_payment.id,
                    "message":
                        "Participant ID is missing."
                }

            # ------------------------------------------------
            # LOCK PARTICIPANT
            # ------------------------------------------------

            participant = (
                db.query(
                    Participant
                )
                .filter(
                    Participant.id ==
                    participant_id
                )
                .with_for_update()
                .first()
            )

            if not participant:

                db.rollback()

                return {
                    "received": True,
                    "processed": False,
                    "payment_type":
                        payment_type,
                    "payment_id":
                        participant_payment.id,
                    "participant_id":
                        participant_id,
                    "message":
                        "Participant not found."
                }

            print(
                "Participant:",
                getattr(
                    participant,
                    "fname",
                    ""
                ),
                getattr(
                    participant,
                    "lname",
                    ""
                )
            )

            # ------------------------------------------------
            # ITEM FLAGS
            #
            # IMPORTANT:
            #
            # The local Payment row is the source of truth.
            #
            # ------------------------------------------------

            tshirt_selected = bool(
                getattr(
                    participant_payment,
                    "tshirt_selected",
                    False
                )
            )

            lanyard_selected = bool(
                getattr(
                    participant_payment,
                    "lanyard_selected",
                    False
                )
            )

            tshirt_size = getattr(
                participant_payment,
                "tshirt_size",
                None
            )

            print(
                "T-Shirt Selected:",
                tshirt_selected
            )

            print(
                "Lanyard Selected:",
                lanyard_selected
            )

            print(
                "T-Shirt Size:",
                tshirt_size
            )

            # ------------------------------------------------
            # SAVE PAYMONGO IDENTIFIERS
            # ------------------------------------------------

            if (
                paymongo_link_id
                and hasattr(
                    participant_payment,
                    "paymongo_link_id"
                )
            ):

                participant_payment.paymongo_link_id = (
                    paymongo_link_id
                )

            if (
                paymongo_payment_id
                and hasattr(
                    participant_payment,
                    "paymongo_payment_id"
                )
            ):

                participant_payment.paymongo_payment_id = (
                    paymongo_payment_id
                )

            if (
                paymongo_reference
                and hasattr(
                    participant_payment,
                    "paymongo_reference"
                )
            ):

                participant_payment.paymongo_reference = (
                    paymongo_reference
                )

            # ------------------------------------------------
            # MARK LOCAL PAYMENT PAID
            #
            # This is intentionally idempotent.
            # If PayMongo sends the webhook twice, it stays Paid.
            # ------------------------------------------------

            previous_payment_status = str(
                getattr(
                    participant_payment,
                    "status",
                    ""
                )
                or ""
            ).strip().lower()

            participant_payment.status = (
                "Paid"
            )

            if hasattr(
                participant_payment,
                "paid_at"
            ):

                if (
                    previous_payment_status !=
                    "paid"
                ):

                    participant_payment.paid_at = (
                        now
                    )

                elif not participant_payment.paid_at:

                    participant_payment.paid_at = (
                        now
                    )

            # ------------------------------------------------
            # T-SHIRT
            # ------------------------------------------------

            if tshirt_selected:

                print(
                    "Updating T-Shirt -> Paid"
                )

                if hasattr(
                    participant,
                    "tshirt_status"
                ):

                    participant.tshirt_status = (
                        "Paid"
                    )

                if (
                    tshirt_size
                    and
                    hasattr(
                        participant,
                        "tshirt_size"
                    )
                ):

                    participant.tshirt_size = (
                        tshirt_size
                    )

            # ------------------------------------------------
            # LANYARD
            # ------------------------------------------------

            if lanyard_selected:

                print(
                    "Updating Lanyard -> Paid"
                )

                if hasattr(
                    participant,
                    "lanyard_status"
                ):

                    participant.lanyard_status = (
                        "Paid"
                    )

                else:

                    print(
                        "WARNING: Participant has no "
                        "lanyard_status column."
                    )

            # ------------------------------------------------
            # REGISTRATION STATUS
            #
            # Lanyard is mandatory.
            #
            # IMPORTANT:
            # Only change registration status based on the
            # resulting lanyard status.
            # ------------------------------------------------

            lanyard_status = str(
                getattr(
                    participant,
                    "lanyard_status",
                    ""
                )
                or ""
            ).strip().lower()

            lanyard_paid = (
                lanyard_status ==
                "paid"
            )

            if hasattr(
                participant,
                "registration_status"
            ):

                if lanyard_paid:

                    participant.registration_status = (
                        "Confirmed"
                    )

                # Do NOT force Pending here if this webhook
                # was only for another optional item.
                #
                # Existing registration state is preserved
                # when the mandatory lanyard is still unpaid.

            # ------------------------------------------------
            # UPDATED TIME
            # ------------------------------------------------

            if hasattr(
                participant,
                "updated_at"
            ):

                participant.updated_at = (
                    now
                )

            # ------------------------------------------------
            # ADD RESULT
            # ------------------------------------------------

            processed_participants.append({
                "payment_id":
                    participant_payment.id,

                "participant_id":
                    participant.id,

                "registration_number":
                    getattr(
                        participant,
                        "registration_number",
                        None
                    ),

                "payment_status":
                    participant_payment.status,

                "tshirt_selected":
                    tshirt_selected,

                "tshirt_status":
                    getattr(
                        participant,
                        "tshirt_status",
                        None
                    ),

                "tshirt_size":
                    getattr(
                        participant,
                        "tshirt_size",
                        None
                    ),

                "lanyard_selected":
                    lanyard_selected,

                "lanyard_status":
                    getattr(
                        participant,
                        "lanyard_status",
                        None
                    ),

                "registration_status":
                    getattr(
                        participant,
                        "registration_status",
                        None
                    )
            })

        # ====================================================
        # FLUSH EVERYTHING
        # ====================================================

        try:

            db.flush()

            print("=" * 80)
            print(
                "ALL PARTICIPANT CHANGES FLUSHED"
            )
            print("=" * 80)

        except Exception as e:

            db.rollback()

            print(
                "Participant flush failed:",
                repr(e)
            )

            return JSONResponse(
                status_code=500,
                content={
                    "received": True,
                    "processed": False,
                    "payment_type":
                        payment_type,
                    "message":
                        "Participant database update failed."
                }
            )

        # ====================================================
        # COMMIT EVERYTHING AS ONE TRANSACTION
        # ====================================================

        try:

            db.commit()

            print("=" * 80)
            print(
                "PARTICIPANT PAYMENT DATABASE UPDATE SUCCESSFUL"
            )
            print(
                "Participant Count:",
                len(
                    processed_participants
                )
            )
            print("=" * 80)

        except Exception as e:

            db.rollback()

            print(
                "Participant commit failed:",
                repr(e)
            )

            return JSONResponse(
                status_code=500,
                content={
                    "received": True,
                    "processed": False,
                    "payment_type":
                        payment_type,
                    "message":
                        "Participant database update failed."
                }
            )

        # ====================================================
        # REFRESH AND VERIFY
        # ====================================================

        final_participants = []

        for participant_payment in participant_payments:

            try:

                db.refresh(
                    participant_payment
                )

            except Exception as e:

                print(
                    "Payment refresh failed:",
                    repr(e)
                )

            participant_id = getattr(
                participant_payment,
                "participant_id",
                None
            )

            participant = None

            if participant_id:

                participant = (
                    db.query(
                        Participant
                    )
                    .filter(
                        Participant.id ==
                        participant_id
                    )
                    .first()
                )

            if not participant:
                continue

            final_lanyard_status = getattr(
                participant,
                "lanyard_status",
                None
            )

            final_tshirt_status = getattr(
                participant,
                "tshirt_status",
                None
            )

            final_registration_status = getattr(
                participant,
                "registration_status",
                None
            )

            final_lanyard_paid = (
                str(
                    final_lanyard_status
                    or ""
                ).strip().lower()
                ==
                "paid"
            )

            final_participants.append({
                "payment_id":
                    participant_payment.id,

                "participant_id":
                    participant.id,

                "registration_number":
                    getattr(
                        participant,
                        "registration_number",
                        None
                    ),

                "payment_status":
                    participant_payment.status,

                "tshirt_selected":
                    bool(
                        getattr(
                            participant_payment,
                            "tshirt_selected",
                            False
                        )
                    ),

                "tshirt_status":
                    final_tshirt_status,

                "lanyard_selected":
                    bool(
                        getattr(
                            participant_payment,
                            "lanyard_selected",
                            False
                        )
                    ),

                "lanyard_status":
                    final_lanyard_status,

                "lanyard_paid":
                    final_lanyard_paid,

                "registration_status":
                    final_registration_status
            })

            print("=" * 80)
            print(
                "FINAL PARTICIPANT STATUS"
            )
            print(
                "Payment ID:",
                participant_payment.id
            )
            print(
                "Participant ID:",
                participant.id
            )
            print(
                "Payment Status:",
                participant_payment.status
            )
            print(
                "T-Shirt Status:",
                final_tshirt_status
            )
            print(
                "Lanyard Status:",
                final_lanyard_status
            )
            print(
                "Registration Status:",
                final_registration_status
            )
            print("=" * 80)

        # ====================================================
        # PARTICIPANT EMAIL
        #
        # Send confirmation for each participant.
        # A failed email must NOT undo the successful payment.
        # ====================================================

        email_results = []

        for participant_payment in participant_payments:

            participant_id = getattr(
                participant_payment,
                "participant_id",
                None
            )

            if not participant_id:
                continue

            participant = (
                db.query(
                    Participant
                )
                .filter(
                    Participant.id ==
                    participant_id
                )
                .first()
            )

            if not participant:
                continue

            participant_email = getattr(
                participant,
                "email",
                None
            )

            if not participant_email:

                print(
                    "Participant Gmail skipped: no email.",
                    participant.id
                )

                email_results.append({
                    "participant_id":
                        participant.id,
                    "sent":
                        False
                })

                continue

            gmail_success = False

            try:

                gmail_success = bool(
                    await send_participant_payment_confirmation_email(
                        participant,
                        participant_payment
                    )
                )

                print(
                    "Participant Gmail Result:",
                    participant.id,
                    gmail_success
                )

            except Exception as e:

                print(
                    "Participant Gmail failed:",
                    participant.id,
                    repr(e)
                )

            email_results.append({
                "participant_id":
                    participant.id,
                "sent":
                    gmail_success
            })

        # ====================================================
        # FINAL RESULT
        # ====================================================

        all_payment_rows_paid = all(
            str(
                getattr(
                    p,
                    "status",
                    ""
                )
                or ""
            ).strip().lower()
            ==
            "paid"
            for p in participant_payments
        )

        all_lanyards_paid = all(
            item.get(
                "lanyard_paid",
                False
            )
            for item in final_participants
        )

        is_bulk = (
            len(
                participant_payments
            ) > 1
            or
            payment_type == "bulk"
        )

        print("=" * 80)
        print(
            "PARTICIPANT PAYMENT COMPLETED"
        )
        print(
            "Bulk:",
            is_bulk
        )
        print(
            "Payment Rows:",
            len(
                participant_payments
            )
        )
        print(
            "All Payment Rows Paid:",
            all_payment_rows_paid
        )
        print(
            "All Lanyards Paid:",
            all_lanyards_paid
        )
        print("=" * 80)

        return {
            "received": True,
            "processed": True,

            "payment_type":
                "bulk"
                if is_bulk
                else "participant",

            "event_id":
                event_id,

            "payment_id":
                payment.id,

            "payment_ids":
                [
                    p.id
                    for p in participant_payments
                ],

            "participant_ids":
                [
                    p.participant_id
                    for p in participant_payments
                ],

            "participant_count":
                len(
                    participant_payments
                ),

            "participants":
                final_participants,

            "payment_status":
                "Paid"
                if all_payment_rows_paid
                else "Pending",

            "payment_success":
                all_payment_rows_paid,

            "all_lanyards_paid":
                all_lanyards_paid,

            "paymongo_amount":
                paymongo_amount,

            "expected_amount":
                expected_participant_amount,

            "paymongo_reference":
                paymongo_reference,

            "paymongo_payment_id":
                paymongo_payment_id,

            "paymongo_link_id":
                paymongo_link_id,

            "email_results":
                email_results
        }

    # ========================================================
    # ========================================================
    # STORE PAYMENT
    # ========================================================
    # ========================================================

    elif payment_type == "store":

        print("=" * 80)
        print(
            "PROCESSING STORE PAYMENT"
        )
        print("=" * 80)

        # ----------------------------------------------------
        # RESOLVE STORE ORDER ID
        # ----------------------------------------------------

        if not store_order_id:

            store_order_id = getattr(
                payment,
                "store_order_id",
                None
            )

            if store_order_id:

                store_order_id = str(
                    store_order_id
                ).strip()

        if not store_order_id:

            db.rollback()

            return {
                "received": True,
                "processed": False,
                "payment_type": "store",
                "payment_id":
                    payment.id,
                "message":
                    "Store order ID is missing."
            }

        # ----------------------------------------------------
        # FIND ALL STORE PAYMENT ROWS
        # ----------------------------------------------------

        store_payments = (
            db.query(
                Payment
            )
            .filter(
                Payment.store_order_id ==
                store_order_id,
                Payment.payment_type.ilike(
                    "Store"
                )
            )
            .order_by(
                Payment.id.asc()
            )
            .with_for_update()
            .all()
        )

        # ----------------------------------------------------
        # FALLBACK LINK ID
        # ----------------------------------------------------

        if (
            not store_payments
            and paymongo_link_id
        ):

            store_payments = (
                db.query(
                    Payment
                )
                .filter(
                    Payment.paymongo_link_id ==
                    paymongo_link_id,
                    Payment.payment_type.ilike(
                        "Store"
                    )
                )
                .order_by(
                    Payment.id.asc()
                )
                .with_for_update()
                .all()
            )

        if not store_payments:

            db.rollback()

            return {
                "received": True,
                "processed": False,
                "payment_type": "store",
                "store_order_id":
                    store_order_id,
                "message":
                    "No store payment rows found for this order."
            }

        print(
            "Store payment rows:",
            len(
                store_payments
            )
        )

        # ----------------------------------------------------
        # SAVE PAYMONGO INFORMATION
        # ----------------------------------------------------

        for store_payment in store_payments:

            if (
                paymongo_link_id
                and hasattr(
                    store_payment,
                    "paymongo_link_id"
                )
            ):

                store_payment.paymongo_link_id = (
                    paymongo_link_id
                )

            if (
                paymongo_payment_id
                and hasattr(
                    store_payment,
                    "paymongo_payment_id"
                )
            ):

                store_payment.paymongo_payment_id = (
                    paymongo_payment_id
                )

            if (
                paymongo_reference
                and hasattr(
                    store_payment,
                    "paymongo_reference"
                )
            ):

                store_payment.paymongo_reference = (
                    paymongo_reference
                )

        # ----------------------------------------------------
        # CALCULATE CART TOTAL
        # ----------------------------------------------------

        expected_cart_amount = 0

        for store_payment in store_payments:

            try:

                row_amount = int(
                    getattr(
                        store_payment,
                        "amount",
                        0
                    )
                    or 0
                )

            except (
                ValueError,
                TypeError
            ):

                row_amount = 0

            if row_amount <= 0:

                db.rollback()

                return {
                    "received": True,
                    "processed": False,
                    "payment_type":
                        "store",
                    "store_order_id":
                        store_order_id,
                    "payment_id":
                        store_payment.id,
                    "message":
                        "Invalid store payment row amount."
                }

            expected_cart_amount += (
                row_amount
            )

        # ----------------------------------------------------
        # VERIFY AMOUNT
        # ----------------------------------------------------

        if (
            paymongo_amount > 0
            and
            paymongo_amount !=
            expected_cart_amount
        ):

            print(
                "STORE CART AMOUNT MISMATCH"
            )

            db.rollback()

            return {
                "received": True,
                "processed": False,
                "payment_type":
                    "store",
                "store_order_id":
                    store_order_id,
                "paymongo_amount":
                    paymongo_amount,
                "expected_amount":
                    expected_cart_amount,
                "message":
                    "Payment amount does not match the store cart total."
            }

        # ----------------------------------------------------
        # CHECK ALREADY PAID
        # ----------------------------------------------------

        all_already_paid = all(
            str(
                getattr(
                    p,
                    "status",
                    ""
                )
                or ""
            ).strip().lower()
            ==
            "paid"
            for p in store_payments
        )

        if all_already_paid:

            try:
                db.commit()
            except Exception:
                db.rollback()

            return {
                "received": True,
                "processed": True,
                "already_processed": True,
                "payment_type":
                    "store",
                "store_order_id":
                    store_order_id,
                "payment_id":
                    payment.id,
                "payment_ids":
                    [
                        p.id
                        for p in store_payments
                    ],
                "payment_status":
                    "Paid",
                "payment_success":
                    True
            }

        # ----------------------------------------------------
        # PROCESS UNPAID STORE ROWS
        # ----------------------------------------------------

        unpaid_payments = [
            p
            for p in store_payments
            if str(
                getattr(
                    p,
                    "status",
                    ""
                )
                or ""
            ).strip().lower()
            != "paid"
        ]

        store_items_to_update = []

        # ----------------------------------------------------
        # VALIDATE ALL INVENTORY FIRST
        # ----------------------------------------------------

        for store_payment in unpaid_payments:

            store_item_id = getattr(
                store_payment,
                "store_item_id",
                None
            )

            if not store_item_id:

                db.rollback()

                return {
                    "received": True,
                    "processed": False,
                    "payment_type":
                        "store",
                    "store_order_id":
                        store_order_id,
                    "payment_id":
                        store_payment.id,
                    "message":
                        "Store item ID is missing."
                }

            try:

                store_quantity = int(
                    getattr(
                        store_payment,
                        "store_quantity",
                        1
                    )
                    or 1
                )

            except (
                ValueError,
                TypeError
            ):

                store_quantity = 0

            if store_quantity <= 0:

                db.rollback()

                return {
                    "received": True,
                    "processed": False,
                    "payment_type":
                        "store",
                    "store_order_id":
                        store_order_id,
                    "payment_id":
                        store_payment.id,
                    "message":
                        "Invalid store quantity."
                }

            store_item = (
                db.query(
                    StoreItem
                )
                .filter(
                    StoreItem.id ==
                    store_item_id
                )
                .with_for_update()
                .first()
            )

            if not store_item:

                db.rollback()

                return {
                    "received": True,
                    "processed": False,
                    "payment_type":
                        "store",
                    "store_order_id":
                        store_order_id,
                    "payment_id":
                        store_payment.id,
                    "store_item_id":
                        store_item_id,
                    "message":
                        "Store item not found."
                }

            try:

                current_inventory = int(
                    store_item.quantity
                    or 0
                )

            except (
                ValueError,
                TypeError
            ):

                current_inventory = 0

            if current_inventory < store_quantity:

                db.rollback()

                return {
                    "received": True,
                    "processed": False,
                    "payment_type":
                        "store",
                    "store_order_id":
                        store_order_id,
                    "payment_id":
                        store_payment.id,
                    "store_item_id":
                        store_item.id,
                    "item_name":
                        store_item.item_name,
                    "requested_quantity":
                        store_quantity,
                    "available_quantity":
                        current_inventory,
                    "message":
                        "Insufficient inventory."
                }

            store_items_to_update.append({
                "payment":
                    store_payment,
                "store_item":
                    store_item,
                "quantity":
                    store_quantity
            })

        # ----------------------------------------------------
        # PROCESS ALL VALIDATED STORE ITEMS
        # ----------------------------------------------------

        processed_items = []

        now = datetime.datetime.now()

        for entry in store_items_to_update:

            store_payment = entry[
                "payment"
            ]

            store_item = entry[
                "store_item"
            ]

            store_quantity = entry[
                "quantity"
            ]

            # ------------------------------------------------
            # MARK PAID
            # ------------------------------------------------

            store_payment.status = (
                "Paid"
            )

            if hasattr(
                store_payment,
                "paid_at"
            ):

                store_payment.paid_at = (
                    now
                )

            # ------------------------------------------------
            # PAYMONGO IDS
            # ------------------------------------------------

            if (
                paymongo_link_id
                and hasattr(
                    store_payment,
                    "paymongo_link_id"
                )
            ):

                store_payment.paymongo_link_id = (
                    paymongo_link_id
                )

            if (
                paymongo_payment_id
                and hasattr(
                    store_payment,
                    "paymongo_payment_id"
                )
            ):

                store_payment.paymongo_payment_id = (
                    paymongo_payment_id
                )

            if (
                paymongo_reference
                and hasattr(
                    store_payment,
                    "paymongo_reference"
                )
            ):

                store_payment.paymongo_reference = (
                    paymongo_reference
                )

            # ------------------------------------------------
            # REDUCE INVENTORY
            # ------------------------------------------------

            old_inventory = int(
                store_item.quantity
                or 0
            )

            store_item.quantity = (
                old_inventory -
                store_quantity
            )

            if hasattr(
                store_item,
                "updated_at"
            ):

                store_item.updated_at = (
                    now
                )

            processed_items.append({
                "payment_id":
                    store_payment.id,

                "store_item_id":
                    store_item.id,

                "item_name":
                    store_item.item_name,

                "quantity":
                    store_quantity,

                "remaining_inventory":
                    store_item.quantity,

                "payment_status":
                    store_payment.status
            })

        # ----------------------------------------------------
        # COMMIT STORE TRANSACTION
        # ----------------------------------------------------

        try:

            db.commit()

        except Exception as e:

            db.rollback()

            print(
                "Store commit failed:",
                repr(e)
            )

            return JSONResponse(
                status_code=500,
                content={
                    "received": True,
                    "processed": False,
                    "payment_type":
                        "store",
                    "store_order_id":
                        store_order_id,
                    "message":
                        "Store cart database update failed."
                }
            )

        # ----------------------------------------------------
        # FINAL STATUS
        # ----------------------------------------------------

        final_order_status = (
            "Paid"
            if all(
                str(
                    getattr(
                        p,
                        "status",
                        ""
                    )
                    or ""
                ).strip().lower()
                ==
                "paid"
                for p in store_payments
            )
            else
            "Pending"
        )

        print("=" * 80)
        print(
            "STORE PAYMENT COMPLETED"
        )
        print(
            "Store Order ID:",
            store_order_id
        )
        print(
            "Payment Rows:",
            len(
                store_payments
            )
        )
        print(
            "Order Status:",
            final_order_status
        )
        print("=" * 80)

        return {
            "received": True,
            "processed": True,
            "payment_type":
                "store",
            "event_id":
                event_id,
            "store_order_id":
                store_order_id,
            "payment_id":
                payment.id,
            "payment_ids":
                [
                    p.id
                    for p in store_payments
                ],
            "item_count":
                len(
                    store_payments
                ),
            "items":
                processed_items,
            "paymongo_amount":
                paymongo_amount,
            "expected_cart_amount":
                expected_cart_amount,
            "total_amount":
                expected_cart_amount / 100,
            "payment_status":
                final_order_status,
            "payment_success":
                final_order_status == "Paid",
            "paymongo_reference":
                paymongo_reference,
            "paymongo_payment_id":
                paymongo_payment_id,
            "paymongo_link_id":
                paymongo_link_id
        }

    # ========================================================
    # UNKNOWN PAYMENT TYPE
    # ========================================================

    db.rollback()

    print("=" * 80)
    print(
        "UNSUPPORTED PAYMENT TYPE"
    )
    print(
        "Payment Type:",
        payment_type
    )
    print("=" * 80)

    return {
        "received": True,
        "processed": False,
        "payment_id":
            payment.id,
        "payment_type":
            payment_type,
        "message":
            "Payment type is not supported."
    }




































    
    
# ============================================================
# CREATE CASH SPONSORSHIP
# ============================================================
#
# IMPORTANT:
#
# This endpoint ONLY creates the sponsorship/payment.
#
# The donation is NOT added to CashDonationTotal yet because
# the PayMongo payment is still Pending.
#
# cash_total_added:
#
#     0 = donation has NOT yet been added to CashDonationTotal
#
#     donation_amount = donation has already been added
#
# The payment-success/webhook endpoint is responsible for:
#
#     1. Marking payment as Paid
#     2. Adding donation_amount to CashDonationTotal
#     3. Setting cash_total_added = donation_amount
#
# This prevents the same PayMongo payment from being added
# to CashDonationTotal multiple times.
#
# ============================================================

@app.post("/sponsorship/create_cash")
def create_cash_sponsorship(
    data: CashSponsorshipCreate,
    db: Session = Depends(get_db)
):

    # ========================================================
    # CLEAN INPUT
    # ========================================================

    selected_tier = (
        data.selected_tier.strip()
    )

    sponsor_name = (
        data.sponsor_name.strip()
    )

    local_church = (
        data.local_church.strip()
    )

    sector = (
        data.sector.strip()
    )

    amount = Decimal(
        str(data.donation_amount)
    ).quantize(
        Decimal("0.01")
    )

    # ========================================================
    # VALIDATE AMOUNT
    # ========================================================

    if amount <= 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "Donation amount must be "
                "greater than ₱0.00."
            )
        )

    # ========================================================
    # DETERMINE CORRECT TIER
    # ========================================================

    correct_tier = (
        determine_sponsorship_tier(
            amount
        )
    )

    # ========================================================
    # CHECK SELECTED TIER
    # ========================================================

    if (
        selected_tier.lower()
        !=
        correct_tier.lower()
    ):

        if (
            correct_tier
            ==
            "1st (Bronze) Tier"
        ):

            message = (
                f"Your donation of "
                f"₱{amount:,.2f} belongs to "
                f"the 1st (Bronze) Tier, "
                f"which is below ₱1,000. "
                f"Please reselect the "
                f"1st (Bronze) Tier package."
            )

        elif (
            correct_tier
            ==
            "2nd (Silver) Tier"
        ):

            message = (
                f"Your donation of "
                f"₱{amount:,.2f} belongs to "
                f"the 2nd (Silver) Tier, "
                f"which is ₱1,000 to below "
                f"₱2,000. Please reselect "
                f"the 2nd (Silver) Tier package."
            )

        elif (
            correct_tier
            ==
            "3rd (Gold) Tier"
        ):

            message = (
                f"Your donation of "
                f"₱{amount:,.2f} belongs to "
                f"the 3rd (Gold) Tier, "
                f"which is ₱2,000 to below "
                f"₱3,000. Please reselect "
                f"the 3rd (Gold) Tier package."
            )

        else:

            message = (
                f"Your donation of "
                f"₱{amount:,.2f} belongs to "
                f"the 4th (Diamond) Tier, "
                f"which is ₱3,000 and above. "
                f"Please reselect the "
                f"4th (Diamond) Tier package."
            )

        raise HTTPException(
            status_code=400,
            detail=message
        )

    # ========================================================
    # CREATE LOCAL SPONSORSHIP RECORD
    # ========================================================
    #
    # IMPORTANT:
    #
    # cash_total_added = 0
    #
    # The donation is NOT yet available for Finding Sponsor
    # participants.
    #
    # It becomes available only after PayMongo confirms
    # successful payment.
    #
    # ========================================================

    sponsorship = CashSponsorship(

        sponsor_name=sponsor_name,

        local_church=local_church,

        contact=(
            data.contact.strip()
            if data.contact
            else None
        ),

        sector=sector,

        email=(
            str(data.email)
            if data.email
            else None
        ),

        selected_tier=correct_tier,

        donation_amount=int(
            amount * 100
        ),

        payment_status="Pending",

        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        # Nothing has been added to CashDonationTotal yet.
        #
        # This value will be updated by the payment-success
        # / webhook logic.
        #
        cash_total_added=0

    )

    db.add(
        sponsorship
    )

    db.commit()

    db.refresh(
        sponsorship
    )

    # ========================================================
    # PAYMONGO AMOUNT
    # ========================================================

    paymongo_amount = int(
        amount * 100
    )

    # ========================================================
    # DESCRIPTION
    # ========================================================

    description = (
        f"Sponsorship - "
        f"{correct_tier} - "
        f"{sponsor_name}"
    )

    # ========================================================
    # REMARKS
    # ========================================================

    remarks = (
        f"Sponsorship ID: "
        f"{sponsorship.id}"
    )

    # ========================================================
    # PAYMONGO SECRET KEY
    # ========================================================

    secret_key = os.getenv(
        "PAYMONGO_SECRET_KEY"
    )

    if not secret_key:

        sponsorship.payment_status = (
            "Failed"
        )

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "PAYMONGO_SECRET_KEY "
                "is not configured."
            )
        )

    # ========================================================
    # PAYMONGO PAYLOAD
    # ========================================================

    payload = {

        "amount":
            paymongo_amount,

        "currency":
            "PHP",

        "description":
            description,

        "remarks":
            remarks,

        "metadata": {

            "type":
                "cash_sponsorship",

            "sponsorship_id":
                str(sponsorship.id),

            "sponsor_name":
                sponsor_name,

            "tier":
                correct_tier,

            "email":
                (
                    str(data.email)
                    if data.email
                    else ""
                )

        }

    }

    # ========================================================
    # CREATE PAYMONGO PAYMENT LINK
    # ========================================================

    try:

        response = httpx.post(

            "https://api.paymongo.com/v1/payment_links",

            auth=(
                secret_key,
                ""
            ),

            headers={

                "Content-Type":
                    "application/json",

                "Accept":
                    "application/json",

                "Idempotency-Key":
                    (
                        f"sponsorship-"
                        f"{sponsorship.id}-"
                        f"{uuid.uuid4()}"
                    )

            },

            json=payload,

            timeout=30

        )

    except Exception as e:

        sponsorship.payment_status = (
            "Failed"
        )

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to connect to PayMongo: "
                f"{str(e)}"
            )
        )

    # ========================================================
    # PAYMONGO ERROR
    # ========================================================

    if response.status_code not in [
        200,
        201
    ]:

        try:

            error_data = (
                response.json()
            )

        except Exception:

            error_data = {
                "detail":
                    response.text
            }

        sponsorship.payment_status = (
            "Failed"
        )

        db.commit()

        raise HTTPException(
            status_code=502,
            detail={

                "message":
                    "PayMongo rejected "
                    "the payment link.",

                "paymongo":
                    error_data

            }
        )

    # ========================================================
    # PARSE PAYMONGO RESPONSE
    # ========================================================

    try:

        result = (
            response.json()
        )

        payment_data = (
            result.get(
                "data",
                {}
            )
        )

        payment_link_id = (
            payment_data.get(
                "id"
            )
        )

        payment_attributes = (
            payment_data.get(
                "attributes",
                {}
            )
        )

        payment_url = (

            payment_attributes.get(
                "checkout_url"
            )

            or

            payment_attributes.get(
                "url"
            )

            or

            payment_data.get(
                "url"
            )

        )

        reference_number = (

            payment_attributes.get(
                "reference_number"
            )

            or

            payment_data.get(
                "reference_number"
            )

        )

    except Exception:

        sponsorship.payment_status = (
            "Failed"
        )

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "Invalid response received "
                "from PayMongo."
            )
        )

    # ========================================================
    # VALIDATE PAYMENT LINK ID
    # ========================================================

    if not payment_link_id:

        sponsorship.payment_status = (
            "Failed"
        )

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "PayMongo did not return "
                "a payment link ID."
            )
        )

    # ========================================================
    # VALIDATE PAYMENT URL
    # ========================================================

    if not payment_url:

        sponsorship.payment_status = (
            "Failed"
        )

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "PayMongo did not return "
                "a payment URL."
            )
        )

    # ========================================================
    # SAVE PAYMONGO DETAILS
    # ========================================================

    sponsorship.paymongo_link_id = (
        payment_link_id
    )

    sponsorship.paymongo_reference = (
        reference_number
    )

    sponsorship.payment_url = (
        payment_url
    )

    # --------------------------------------------------------
    # REMAIN PENDING
    # --------------------------------------------------------

    sponsorship.payment_status = (
        "Pending"
    )

    # --------------------------------------------------------
    # STILL NOT ADDED TO CASH DONATION TOTAL
    # --------------------------------------------------------

    sponsorship.cash_total_added = 0

    db.commit()

    db.refresh(
        sponsorship
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "success":
            True,

        "message":
            "Sponsorship created successfully. "
            "Payment is currently pending.",

        "sponsorship_id":
            sponsorship.id,

        "sponsor_name":
            sponsorship.sponsor_name,

        "tier":
            correct_tier,

        "donation_amount":
            float(amount),

        "payment_status":
            sponsorship.payment_status,

        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        # This confirms to the frontend that the money has
        # NOT yet entered the available sponsorship balance.
        #
        "cash_total_added":
            sponsorship.cash_total_added,

        "cash_total_added_display":
            "₱0.00",

        "cash_donation_total_updated":
            False,

        "payment_id":
            payment_link_id,

        "paymongo_link_id":
            payment_link_id,

        "reference_number":
            reference_number,

        "payment_url":
            payment_url

    }
    
    
    
    
    
    
    
    
    


# ============================================================
# GET AVAILABLE SPONSORSHIP ITEMS
# ============================================================

@app.get("/sponsorship/items")
def get_sponsorship_items(
    db: Session = Depends(get_db)
):

    items = db.query(
        SponsorshipItem
    ).filter(
        SponsorshipItem.is_active == True
    ).order_by(
        SponsorshipItem.item_name.asc()
    ).all()

    result = []

    for item in items:

        result.append({

            "id":
                item.id,

            "item_name":
                item.item_name,

            "description":
                item.description,

            "total_quantity":
                item.total_quantity,

            "remaining_quantity":
                item.remaining_quantity,

            "unit":
                item.unit,

            "available":
                item.remaining_quantity > 0

        })

    return result       





















# ============================================================
# SPONSORSHIP PAYMENT STATUS
# ============================================================
#
# Used by the cash sponsorship payment page to continuously
# check whether the sponsorship payment has been completed.
#
# The frontend sends the PayMongo Link ID:
#
#     /sponsorship/payment/status/{payment_id}
#
# The endpoint first finds the CashSponsorship by the stored
# PayMongo Link ID.
#
# After the webhook receives payment.paid, the webhook updates:
#
#     payment_status = "Paid"
#
# Therefore this endpoint will automatically return:
#
#     paid = True
#
# ============================================================

@app.get("/sponsorship/payment/status/{payment_id}")
def sponsorship_payment_status(
    payment_id: str,
    db: Session = Depends(get_db)
):

    # ======================================================
    # FIND SPONSORSHIP BY PAYMONGO LINK ID
    # ======================================================

    sponsorship = (
        db.query(CashSponsorship)
        .filter(
            CashSponsorship.paymongo_link_id == payment_id
        )
        .first()
    )

    # ======================================================
    # SPONSORSHIP NOT FOUND
    # ======================================================

    if not sponsorship:

        print("=" * 70)
        print("SPONSORSHIP PAYMENT STATUS")
        print("=" * 70)
        print("Requested Payment ID:", payment_id)
        print("SPONSORSHIP NOT FOUND")
        print("=" * 70)

        return {
            "success": False,
            "found": False,
            "payment_status": "Not Found",
            "paid": False
        }

    # ======================================================
    # GET PAYMENT STATUS
    # ======================================================

    payment_status = str(
        sponsorship.payment_status or "Pending"
    ).strip().lower()

    # ======================================================
    # DETERMINE IF PAID
    # ======================================================

    paid = payment_status in [
        "paid",
        "succeeded",
        "successful",
        "completed"
    ]

    # ======================================================
    # DEBUG LOG
    # ======================================================

    print("=" * 70)
    print("SPONSORSHIP PAYMENT STATUS")
    print("=" * 70)

    print(
        "Requested Payment ID:",
        payment_id
    )

    print(
        "Sponsorship ID:",
        sponsorship.id
    )

    print(
        "PayMongo Link ID:",
        sponsorship.paymongo_link_id
    )

    print(
        "PayMongo Reference:",
        sponsorship.paymongo_reference
    )

    print(
        "Payment Status:",
        sponsorship.payment_status
    )

    print(
        "Paid:",
        paid
    )

    print("=" * 70)

    # ======================================================
    # RESPONSE
    # ======================================================

    return {

        "success":
            True,

        "found":
            True,

        "sponsorship_id":
            sponsorship.id,

        "payment_status":
            sponsorship.payment_status or "Pending",

        "paid":
            paid,

        "paymongo_link_id":
            sponsorship.paymongo_link_id,

        "paymongo_reference":
            sponsorship.paymongo_reference
    }










# ============================================================
# CREATE ITEM SPONSORSHIP
# ============================================================

@app.post("/sponsorship/create_item")
async def create_item_sponsorship(
    data: ItemSponsorshipCreate,
    db: Session = Depends(get_db)
):

    print()
    print("============================================================")
    print("ITEM SPONSORSHIP REQUEST")
    print("============================================================")

    print("Sponsor:", data.sponsor_name)
    print("Local Church:", data.local_church)
    print("Visiting Church:", getattr(data, "visiting_church", None))
    print("Sector:", data.sector)
    print("Contact:", data.contact)
    print("Email:", data.email)
    print("Items:", data.items)

    # ========================================================
    # NORMALIZE CONTACT / EMAIL
    # ========================================================

    contact = (
        str(data.contact).strip()
        if data.contact
        else "0910101010"
    )

    email = (
        str(data.email).strip()
        if data.email
        else "optional@mail.com"
    )

    sponsor_name = (
        data.sponsor_name.strip()
    )

    local_church = (
        data.local_church.strip()
    )

    sector = (
        data.sector.strip()
    )

    visiting_church = getattr(
        data,
        "visiting_church",
        None
    )

    if visiting_church:
        visiting_church = (
            visiting_church.strip()
        )

    # ========================================================
    # VALIDATE BASIC INFORMATION
    # ========================================================

    if not sponsor_name:

        raise HTTPException(
            status_code=400,
            detail="Sponsor name is required."
        )

    if not local_church:

        raise HTTPException(
            status_code=400,
            detail="Local church is required."
        )

    if not sector:

        raise HTTPException(
            status_code=400,
            detail="Sector is required."
        )

    # ========================================================
    # VALIDATE ITEMS
    # ========================================================

    if not data.items:

        raise HTTPException(
            status_code=400,
            detail="Please select at least one item."
        )

    # ========================================================
    # PREVENT DUPLICATE ITEM IDS
    # ========================================================

    item_ids = []

    for selected_item in data.items:

        try:

            item_id = int(
                selected_item.item_id
            )

        except (
            ValueError,
            TypeError
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid sponsorship item ID."
            )

        if item_id in item_ids:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Item {item_id} was selected "
                    f"more than once."
                )
            )

        item_ids.append(item_id)

    # ========================================================
    # START TRANSACTION
    # ========================================================

    created_donations = []

    try:

        # ====================================================
        # PROCESS EVERY SELECTED ITEM
        # ====================================================

        for selected_item in data.items:

            item = db.query(
                SponsorshipItem
            ).filter(
                SponsorshipItem.id ==
                selected_item.item_id,

                SponsorshipItem.is_active ==
                True
            ).first()

            # ------------------------------------------------
            # ITEM NOT FOUND
            # ------------------------------------------------

            if not item:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Sponsorship item "
                        f"{selected_item.item_id} "
                        f"was not found."
                    )
                )

            # ------------------------------------------------
            # QUANTITY
            # ------------------------------------------------

            try:

                quantity = int(
                    selected_item.quantity
                )

            except (
                ValueError,
                TypeError
            ):

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid quantity for "
                        f"{item.item_name}."
                    )
                )

            # ------------------------------------------------
            # VALIDATE QUANTITY
            # ------------------------------------------------

            if quantity <= 0:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Quantity for "
                        f"{item.item_name} "
                        f"must be greater than 0."
                    )
                )

            # ------------------------------------------------
            # INVENTORY
            # ------------------------------------------------

            if item.remaining_quantity <= 0:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"{item.item_name} "
                        f"is already fully sponsored."
                    )
                )

            if quantity > item.remaining_quantity:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Only "
                        f"{item.remaining_quantity} "
                        f"{item.unit} remaining for "
                        f"{item.item_name}."
                    )
                )

            # ------------------------------------------------
            # SAVE ORIGINAL INFORMATION
            # ------------------------------------------------

            item_name = item.item_name

            unit = item.unit

            # ------------------------------------------------
            # REDUCE INVENTORY
            # ------------------------------------------------

            item.remaining_quantity -= quantity

            # ------------------------------------------------
            # CREATE DONATION
            #
            # IMPORTANT:
            #
            # visiting_church is NOT passed here because
            # your current ItemSponsorship SQLAlchemy model
            # does not have that column.
            # ------------------------------------------------

            donation = ItemSponsorship(

                sponsor_name=
                    sponsor_name,

                local_church=
                    local_church,

                contact=
                    contact,

                sector=
                    sector,

                email=
                    email,

                item_id=
                    item.id,

                item_name=
                    item_name,

                quantity=
                    quantity,

                status=
                    "Confirmed"
            )

            db.add(donation)

            created_donations.append({

                "donation":
                    donation,

                "item":
                    item,

                "item_name":
                    item_name,

                "unit":
                    unit,

                "quantity":
                    quantity

            })

        # ====================================================
        # COMMIT ALL ITEMS TOGETHER
        # ====================================================

        db.commit()

        # ====================================================
        # REFRESH DONATIONS
        # ====================================================

        for record in created_donations:

            db.refresh(
                record["donation"]
            )

            db.refresh(
                record["item"]
            )

        print()
        print(
            "ITEM SPONSORSHIP DATABASE SAVE SUCCESSFUL"
        )

        # ====================================================
        # SEND ONE CONFIRMATION EMAIL
        # ====================================================

        email_sent = False

        try:

            # ------------------------------------------------
            # If your current email function accepts ONE
            # donation object, send one email per donation.
            # ------------------------------------------------

            for record in created_donations:

                try:

                    await send_item_sponsorship_confirmation_email(
                        record["donation"]
                    )

                    email_sent = True

                except Exception as email_error:

                    print(
                        "Item sponsorship email failed:",
                        repr(email_error)
                    )

        except Exception as e:

            print(
                "Item sponsorship email error:",
                repr(e)
            )

        # ====================================================
        # BUILD ITEM SUMMARY
        # ====================================================

        item_summary = []

        for record in created_donations:

            donation = record["donation"]

            item_summary.append({

                "donation_id":
                    donation.id,

                "item_id":
                    donation.item_id,

                "item":
                    donation.item_name,

                "quantity":
                    donation.quantity,

                "unit":
                    record["unit"],

                "remaining_quantity":
                    record["item"].remaining_quantity,

                "status":
                    donation.status

            })

        # ====================================================
        # THANK YOU MESSAGE
        # ====================================================

        item_text = ", ".join(

            f'{record["quantity"]} '
            f'{record["unit"]} '
            f'{record["item_name"]}'

            for record
            in created_donations

        )

        thank_you_message = (

            f"Thank you {sponsor_name} "
            f"for your item donation: "
            f"{item_text}. "
            f"Please deliver the donation to the "
            f"donation designation area at "
            f"Butuan Grace Baptist Church "
            f"or contact Pastor Edward Deligero "
            f"at 0911 252 3584."

        )

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "success":
                True,

            "message":
                "Item donation recorded successfully.",

            "donation_count":
                len(created_donations),

            "sponsor_name":
                sponsor_name,

            "local_church":
                local_church,

            "visiting_church":
                visiting_church,

            "sector":
                sector,

            "contact":
                contact,

            "email":
                email,

            "items":
                item_summary,

            "email_sent":
                email_sent,

            "thank_you_message":
                thank_you_message

        }

    except HTTPException:

        # ====================================================
        # ROLLBACK
        # ====================================================

        db.rollback()

        raise

    except Exception as e:

        # ====================================================
        # ROLLBACK
        # ====================================================

        db.rollback()

        print()
        print(
            "ITEM SPONSORSHIP DATABASE ERROR:",
            repr(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to record item donation."
            )
        )
        
        



        


# ============================================================
# STORE CATEGORIES
# ============================================================

STORE_CATEGORIES = [
    "clothes",
    "souvenir",
    "others"
]


# ============================================================
# HELPER - STORE ITEM RESPONSE
# ============================================================

# ============================================================
# HELPER - STORE ITEM RESPONSE
# ============================================================

def store_item_response(item):

    item_sizes = []

    if item.sizes:

        try:
            item_sizes = json.loads(item.sizes)

        except Exception:
            item_sizes = []

    return {
        "id": item.id,
        "item_name": item.item_name,
        "description": item.description,
        "category": item.category,
        "quantity": item.quantity,
        "price": item.price,
        "image_url": item.image_url,
        "sizes": item_sizes,
        "available": item.quantity > 0,
        "is_archived": bool(item.is_archived),
        "created_at": item.created_at,
        "updated_at": item.updated_at
    }

# ============================================================
# VIEW ACTIVE STORE
# ============================================================

@app.get("/store")
def view_store(
    db: Session = Depends(get_db)
):

    items = (
        db.query(StoreItem)
        .filter(
            StoreItem.is_archived == False
        )
        .order_by(
            StoreItem.created_at.desc()
        )
        .all()
    )

    return {
        "success": True,
        "items": [
            store_item_response(item)
            for item in items
        ]
    }


# ============================================================
# GET STORE CATEGORIES
# ============================================================

@app.get("/store/categories")
def get_store_categories():

    return {
        "success": True,
        "categories": STORE_CATEGORIES
    }
    
    
    
# ============================================================
# STORE CATEGORIES / SIZES
# ============================================================

STORE_CATEGORIES = [
    "clothes",
    "souvenir",
    "others"
]

STORE_CLOTHING_SIZES = [
    "S",
    "M",
    "L",
    "XL",
    "2XL"
]    


# ============================================================
# CREATE STORE ITEM
# ============================================================

@app.post("/create_store_item")
def create_store_item(
    data: StoreItemCreateSchema,
    db: Session = Depends(get_db)
):

    item_name = (
        data.item_name.strip()
        if data.item_name
        else ""
    )

    if not item_name:
        raise HTTPException(
            status_code=400,
            detail="Item name is required."
        )

    category = (
        data.category.strip().lower()
        if data.category
        else ""
    )

    if category not in STORE_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid store item category. "
                "Allowed categories: "
                + ", ".join(STORE_CATEGORIES)
            )
        )

    if data.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative."
        )

    if data.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Price must be greater than zero."
        )

    # --------------------------------------------------------
    # CLOTHING SIZES
    # --------------------------------------------------------

    sizes = []

    if category == "clothes":

        sizes = data.sizes or []

        sizes = [
            size.strip().upper()
            for size in sizes
            if size and size.strip()
        ]

        if not sizes:
            sizes = STORE_CLOTHING_SIZES

        invalid_sizes = [
            size
            for size in sizes
            if size not in STORE_CLOTHING_SIZES
        ]

        if invalid_sizes:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid clothing size(s): "
                    + ", ".join(invalid_sizes)
                    + ". Allowed sizes: "
                    + ", ".join(STORE_CLOTHING_SIZES)
                )
            )

    else:

        # Souvenir / Others do not need sizes
        sizes = []

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    now = datetime.datetime.now()

    item = StoreItem(
        item_name=item_name,

        description=(
            data.description.strip()
            if data.description
            else None
        ),

        category=category,

        quantity=data.quantity,

        price=data.price,

        image_url=(
            data.image_url.strip()
            if data.image_url
            else None
        ),

        sizes=json.dumps(sizes),

        is_archived=False,

        created_at=now,

        updated_at=now
    )

    db.add(item)

    db.commit()

    db.refresh(item)

    return {
        "success": True,
        "message": "Store item created successfully.",
        "item": store_item_response(item)
    }


# ============================================================
# UPDATE STORE ITEM
# ============================================================

@app.put("/update_store_item/{item_id}")
def update_store_item(
    item_id: int,
    data: StoreItemUpdateSchema,
    db: Session = Depends(get_db)
):

    item = (
        db.query(StoreItem)
        .filter(
            StoreItem.id == item_id,
            StoreItem.is_archived == False
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Store item not found."
        )

    item_name = (
        data.item_name.strip()
        if data.item_name
        else ""
    )

    if not item_name:
        raise HTTPException(
            status_code=400,
            detail="Item name is required."
        )

    category = (
        data.category.strip().lower()
        if data.category
        else ""
    )

    if category not in STORE_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid store item category. "
                "Allowed categories: "
                + ", ".join(STORE_CATEGORIES)
            )
        )

    if data.quantity < 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity cannot be negative."
        )

    if data.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Price must be greater than zero."
        )

    # --------------------------------------------------------
    # SIZES
    # --------------------------------------------------------

    sizes = []

    if category == "clothes":

        sizes = data.sizes or []

        sizes = [
            size.strip().upper()
            for size in sizes
            if size and size.strip()
        ]

        if not sizes:
            sizes = STORE_CLOTHING_SIZES

        invalid_sizes = [
            size
            for size in sizes
            if size not in STORE_CLOTHING_SIZES
        ]

        if invalid_sizes:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid clothing size(s): "
                    + ", ".join(invalid_sizes)
                )
            )

    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    item.item_name = item_name

    item.description = (
        data.description.strip()
        if data.description
        else None
    )

    item.category = category

    item.quantity = data.quantity

    item.price = data.price

    item.image_url = (
        data.image_url.strip()
        if data.image_url
        else None
    )

    item.sizes = json.dumps(sizes)

    item.updated_at = datetime.datetime.now()

    db.commit()

    db.refresh(item)

    return {
        "success": True,
        "message": "Store item updated successfully.",
        "item": store_item_response(item)
    }


# ============================================================
# ARCHIVE STORE ITEM
# ============================================================

@app.delete("/delete_store_item/{item_id}")
def delete_store_item(
    item_id: int,
    db: Session = Depends(get_db)
):

    item = (
        db.query(StoreItem)
        .filter(
            StoreItem.id == item_id,
            StoreItem.is_archived == False
        )
        .first()
    )

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Store item not found."
        )

    item.is_archived = True

    item.updated_at = datetime.datetime.now()

    db.commit()

    return {

        "success": True,

        "message":
            "Store item archived successfully.",

        "item_id":
            item.id

    }
    
















# ============================================================
# CREATE STORE PURCHASE PAYMENT
#
# SUPPORTS:
# - ONE ITEM
# - MULTIPLE ITEMS
# - 1 TO 50 CART ITEMS
#
# ONE CART = ONE PAYMONGO PAYMENT LINK
# ONE CART ITEM = ONE PAYMENT DATABASE ROW
# ALL PAYMENT ROWS SHARE THE SAME store_order_id
# ============================================================

@app.post("/store/purchase")
def create_store_purchase(
    data: StorePurchaseSchema,
    db: Session = Depends(get_db)
):

    # ========================================================
    # VALIDATE CUSTOMER
    # ========================================================

    customer_name = (
        data.customer_name or ""
    ).strip()

    customer_contact = (
        data.customer_contact or ""
    ).strip()

    customer_email = (
        str(data.customer_email or "")
    ).strip()

    if not customer_name:

        raise HTTPException(
            status_code=400,
            detail="Customer name is required."
        )

    if not customer_contact:

        raise HTTPException(
            status_code=400,
            detail="Customer contact number is required."
        )

    if not customer_email:

        raise HTTPException(
            status_code=400,
            detail="Customer email is required."
        )

    # ========================================================
    # VALIDATE CART
    # ========================================================

    if not data.items:

        raise HTTPException(
            status_code=400,
            detail="Your cart is empty."
        )

    # ========================================================
    # MAXIMUM CART ITEMS
    #
    # Supports 1 to 50 items.
    # Change 50 if you want a different maximum.
    # ========================================================

    if len(data.items) > 50:

        raise HTTPException(
            status_code=400,
            detail="Too many items in the cart."
        )

    # ========================================================
    # ALLOWED CATEGORIES
    # ========================================================

    allowed_categories = {
        "clothes",
        "souvenir",
        "others"
    }

    default_clothing_sizes = [
        "S",
        "M",
        "L",
        "XL",
        "2XL"
    ]

    # ========================================================
    # PREPARE
    # ========================================================

    validated_items = []

    total_php = 0.0

    # ========================================================
    # VALIDATE EVERY CART ITEM
    # ========================================================

    for cart_item in data.items:

        # ----------------------------------------------------
        # QUANTITY
        # ----------------------------------------------------

        if cart_item.quantity <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid quantity for "
                    f"store item #{cart_item.store_item_id}."
                )
            )

        # ----------------------------------------------------
        # FIND ITEM
        # ----------------------------------------------------

        item = (
            db.query(StoreItem)
            .filter(
                StoreItem.id == cart_item.store_item_id,
                StoreItem.is_archived == False
            )
            .first()
        )

        if not item:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Store item "
                    f"#{cart_item.store_item_id} "
                    f"was not found."
                )
            )

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        category = (
            item.category or "others"
        ).strip().lower()

        if category not in allowed_categories:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid category for "
                    f"{item.item_name}."
                )
            )

        # ----------------------------------------------------
        # INVENTORY
        # ----------------------------------------------------

        current_quantity = int(
            item.quantity or 0
        )

        if current_quantity <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"{item.item_name} "
                    f"is currently out of stock."
                )
            )

        if cart_item.quantity > current_quantity:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Only {current_quantity} "
                    f"item(s) of "
                    f"{item.item_name} "
                    f"remaining."
                )
            )

        # ----------------------------------------------------
        # SIZE
        # ----------------------------------------------------

        selected_size = None

        if category == "clothes":

            if not cart_item.size:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Please select a size "
                        f"for {item.item_name}."
                    )
                )

            selected_size = (
                str(cart_item.size)
                .strip()
                .upper()
            )

            available_sizes = []

            if item.sizes:

                try:

                    parsed_sizes = json.loads(
                        item.sizes
                    )

                    if isinstance(
                        parsed_sizes,
                        list
                    ):

                        available_sizes = [
                            str(size)
                            .strip()
                            .upper()
                            for size in parsed_sizes
                            if str(size).strip()
                        ]

                except Exception:

                    raise HTTPException(
                        status_code=500,
                        detail=(
                            f"The size configuration "
                            f"for {item.item_name} "
                            f"is invalid."
                        )
                    )

            if not available_sizes:

                available_sizes = (
                    default_clothing_sizes
                )

            if selected_size not in available_sizes:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Invalid size "
                        f"'{selected_size}' "
                        f"for {item.item_name}. "
                        f"Available sizes: "
                        f"{', '.join(available_sizes)}."
                    )
                )

        # ----------------------------------------------------
        # NON-CLOTHING
        # ----------------------------------------------------

        else:

            selected_size = None

        # ----------------------------------------------------
        # PRICE
        # ----------------------------------------------------

        unit_price = float(
            item.price or 0
        )

        if unit_price <= 0:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid price for "
                    f"{item.item_name}."
                )
            )

        item_total = (
            unit_price *
            int(cart_item.quantity)
        )

        total_php += item_total

        # ----------------------------------------------------
        # STORE VALIDATED ITEM
        # ----------------------------------------------------

        validated_items.append({

            "item": item,

            "store_item_id": item.id,

            "item_name": item.item_name,

            "category": category,

            "quantity": int(
                cart_item.quantity
            ),

            "size": selected_size,

            "unit_price": unit_price,

            "item_total": item_total

        })

    # ========================================================
    # TOTAL
    # ========================================================

    if total_php <= 0:

        raise HTTPException(
            status_code=400,
            detail="Invalid total payment amount."
        )

    # ========================================================
    # PAYMONGO AMOUNT
    # ========================================================

    paymongo_amount = int(
        round(
            total_php * 100
        )
    )

    if paymongo_amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Invalid PayMongo payment amount."
        )

    # ========================================================
    # GENERATE STORE ORDER ID
    #
    # ONE ID FOR THE ENTIRE CART.
    #
    # Example:
    #
    # STORE-20260829153045-ABC12345
    #
    # Whether the cart has:
    #
    # 1 item
    # 2 items
    # 3 items
    # 10 items
    # 50 items
    #
    # they all use ONE store_order_id.
    # ========================================================

    store_order_id = (
        "STORE-"
        + datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        + "-"
        + uuid.uuid4().hex[:8].upper()
    )

    # ========================================================
    # PAYMENT DESCRIPTION
    # ========================================================

    description_parts = []

    for validated in validated_items:

        if validated["size"]:

            description_parts.append(
                f'{validated["item_name"]} '
                f'x{validated["quantity"]} '
                f'({validated["size"]})'
            )

        else:

            description_parts.append(
                f'{validated["item_name"]} '
                f'x{validated["quantity"]}'
            )

    payment_description = (
        "Store Order "
        + store_order_id
        + ": "
        + ", ".join(description_parts)
    )

    # ========================================================
    # CREATE PAYMENT RECORDS
    #
    # ONE PAYMENT ROW PER CART ITEM.
    #
    # Example 10-item cart:
    #
    # Payment 1  -> STORE-ABC
    # Payment 2  -> STORE-ABC
    # Payment 3  -> STORE-ABC
    # ...
    # Payment 10 -> STORE-ABC
    #
    # ALL ROWS BELONG TO THE SAME CART.
    # ========================================================

    payments = []

    try:

        for validated in validated_items:

            payment = Payment(

                participant_id=None,

                payment_type="Store",

                # ------------------------------------------------
                # STORE ORDER
                # ------------------------------------------------

                store_order_id=store_order_id,

                # ------------------------------------------------
                # ITEM
                # ------------------------------------------------

                store_item_id=validated["store_item_id"],

                store_quantity=validated["quantity"],

                store_size=validated["size"],

                tshirt_size=validated["size"],

                # ------------------------------------------------
                # PAYMENT
                # ------------------------------------------------

                amount=int(
                    round(
                        validated["item_total"] * 100
                    )
                ),

                currency="PHP",

                status="Pending",

                description=payment_description,

                # ------------------------------------------------
                # CUSTOMER
                # ------------------------------------------------

                customer_name=customer_name,

                customer_contact=customer_contact,

                customer_email=customer_email
            )

            db.add(payment)

            payments.append(
                payment
            )

        db.commit()

        for payment in payments:

            db.refresh(payment)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create "
                f"store order: {str(e)}"
            )
        )

    # ========================================================
    # PAYMONGO CONFIG
    # ========================================================

    secret_key = PAYMONGO_SECRET_KEY

    if not secret_key:

        for payment in payments:

            db.delete(payment)

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                "PayMongo secret key "
                "is not configured."
            )
        )

    # ========================================================
    # PAYMONGO METADATA
    # ========================================================

    metadata_items = []

    for validated in validated_items:

        metadata_items.append({

            "store_item_id": str(
                validated["store_item_id"]
            ),

            "item_name": validated["item_name"],

            "category": validated["category"],

            "quantity": str(
                validated["quantity"]
            ),

            "size": validated["size"] or ""

        })

    # ========================================================
    # PAYMONGO PAYLOAD
    # ========================================================

    payload = {

        "amount": paymongo_amount,

        "currency": "PHP",

        "description": payment_description,

        "remarks": (
            f"Store Order {store_order_id}"
        ),

        "metadata": {

            "type": "store_purchase",

            "store_order_id": store_order_id,

            "customer_name": customer_name,

            "customer_contact": customer_contact,

            "customer_email": customer_email,

            "item_count": str(
                len(validated_items)
            ),

            "items": json.dumps(
                metadata_items
            )

        }

    }

    # ========================================================
    # CREATE PAYMONGO PAYMENT LINK
    # ========================================================

    try:

        response = httpx.post(

            "https://api.paymongo.com/v1/payment_links",

            auth=(
                secret_key,
                ""
            ),

            headers={

                "Content-Type": "application/json",

                "Idempotency-Key": (
                    f"store-order-{store_order_id}"
                )

            },

            json=payload,

            timeout=30

        )

    except Exception as e:

        for payment in payments:

            db.delete(payment)

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "Unable to connect to "
                f"PayMongo: {str(e)}"
            )
        )

    # ========================================================
    # PAYMONGO ERROR
    # ========================================================

    if response.status_code not in (
        200,
        201
    ):

        try:

            error_data = response.json()

        except Exception:

            error_data = {
                "detail": response.text
            }

        for payment in payments:

            db.delete(payment)

        db.commit()

        raise HTTPException(
            status_code=502,
            detail={
                "message": (
                    "PayMongo rejected "
                    "the payment."
                ),
                "paymongo": error_data
            }
        )

    # ========================================================
    # READ RESPONSE
    # ========================================================

    try:

        result = response.json()

    except Exception as exc:

        for payment in payments:

            db.delete(payment)

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "PayMongo returned "
                "invalid JSON: "
                f"{str(exc)}"
            )
        )

    # ========================================================
    # PAYMENT DATA
    # ========================================================

    payment_data = result.get(
        "data",
        {}
    )

    payment_link_id = payment_data.get(
        "id"
    )

    payment_url = payment_data.get(
        "url"
    )

    reference_number = payment_data.get(
        "reference_number"
    )

    # ========================================================
    # VALIDATE PAYMONGO RESPONSE
    # ========================================================

    if not payment_link_id:

        for payment in payments:

            db.delete(payment)

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "PayMongo did not return "
                "a payment link ID."
            )
        )

    if not payment_url:

        for payment in payments:

            db.delete(payment)

        db.commit()

        raise HTTPException(
            status_code=502,
            detail=(
                "PayMongo did not return "
                "a payment URL."
            )
        )

    # ========================================================
    # SAVE PAYMONGO INFORMATION
    #
    # EVERY PAYMENT ROW GETS THE SAME:
    #
    # - payment link ID
    # - reference
    # - checkout URL
    # - store order ID
    #
    # ========================================================

    for payment in payments:

        payment.paymongo_link_id = (
            payment_link_id
        )

        payment.paymongo_reference = (
            reference_number
        )

        payment.checkout_url = (
            payment_url
        )

        payment.description = (
            payment_description
        )

    db.commit()

    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "success": True,

        "message": (
            "Store order created successfully."
        ),

        "store_order_id": store_order_id,

        "payment_id": payments[0].id,

        "payment_ids": [
            payment.id
            for payment in payments
        ],

        "item_count": len(
            validated_items
        ),

        "items": [

            {

                "payment_id": payment.id,

                "store_item_id":
                    validated["store_item_id"],

                "item_name":
                    validated["item_name"],

                "quantity":
                    validated["quantity"],

                "size":
                    validated["size"],

                "unit_price":
                    validated["unit_price"],

                "item_total":
                    validated["item_total"]

            }

            for payment, validated
            in zip(
                payments,
                validated_items
            )

        ],

        "total_amount": float(
            total_php
        ),

        "checkout_url": payment_url,

        "payment_status": "Pending"

    }
    
















# ============================================================
# STORE PURCHASE STATUS
# ============================================================

@app.get("/store/purchase/status/{payment_id}")
def store_purchase_status(
    payment_id: int,
    db: Session = Depends(get_db)
):

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.payment_type == "Store"
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=404,
            detail="Store payment not found."
        )

    # ========================================================
    # GET WHOLE STORE ORDER
    # ========================================================

    if payment.store_order_id:

        order_payments = (
            db.query(Payment)
            .filter(
                Payment.store_order_id ==
                    payment.store_order_id,

                Payment.payment_type ==
                    "Store"
            )
            .all()
        )

    else:

        order_payments = [
            payment
        ]

    # ========================================================
    # DETERMINE ORDER STATUS
    # ========================================================

    statuses = [
        str(
            p.status or "Pending"
        ).lower()
        for p in order_payments
    ]

    if all(
        status in (
            "paid",
            "success",
            "successful",
            "completed"
        )
        for status in statuses
    ):

        order_status = "Paid"

    elif any(
        status in (
            "failed",
            "cancelled",
            "canceled"
        )
        for status in statuses
    ):

        order_status = "Failed"

    else:

        order_status = "Pending"

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "success":
            True,

        "payment_id":
            payment.id,

        "store_order_id":
            payment.store_order_id,

        "status":
            order_status,

        "payment_status":
            order_status,

        "paymongo_reference":
            payment.paymongo_reference,

        "item_count":
            len(order_payments),

        "items": [

            {

                "payment_id":
                    p.id,

                "store_item_id":
                    p.store_item_id,

                "quantity":
                    p.store_quantity,

                "size":
                    p.store_size,

                "status":
                    p.status

            }

            for p in order_payments

        ]

    }














# ============================================================
# VIEW STORE ITEMS
# ============================================================

@app.get("/store/items")
def view_store_items(
    db: Session = Depends(get_db)
):

    items = (
        db.query(StoreItem)
        .filter(
            StoreItem.is_archived == False
        )
        .order_by(
            StoreItem.id.desc()
        )
        .all()
    )

    return [

        {
            "id":
                item.id,

            "item_name":
                item.item_name,

            "description":
                item.description,

            "quantity":
                item.quantity,

            "price":
                item.price

        }

        for item in items

    ]
    






# =========================================================
# STORE IMAGE UPLOAD
# =========================================================

STORE_UPLOAD_DIR = Path(
    "/app/data/uploads/store"
)

STORE_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif"
}


@app.post("/upload_store_image")
async def upload_store_image(
    file: UploadFile = File(...)
):

    # -----------------------------------------------------
    # Validate file type
    # -----------------------------------------------------

    if file.content_type not in ALLOWED_IMAGE_TYPES:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid image type. "
                "Only JPG, PNG, WEBP, and GIF are allowed."
            )
        )


    # -----------------------------------------------------
    # Generate unique filename
    # -----------------------------------------------------

    extension = ALLOWED_IMAGE_TYPES[
        file.content_type
    ]

    filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )


    file_path = (
        STORE_UPLOAD_DIR /
        filename
    )


    # -----------------------------------------------------
    # Save file
    # -----------------------------------------------------

    try:

        with file_path.open("wb") as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to save image: {str(e)}"
            )
        )

    finally:

        await file.close()


    # -----------------------------------------------------
    # Return URL/path
    # -----------------------------------------------------

    image_url = (
        f"/uploads/store/{filename}"
    )


    return {

        "success": True,

        "message":
            "Store image uploaded successfully.",

        "filename":
            filename,

        "image_url":
            image_url

    }
    

# ============================================================
# VIEW ALL ITEM SPONSORSHIPS
# ============================================================

@app.get(
    "/sponsor_items",
    response_model=List[ItemSponsorshipResponse]
)
def view_all_sponsor_items(
    db: Session = Depends(get_db)
):

    items = (
        db.query(ItemSponsorship)
        .order_by(
            ItemSponsorship.created_at.desc()
        )
        .all()
    )

    return items


# ============================================================
# VIEW SINGLE ITEM SPONSORSHIP
# ============================================================

@app.get(
    "/sponsor_items/{sponsor_id}",
    response_model=ItemSponsorshipResponse
)
def view_single_sponsor_item(
    sponsor_id: int,
    db: Session = Depends(get_db)
):

    item = (
        db.query(ItemSponsorship)
        .filter(
            ItemSponsorship.id == sponsor_id
        )
        .first()
    )

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Item sponsorship not found."
        )

    return item


# ============================================================
# VIEW ALL CASH SPONSORSHIPS
# ============================================================

@app.get(
    "/sponsor_cash",
    response_model=List[CashSponsorshipResponse]
)
def view_all_sponsor_cash(
    db: Session = Depends(get_db)
):

    sponsorships = (
        db.query(CashSponsorship)
        .order_by(
            CashSponsorship.created_at.desc()
        )
        .all()
    )

    return sponsorships


# ============================================================
# VIEW SINGLE CASH SPONSORSHIP
# ============================================================

@app.get(
    "/sponsor_cash/{sponsor_id}",
    response_model=CashSponsorshipResponse
)
def view_single_sponsor_cash(
    sponsor_id: int,
    db: Session = Depends(get_db)
):

    sponsorship = (
        db.query(CashSponsorship)
        .filter(
            CashSponsorship.id == sponsor_id
        )
        .first()
    )

    if not sponsorship:

        raise HTTPException(
            status_code=404,
            detail="Cash sponsorship not found."
        )

    return sponsorship


# ============================================================
# VIEW ALL STORE PAYMENTS
# ============================================================
#
# Unique name:
# Store Payments
#
# Returns payments specifically connected to StoreItem.
# ============================================================

@app.get(
    "/payments/store",
    response_model=List[PaymentResponse]
)
def view_all_store_payments(
    db: Session = Depends(get_db)
):

    payments = (
        db.query(Payment)
        .filter(
            Payment.store_item_id.isnot(None)
        )
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    return payments


# ============================================================
# VIEW SINGLE STORE PAYMENT
# ============================================================

@app.get(
    "/payments/store/{payment_id}",
    response_model=PaymentResponse
)
def view_single_store_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.store_item_id.isnot(None)
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=404,
            detail="Store payment not found."
        )

    return payment


# ============================================================
# VIEW ALL T-SHIRT PAYMENTS
# ============================================================

@app.get(
    "/payments/tshirt",
    response_model=List[PaymentResponse]
)
def view_all_tshirt_payments(
    db: Session = Depends(get_db)
):

    payments = (
        db.query(Payment)
        .filter(
            Payment.tshirt_selected > 0
        )
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    result = []

    for payment in payments:

        participant = None

        if payment.participant_id:

            participant = (
                db.query(Participant)
                .filter(
                    Participant.id ==
                    payment.participant_id
                )
                .first()
            )

        data = {
            "id": payment.id,
            "participant_id": payment.participant_id,
            "payment_type": payment.payment_type,

            "store_item_id": payment.store_item_id,
            "store_quantity": payment.store_quantity,
            "store_size": payment.store_size,

            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,

            "tshirt_selected":
                payment.tshirt_selected,

            "lanyard_selected":
                payment.lanyard_selected,

            "tshirt_size":
                payment.tshirt_size,

            "sponsorship_tier":
                payment.sponsorship_tier,

            "sponsor_id":
                payment.sponsor_id,

            "paymongo_link_id":
                payment.paymongo_link_id,

            "paymongo_payment_id":
                payment.paymongo_payment_id,

            "paymongo_reference":
                payment.paymongo_reference,

            "checkout_url":
                payment.checkout_url,

            "description":
                payment.description,

            "customer_name":
                payment.customer_name,

            "customer_contact":
                payment.customer_contact,

            "customer_email":
                payment.customer_email,

            "created_at":
                payment.created_at,

            "paid_at":
                payment.paid_at,

            # ==========================================
            # FULL PARTICIPANT NAME
            # ==========================================

            "participant_name":
                (
                    f"{participant.fname} "
                    f"{participant.mname + ' ' if participant.mname else ''}"
                    f"{participant.lname}"
                )
                if participant
                else payment.customer_name
        }

        result.append(data)

    return result


# ============================================================
# VIEW SINGLE T-SHIRT PAYMENT
# ============================================================

@app.get(
    "/payments/tshirt/{payment_id}",
    response_model=PaymentResponse
)
def view_single_tshirt_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.tshirt_selected > 0
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=404,
            detail="T-Shirt payment not found."
        )

    return payment


# ============================================================
# VIEW ALL LANYARD PAYMENTS
# ============================================================

@app.get(
    "/payments/lanyard",
    response_model=List[PaymentResponse]
)
def view_all_lanyard_payments(
    db: Session = Depends(get_db)
):

    payments = (
        db.query(Payment)
        .filter(
            Payment.lanyard_selected > 0
        )
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    result = []

    for payment in payments:

        participant = None

        if payment.participant_id:

            participant = (
                db.query(Participant)
                .filter(
                    Participant.id ==
                    payment.participant_id
                )
                .first()
            )

        data = {
            "id": payment.id,
            "participant_id": payment.participant_id,
            "payment_type": payment.payment_type,

            "store_item_id": payment.store_item_id,
            "store_quantity": payment.store_quantity,
            "store_size": payment.store_size,

            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,

            "tshirt_selected":
                payment.tshirt_selected,

            "lanyard_selected":
                payment.lanyard_selected,

            "tshirt_size":
                payment.tshirt_size,

            "sponsorship_tier":
                payment.sponsorship_tier,

            "sponsor_id":
                payment.sponsor_id,

            "paymongo_link_id":
                payment.paymongo_link_id,

            "paymongo_payment_id":
                payment.paymongo_payment_id,

            "paymongo_reference":
                payment.paymongo_reference,

            "checkout_url":
                payment.checkout_url,

            "description":
                payment.description,

            "customer_name":
                payment.customer_name,

            "customer_contact":
                payment.customer_contact,

            "customer_email":
                payment.customer_email,

            "created_at":
                payment.created_at,

            "paid_at":
                payment.paid_at,

            "participant_name":
                (
                    f"{participant.fname} "
                    f"{participant.mname + ' ' if participant.mname else ''}"
                    f"{participant.lname}"
                )
                if participant
                else payment.customer_name
        }

        result.append(data)

    return result


# ============================================================
# VIEW SINGLE LANYARD PAYMENT
# ============================================================

@app.get(
    "/payments/lanyard/{payment_id}",
    response_model=PaymentResponse
)
def view_single_lanyard_payment(
    payment_id: int,
    db: Session = Depends(get_db)
):

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.lanyard_selected > 0
        )
        .first()
    )

    if not payment:

        raise HTTPException(
            status_code=404,
            detail="Lanyard payment not found."
        )

    return payment






# ============================================================
# CREATE REGISTRATION ITEM
# ============================================================

@app.post(
    "/registration/items",
    response_model=RegistrationItemResponse
)
def create_registration_item(
    data: RegistrationItemCreate,
    db: Session = Depends(get_db)
):

    item_name = data.item_name.strip()

    if not item_name:
        raise HTTPException(
            status_code=400,
            detail="Item name is required."
        )

    if data.price < 0:
        raise HTTPException(
            status_code=400,
            detail="Price cannot be negative."
        )

    # --------------------------------------------------------
    # CHECK DUPLICATE ITEM NAME
    # --------------------------------------------------------

    existing_item = (
        db.query(RegistrationItem)
        .filter(
            func.lower(
                RegistrationItem.item_name
            ) == item_name.lower()
        )
        .first()
    )

    if existing_item:

        raise HTTPException(
            status_code=400,
            detail="Registration item already exists."
        )

    # --------------------------------------------------------
    # CREATE
    # --------------------------------------------------------

    item = RegistrationItem(

        item_name=item_name,

        price=data.price,

        is_active=True

    )

    db.add(item)

    db.commit()

    db.refresh(item)

    return item


# ============================================================
# VIEW ALL REGISTRATION ITEMS
# ============================================================

@app.get(
    "/registration/items",
    response_model=List[RegistrationItemResponse]
)
def view_all_registration_items(
    db: Session = Depends(get_db)
):

    items = (
        db.query(RegistrationItem)
        .order_by(
            RegistrationItem.item_name.asc()
        )
        .all()
    )

    return items

# ============================================================
# VIEW ACTIVE REGISTRATION ITEMS
# ============================================================

@app.get(
    "/registration/items/active",
    response_model=List[RegistrationItemResponse]
)
def view_active_registration_items(
    db: Session = Depends(get_db)
):

    items = (
        db.query(RegistrationItem)
        .filter(
            RegistrationItem.is_active == True
        )
        .order_by(
            RegistrationItem.item_name.asc()
        )
        .all()
    )

    return items

# ============================================================
# VIEW SINGLE REGISTRATION ITEM
# ============================================================

@app.get(
    "/registration/items/{item_id}",
    response_model=RegistrationItemResponse
)
def view_single_registration_item(
    item_id: int,
    db: Session = Depends(get_db)
):

    item = (
        db.query(RegistrationItem)
        .filter(
            RegistrationItem.id == item_id
        )
        .first()
    )

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Registration item not found."
        )

    return item

# ============================================================
# UPDATE REGISTRATION ITEM
# ============================================================

@app.put(
    "/registration/items/{item_id}",
    response_model=RegistrationItemResponse
)
def update_registration_item(
    item_id: int,
    data: RegistrationItemUpdate,
    db: Session = Depends(get_db)
):

    item = (
        db.query(RegistrationItem)
        .filter(
            RegistrationItem.id == item_id
        )
        .first()
    )

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Registration item not found."
        )

    # --------------------------------------------------------
    # UPDATE NAME
    # --------------------------------------------------------

    if data.item_name is not None:

        item_name = data.item_name.strip()

        if not item_name:

            raise HTTPException(
                status_code=400,
                detail="Item name cannot be empty."
            )

        duplicate = (
            db.query(RegistrationItem)
            .filter(
                RegistrationItem.id != item_id,
                func.lower(
                    RegistrationItem.item_name
                ) == item_name.lower()
            )
            .first()
        )

        if duplicate:

            raise HTTPException(
                status_code=400,
                detail="Another registration item already uses this name."
            )

        item.item_name = item_name

    # --------------------------------------------------------
    # UPDATE PRICE
    # --------------------------------------------------------

    if data.price is not None:

        if data.price < 0:

            raise HTTPException(
                status_code=400,
                detail="Price cannot be negative."
            )

        item.price = data.price

    # --------------------------------------------------------
    # UPDATE ACTIVE STATUS
    # --------------------------------------------------------

    if data.is_active is not None:

        item.is_active = data.is_active

    db.commit()

    db.refresh(item)

    return item

# ============================================================
# DEACTIVATE REGISTRATION ITEM
# ============================================================

@app.delete(
    "/registration/items/{item_id}"
)
def deactivate_registration_item(
    item_id: int,
    db: Session = Depends(get_db)
):

    item = (
        db.query(RegistrationItem)
        .filter(
            RegistrationItem.id == item_id
        )
        .first()
    )

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Registration item not found."
        )

    item.is_active = False

    db.commit()

    return {

        "success": True,

        "message":
            "Registration item deactivated.",

        "item_id":
            item.id

    }
    
    
# ============================================================
# ACTIVATE REGISTRATION ITEM
# ============================================================

@app.put(
    "/registration/items/{item_id}/activate"
)
def activate_registration_item(
    item_id: int,
    db: Session = Depends(get_db)
):

    item = (
        db.query(RegistrationItem)
        .filter(
            RegistrationItem.id == item_id
        )
        .first()
    )

    if not item:

        raise HTTPException(
            status_code=404,
            detail="Registration item not found."
        )

    item.is_active = True

    db.commit()

    return {

        "success": True,

        "message":
            "Registration item activated.",

        "item_id":
            item.id

    }
    

# ============================================================
# GET ACTIVE REGISTRATION ITEMS
# ============================================================

@app.get("/registration_items")
def get_registration_items(
    db: Session = Depends(get_db)
):

    items = (
        db.query(RegistrationItem)
        .filter(
            RegistrationItem.is_active == True
        )
        .order_by(
            RegistrationItem.id.asc()
        )
        .all()
    )

    result = []

    for item in items:

        result.append({

            "id":
                item.id,

            "item_name":
                item.item_name,

            # Database value is stored in centavos
            "price":
                item.price,

            "price_display":
                f"₱{item.price / 100:,.2f}",

            "is_active":
                item.is_active
        })

    return result




# ============================================================
# MANUAL FIND SPONSOR / PROCESS SPONSOR QUEUE
# ============================================================
#
# POST /process_finding_sponsor_queue
#
# CashDonationTotal.total_amount:
#     STORED IN PESOS
#
# RegistrationItem.price:
#     STORED IN CENTAVOS
#
# Example:
#
# T-shirt:
#     35000 centavos = ₱350.00
#
# Lanyard:
#     9000 centavos = ₱90.00
#
# Required per participant:
#     ₱350 + ₱90 = ₱440
#
# If sponsorship fund = ₱1,250:
#
# Participant 1 = ₱440
# Participant 2 = ₱440
# Remaining     = ₱370
#
# After sponsorship:
#
# - T-shirt = Paid
# - Lanyard = Paid
# - Registration = Confirmed
# - Sponsor review = Approved (if field exists)
# - Participant receives confirmation email
#
# IMPORTANT:
#
# This endpoint does NOT add money to the sponsorship fund.
# It only uses the existing CashDonationTotal balance.
#
# ============================================================










@app.post("/process_finding_sponsor_queue")
async def process_finding_sponsor_queue(
    db: Session = Depends(get_db)
):

    print("\n")
    print("=" * 70)
    print("MANUAL FIND SPONSOR PROCESSING")
    print("=" * 70)

    # ========================================================
    # GET T-SHIRT PRICE
    # ========================================================

    tshirt_item = (
        db.query(
            RegistrationItem
        )
        .filter(
            RegistrationItem.item_name.ilike("T-Shirt"),
            RegistrationItem.is_active == True
        )
        .first()
    )

    if not tshirt_item:

        raise HTTPException(
            status_code=404,
            detail="T-shirt registration item was not found."
        )

    # ========================================================
    # GET LANYARD PRICE
    # ========================================================

    lanyard_item = (
        db.query(
            RegistrationItem
        )
        .filter(
            RegistrationItem.item_name.ilike("Lanyard"),
            RegistrationItem.is_active == True
        )
        .first()
    )

    if not lanyard_item:

        raise HTTPException(
            status_code=404,
            detail="Lanyard registration item was not found."
        )

    # ========================================================
    # GET PRICES
    #
    # RegistrationItem.price = CENTAVOS
    #
    # 35000 = ₱350.00
    # 9000  = ₱90.00
    # ========================================================

    try:

        tshirt_price_centavos = int(
            tshirt_item.price or 0
        )

    except (
        ValueError,
        TypeError
    ):

        tshirt_price_centavos = 0

    try:

        lanyard_price_centavos = int(
            lanyard_item.price or 0
        )

    except (
        ValueError,
        TypeError
    ):

        lanyard_price_centavos = 0

    # ========================================================
    # CONVERT CENTAVOS TO PESOS
    # ========================================================

    tshirt_price = (
        tshirt_price_centavos / 100
    )

    lanyard_price = (
        lanyard_price_centavos / 100
    )

    # ========================================================
    # REQUIRED AMOUNT PER PARTICIPANT
    # ========================================================

    required_amount = (
        tshirt_price +
        lanyard_price
    )

    if required_amount <= 0:

        raise HTTPException(
            status_code=400,
            detail=(
                "T-shirt and lanyard prices must be "
                "greater than zero."
            )
        )

    print(
        "T-shirt Price:",
        f"₱{tshirt_price:,.2f}"
    )

    print(
        "Lanyard Price:",
        f"₱{lanyard_price:,.2f}"
    )

    print(
        "Required Per Participant:",
        f"₱{required_amount:,.2f}"
    )

    # ========================================================
    # GET CURRENT CASH DONATION TOTAL
    #
    # CashDonationTotal.total_amount = PESOS
    # ========================================================

    donation_total = (
        db.query(
            CashDonationTotal
        )
        .order_by(
            CashDonationTotal.id.asc()
        )
        .first()
    )

    if not donation_total:

        return {

            "success": True,

            "message":
                "No CashDonationTotal record exists.",

            "status":
                "Queued",

            "cash_donation_total":
                0,

            "cash_donation_total_display":
                "₱0.00",

            "tshirt_price":
                tshirt_price,

            "tshirt_price_display":
                f"₱{tshirt_price:,.2f}",

            "lanyard_price":
                lanyard_price,

            "lanyard_price_display":
                f"₱{lanyard_price:,.2f}",

            "required_amount_per_participant":
                required_amount,

            "required_amount_display":
                f"₱{required_amount:,.2f}",

            "sponsored_count":
                0,

            "remaining_queue_count":
                0,

            "participants":
                []

        }

    # ========================================================
    # CURRENT BALANCE
    # ========================================================

    try:

        current_balance = float(
            donation_total.total_amount or 0
        )

    except (
        ValueError,
        TypeError
    ):

        current_balance = 0.0

    initial_balance = current_balance

    print(
        "Current Sponsorship Fund:",
        f"₱{current_balance:,.2f}"
    )

    # ========================================================
    # FIND FINDING SPONSOR PARTICIPANTS
    #
    # FIFO:
    # Oldest participant is processed first.
    #
    # IMPORTANT:
    #
    # func and or_ must come from SQLAlchemy:
    #
    # from sqlalchemy import func, or_
    #
    # Do NOT use:
    #
    # db.func
    # db.or_
    # ========================================================

    finding_sponsors = (
        db.query(
            Participant
        )
        .filter(

            Participant.is_archived == 0,

            Participant.participant_type.ilike(
                "Finding Sponsor"
            ),

            or_(

                func.lower(
                    func.coalesce(
                        Participant.tshirt_status,
                        "Unpaid"
                    )
                ) != "paid",

                func.lower(
                    func.coalesce(
                        Participant.lanyard_status,
                        "Unpaid"
                    )
                ) != "paid"

            )

        )
        .order_by(

            Participant.created_at.asc(),

            Participant.id.asc()

        )
        .all()
    )

    # ========================================================
    # QUEUE COUNT
    # ========================================================

    initial_queue_count = len(
        finding_sponsors
    )

    print(
        "Finding Sponsor Queue:",
        initial_queue_count
    )

    # ========================================================
    # NO PARTICIPANTS
    # ========================================================

    if initial_queue_count == 0:

        print(
            "No Finding Sponsor participants waiting."
        )

        return {

            "success": True,

            "message":
                "No Finding Sponsor participants are waiting for sponsorship.",

            "status":
                "Completed",

            "cash_donation_total":
                current_balance,

            "cash_donation_total_display":
                f"₱{current_balance:,.2f}",

            "tshirt_price":
                tshirt_price,

            "tshirt_price_display":
                f"₱{tshirt_price:,.2f}",

            "tshirt_price_centavos":
                tshirt_price_centavos,

            "lanyard_price":
                lanyard_price,

            "lanyard_price_display":
                f"₱{lanyard_price:,.2f}",

            "lanyard_price_centavos":
                lanyard_price_centavos,

            "required_amount_per_participant":
                required_amount,

            "required_amount_display":
                f"₱{required_amount:,.2f}",

            "initial_queue_count":
                0,

            "sponsored_count":
                0,

            "remaining_queue_count":
                0,

            "participant_emails_sent":
                0,

            "participant_email_errors":
                [],

            "participants":
                []

        }

    # ========================================================
    # NOT ENOUGH FOR EVEN ONE PARTICIPANT
    # ========================================================

    if current_balance < required_amount:

        amount_needed = (
            required_amount -
            current_balance
        )

        print(
            "Insufficient sponsorship fund."
        )

        print(
            "Current:",
            f"₱{current_balance:,.2f}"
        )

        print(
            "Needed:",
            f"₱{required_amount:,.2f}"
        )

        print(
            "Still Needed:",
            f"₱{amount_needed:,.2f}"
        )

        return {

            "success": True,

            "message":
                "Cash donation balance is insufficient to sponsor the next participant.",

            "status":
                "Queued",

            "cash_donation_total":
                current_balance,

            "cash_donation_total_display":
                f"₱{current_balance:,.2f}",

            "tshirt_price":
                tshirt_price,

            "tshirt_price_display":
                f"₱{tshirt_price:,.2f}",

            "tshirt_price_centavos":
                tshirt_price_centavos,

            "lanyard_price":
                lanyard_price,

            "lanyard_price_display":
                f"₱{lanyard_price:,.2f}",

            "lanyard_price_centavos":
                lanyard_price_centavos,

            "required_amount_per_participant":
                required_amount,

            "required_amount_display":
                f"₱{required_amount:,.2f}",

            "amount_still_needed":
                amount_needed,

            "amount_still_needed_display":
                f"₱{amount_needed:,.2f}",

            "initial_queue_count":
                initial_queue_count,

            "sponsored_count":
                0,

            "remaining_queue_count":
                initial_queue_count,

            "participant_emails_sent":
                0,

            "participant_email_errors":
                [],

            "participants":
                []

        }

    # ========================================================
    # PROCESS PARTICIPANTS
    # ========================================================

    sponsored_participants = []

    try:

        for participant in finding_sponsors:

            # =================================================
            # STOP WHEN BALANCE IS NOT ENOUGH
            # =================================================

            if current_balance < required_amount:

                break

            # =================================================
            # FULL NAME
            # =================================================

            fullname = " ".join(

                part

                for part in [

                    getattr(
                        participant,
                        "fname",
                        None
                    ),

                    getattr(
                        participant,
                        "mname",
                        None
                    ),

                    getattr(
                        participant,
                        "lname",
                        None
                    )

                ]

                if part

            ).strip()

            # =================================================
            # DEDUCT SPONSORSHIP COST
            # =================================================

            current_balance -= (
                required_amount
            )

            # Prevent floating-point negative values
            if abs(current_balance) < 0.000001:

                current_balance = 0.0

            # =================================================
            # MARK T-SHIRT PAID
            # =================================================

            if hasattr(
                participant,
                "tshirt_status"
            ):

                participant.tshirt_status = (
                    "Paid"
                )

            # =================================================
            # MARK LANYARD PAID
            # =================================================

            if hasattr(
                participant,
                "lanyard_status"
            ):

                participant.lanyard_status = (
                    "Paid"
                )

            # =================================================
            # COMPLETE REGISTRATION
            # =================================================

            if hasattr(
                participant,
                "registration_status"
            ):

                participant.registration_status = (
                    "Confirmed"
                )

            # =================================================
            # SPONSOR REVIEW APPROVED
            #
            # Supports either possible field name.
            # =================================================

            sponsor_review_field = None

            if hasattr(
                participant,
                "sponsor_review_status"
            ):

                participant.sponsor_review_status = (
                    "Approved"
                )

                sponsor_review_field = (
                    "sponsor_review_status"
                )

            elif hasattr(
                participant,
                "sponsorship_review_status"
            ):

                participant.sponsorship_review_status = (
                    "Approved"
                )

                sponsor_review_field = (
                    "sponsorship_review_status"
                )

            # =================================================
            # UPDATE TIMESTAMP
            # =================================================

            if hasattr(
                participant,
                "updated_at"
            ):

                participant.updated_at = (
                    datetime.datetime.now()
                )

            # =================================================
            # RECORD PARTICIPANT
            # =================================================

            sponsor_review_status = (
                getattr(
                    participant,
                    "sponsor_review_status",
                    None
                )
            )

            if sponsor_review_status is None:

                sponsor_review_status = (
                    getattr(
                        participant,
                        "sponsorship_review_status",
                        "Approved"
                    )
                )

            sponsored_participants.append({

                "participant_id":
                    participant.id,

                "registration_number":
                    getattr(
                        participant,
                        "registration_number",
                        None
                    ),

                "fullname":
                    fullname,

                "email":
                    getattr(
                        participant,
                        "email",
                        None
                    ),

                "participant_type":
                    getattr(
                        participant,
                        "participant_type",
                        None
                    ),

                "tshirt_status":
                    getattr(
                        participant,
                        "tshirt_status",
                        "Paid"
                    ),

                "lanyard_status":
                    getattr(
                        participant,
                        "lanyard_status",
                        "Paid"
                    ),

                "registration_status":
                    getattr(
                        participant,
                        "registration_status",
                        None
                    ),

                "sponsor_review_status":
                    sponsor_review_status,

                "sponsor_review_field":
                    sponsor_review_field,

                "sponsored_amount":
                    required_amount,

                "sponsored_amount_display":
                    f"₱{required_amount:,.2f}"

            })

            # =================================================
            # LOG
            # =================================================

            print("=" * 50)

            print(
                "PARTICIPANT SPONSORED"
            )

            print(
                "Participant ID:",
                participant.id
            )

            print(
                "Registration:",
                getattr(
                    participant,
                    "registration_number",
                    None
                )
            )

            print(
                "Name:",
                fullname
            )

            print(
                "Sponsored:",
                f"₱{required_amount:,.2f}"
            )

            print(
                "T-shirt:",
                getattr(
                    participant,
                    "tshirt_status",
                    None
                )
            )

            print(
                "Lanyard:",
                getattr(
                    participant,
                    "lanyard_status",
                    None
                )
            )

            print(
                "Registration:",
                getattr(
                    participant,
                    "registration_status",
                    None
                )
            )

            print(
                "Sponsor Review:",
                sponsor_review_status
            )

            print(
                "Remaining Fund:",
                f"₱{current_balance:,.2f}"
            )

            print("=" * 50)

        # ====================================================
        # SAVE REMAINING BALANCE
        # ====================================================

        donation_total.total_amount = (
            current_balance
        )

        if hasattr(
            donation_total,
            "updated_at"
        ):

            donation_total.updated_at = (
                datetime.datetime.now()
            )

        # ====================================================
        # COMMIT DATABASE CHANGES
        # ====================================================

        db.commit()

        db.refresh(
            donation_total
        )

    except Exception as e:

        db.rollback()

        print(
            "=" * 70
        )

        print(
            "MANUAL FIND SPONSOR ERROR:"
        )

        print(
            repr(e)
        )

        print(
            "=" * 70
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to process Finding Sponsor "
                "participants."
            )
        )

    # ========================================================
    # GET REMAINING QUEUE
    # ========================================================

    remaining_queue = (
        db.query(
            Participant
        )
        .filter(

            Participant.is_archived == 0,

            Participant.participant_type.ilike(
                "Finding Sponsor"
            ),

            or_(

                func.lower(
                    func.coalesce(
                        Participant.tshirt_status,
                        "Unpaid"
                    )
                ) != "paid",

                func.lower(
                    func.coalesce(
                        Participant.lanyard_status,
                        "Unpaid"
                    )
                ) != "paid"

            )

        )
        .order_by(

            Participant.created_at.asc(),

            Participant.id.asc()

        )
        .all()
    )

    # ========================================================
    # DETERMINE QUEUE STATUS
    # ========================================================

    if len(remaining_queue) == 0:

        queue_status = "Completed"

    elif current_balance >= required_amount:

        queue_status = "Ready"

    else:

        queue_status = "Queued"

    # ========================================================
    # SEND SPONSORED PARTICIPANT EMAILS
    # ========================================================
    #
    # The email function must exist somewhere above/before
    # this endpoint:
    #
    # async def send_sponsored_participant_confirmation_email(
    #     participant
    # ):
    #
    # This endpoint uses:
    #
    # await email_function(participant)
    #
    # ========================================================

    participant_emails_sent = 0

    participant_email_errors = []

    email_function = globals().get(
        "send_sponsored_participant_confirmation_email"
    )

    if not email_function:

        print(
            "WARNING: "
            "send_sponsored_participant_confirmation_email "
            "is not defined."
        )

        print(
            "Participants were sponsored successfully, "
            "but confirmation emails were not sent."
        )

    else:

        for sponsored in sponsored_participants:

            try:

                sponsored_participant = (
                    db.query(
                        Participant
                    )
                    .filter(
                        Participant.id ==
                        sponsored["participant_id"]
                    )
                    .first()
                )

                if not sponsored_participant:

                    print(
                        "Sponsored participant not found:",
                        sponsored["participant_id"]
                    )

                    participant_email_errors.append({

                        "participant_id":
                            sponsored["participant_id"],

                        "error":
                            "Participant not found after sponsorship."

                    })

                    continue

                participant_email = getattr(
                    sponsored_participant,
                    "email",
                    None
                )

                if participant_email:

                    participant_email = str(
                        participant_email
                    ).strip()

                if not participant_email:

                    print(
                        "Sponsored participant has no email:",
                        sponsored["participant_id"]
                    )

                    participant_email_errors.append({

                        "participant_id":
                            sponsored["participant_id"],

                        "error":
                            "Participant has no email address."

                    })

                    continue

                # ==========================================
                # SEND EMAIL
                # ==========================================

                print(
                    "Sending sponsored participant email to:",
                    participant_email
                )

                await email_function(
                sponsored_participant,
                sponsored["sponsored_amount"]
                )

                participant_emails_sent += 1

                print(
                    "Sponsored participant email sent:",
                    participant_email
                )

            except Exception as e:

                print(
                    "Sponsored participant email failed:"
                )

                print(
                    "Participant ID:",
                    sponsored["participant_id"]
                )

                print(
                    "Error:",
                    repr(e)
                )

                participant_email_errors.append({

                    "participant_id":
                        sponsored["participant_id"],

                    "error":
                        str(e)

                })

    # ========================================================
    # TOTAL SPONSORED AMOUNT
    # ========================================================

    total_sponsored_amount = (
        len(sponsored_participants) *
        required_amount
    )

    # ========================================================
    # FINAL LOG
    # ========================================================

    print("=" * 70)

    print(
        "FINDING SPONSOR PROCESSING COMPLETE"
    )

    print("=" * 70)

    print(
        "Initial Fund:",
        f"₱{initial_balance:,.2f}"
    )

    print(
        "Total Sponsored:",
        f"₱{total_sponsored_amount:,.2f}"
    )

    print(
        "Remaining Fund:",
        f"₱{current_balance:,.2f}"
    )

    print(
        "Sponsored Participants:",
        len(
            sponsored_participants
        )
    )

    print(
        "Remaining Queue:",
        len(
            remaining_queue
        )
    )

    print(
        "Emails Sent:",
        participant_emails_sent
    )

    print(
        "Email Errors:",
        len(
            participant_email_errors
        )
    )

    print("=" * 70)

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "success": True,

        "message":
            "Finding Sponsor queue processed successfully.",

        "status":
            queue_status,

        # ====================================================
        # FUND
        # ====================================================

        "initial_cash_donation_total":
            initial_balance,

        "initial_cash_donation_total_display":
            f"₱{initial_balance:,.2f}",

        "total_sponsored_amount":
            total_sponsored_amount,

        "total_sponsored_amount_display":
            f"₱{total_sponsored_amount:,.2f}",

        "cash_donation_total":
            current_balance,

        "cash_donation_total_display":
            f"₱{current_balance:,.2f}",

        # ====================================================
        # PRICES
        # ====================================================

        "tshirt_price":
            tshirt_price,

        "tshirt_price_display":
            f"₱{tshirt_price:,.2f}",

        "tshirt_price_centavos":
            tshirt_price_centavos,

        "lanyard_price":
            lanyard_price,

        "lanyard_price_display":
            f"₱{lanyard_price:,.2f}",

        "lanyard_price_centavos":
            lanyard_price_centavos,

        "required_amount_per_participant":
            required_amount,

        "required_amount_display":
            f"₱{required_amount:,.2f}",

        # ====================================================
        # QUEUE
        # ====================================================

        "initial_queue_count":
            initial_queue_count,

        "sponsored_count":
            len(
                sponsored_participants
            ),

        "remaining_queue_count":
            len(
                remaining_queue
            ),

        # ====================================================
        # EMAIL
        # ====================================================

        "participant_emails_sent":
            participant_emails_sent,

        "participant_email_errors":
            participant_email_errors,

        # ====================================================
        # PARTICIPANTS
        # ====================================================

        "participants":
            sponsored_participants

    }











    





# ============================================================
# SPONSOR DASHBOARD STATISTICS
# ============================================================

@app.get("/sponsor_dashboard_stats")
def sponsor_dashboard_stats(
    db: Session = Depends(get_db)
):
    # ========================================================
    # GET CURRENT CASH DONATION FUND
    #
    # CashDonationTotal.total_amount is already stored in PESOS.
    #
    # Example:
    # 1500 = ₱1,500.00
    #
    # DO NOT divide this value by 100.
    # ========================================================

    donation_total = (
        db.query(
            CashDonationTotal
        )
        .order_by(
            CashDonationTotal.id.asc()
        )
        .first()
    )

    if donation_total:
        try:
            cash_donation_total = float(
                donation_total.total_amount or 0
            )
        except (
            ValueError,
            TypeError
        ):
            cash_donation_total = 0.0
    else:
        cash_donation_total = 0.0


    # ========================================================
    # GET TOTAL SPONSORED PARTICIPANTS
    #
    # A participant is considered sponsored when:
    # - participant_type = Finding Sponsor
    # - T-shirt is Paid
    # - Lanyard is Paid
    #
    # ========================================================

    total_sponsored_participants = (
        db.query(
            Participant
        )
        .filter(
            Participant.is_archived == 0,

            Participant.participant_type.ilike(
                "Finding Sponsor"
            ),

            func.lower(
                func.coalesce(
                    Participant.tshirt_status,
                    "Unpaid"
                )
            ) == "paid",

            func.lower(
                func.coalesce(
                    Participant.lanyard_status,
                    "Unpaid"
                )
            ) == "paid"
        )
        .count()
    )


    # ========================================================
    # GET CURRENT T-SHIRT PRICE
    # ========================================================

    tshirt_item = (
        db.query(
            RegistrationItem
        )
        .filter(
            RegistrationItem.item_name.ilike(
                "T-Shirt"
            ),
            RegistrationItem.is_active == True
        )
        .first()
    )

    tshirt_price = 0.0

    if tshirt_item:
        try:
            tshirt_price = (
                int(
                    tshirt_item.price or 0
                ) / 100
            )
        except (
            ValueError,
            TypeError
        ):
            tshirt_price = 0.0


    # ========================================================
    # GET CURRENT LANYARD PRICE
    # ========================================================

    lanyard_item = (
        db.query(
            RegistrationItem
        )
        .filter(
            RegistrationItem.item_name.ilike(
                "Lanyard"
            ),
            RegistrationItem.is_active == True
        )
        .first()
    )

    lanyard_price = 0.0

    if lanyard_item:
        try:
            lanyard_price = (
                int(
                    lanyard_item.price or 0
                ) / 100
            )
        except (
            ValueError,
            TypeError
        ):
            lanyard_price = 0.0


    # ========================================================
    # SPONSORSHIP COST PER PARTICIPANT
    # ========================================================

    sponsorship_amount_per_participant = (
        tshirt_price +
        lanyard_price
    )


    # ========================================================
    # TOTAL USED DONATION FUND
    #
    # Example:
    #
    # 10 sponsored participants
    # ₱440 sponsorship cost each
    #
    # Used = ₱4,400
    # ========================================================

    total_used_donation_fund = (
        total_sponsored_participants *
        sponsorship_amount_per_participant
    )


    # ========================================================
    # TOTAL DONATION FUND EVER RECEIVED
    #
    # Current balance + amount already used
    #
    # ========================================================

    total_donation_fund_received = (
        cash_donation_total +
        total_used_donation_fund
    )


    # ========================================================
    # RETURN DASHBOARD STATISTICS
    #
    # Amounts are returned in PESOS.
    #
    # No extra /100 conversion is applied to the donation
    # balance because CashDonationTotal.total_amount is already
    # stored in pesos.
    # ========================================================

    return {
        "success": True,

        "cash_donation_total":
            round(
                cash_donation_total,
                2
            ),

        "cash_donation_total_display":
            f"₱{cash_donation_total:,.2f}",

        "total_sponsored_participants":
            total_sponsored_participants,

        "sponsorship_amount_per_participant":
            round(
                sponsorship_amount_per_participant,
                2
            ),

        "sponsorship_amount_per_participant_display":
            f"₱{sponsorship_amount_per_participant:,.2f}",

        "total_used_donation_fund":
            round(
                total_used_donation_fund,
                2
            ),

        "total_used_donation_fund_display":
            f"₱{total_used_donation_fund:,.2f}",

        "total_donation_fund_received":
            round(
                total_donation_fund_received,
                2
            ),

        "total_donation_fund_received_display":
            f"₱{total_donation_fund_received:,.2f}"
    }    
    
    
    
    
    





# ============================================================
# REPORT DASHBOARD DATA
# Add this endpoint to main(6).py
#
# Uses the existing models:
# Participant
# ParticipantEvaluation
# Staff
# Chaperone
# User
# StoreItem
# Payment
# CashSponsorship
# ItemSponsorship
# SponsorshipItem
# CashDonationTotal
# Event
# ============================================================

@app.get("/report_dashboard_data")
def report_dashboard_data(
    db: Session = Depends(get_db)
):

    today = datetime.date.today()

    # ========================================================
    # PARTICIPANTS
    # ========================================================

    participants_db = (
        db.query(Participant)
        .filter(
            Participant.is_archived == 0
        )
        .order_by(
            Participant.id.asc()
        )
        .all()
    )

    evaluations = (
        db.query(
            ParticipantEvaluation
        )
        .all()
    )

    evaluation_tier = {
        evaluation.participant_id:
            evaluation.participant_tier
        for evaluation in evaluations
    }

    participants = []

    for participant in participants_db:

        fullname = " ".join(
            part
            for part in [
                participant.fname,
                participant.mname,
                participant.lname
            ]
            if part
        ).strip()

        participants.append({
            "id": participant.id,
            "registration_number":
                participant.registration_number,
            "fullname": fullname,
            "sex": participant.sex,
            "age": participant.registration_age,
            "age_group": (
                "Under 13"
                if participant.registration_age < 13
                else "13-15"
                if participant.registration_age <= 15
                else "16-18"
                if participant.registration_age <= 18
                else "19-21"
                if participant.registration_age <= 21
                else "22-25"
                if participant.registration_age <= 25
                else "26+"
            ),
            "tier":
                evaluation_tier.get(
                    participant.id
                ),
            "sector":
                participant.sector,
            "participant_type":
                participant.participant_type,
            "registration_status":
                participant.registration_status,
            "event_id":
                participant.event_id,
            "event_name":
                participant.event_name
        })


    # ========================================================
    # STAFF
    # ========================================================

    staff_db = (
        db.query(Staff)
        .filter(
            Staff.is_archived == 0
        )
        .order_by(
            Staff.id.asc()
        )
        .all()
    )

    staff = []

    for member in staff_db:

        fullname = " ".join(
            part
            for part in [
                member.fname,
                member.mname,
                member.lname
            ]
            if part
        ).strip()

        profile_completed = bool(
            member.sex
            and member.birthday
            and member.contact
            and member.local_church
            and member.sector
        )

        event = (
            db.query(Event)
            .filter(
                Event.id == member.event_id
            )
            .first()
        )

        staff.append({
            "id": member.id,
            "event_id": member.event_id,
            "event_name":
                event.event_name
                if event
                else None,
            "fullname": fullname,
            "position": member.position,
            "sex": member.sex,
            "sector": member.sector,
            "local_church": member.local_church,
            "profile_completed":
                profile_completed
        })


    # ========================================================
    # CHAPERONES
    # ========================================================

    chaperones_db = (
        db.query(Chaperone)
        .filter(
            Chaperone.is_archived == 0
        )
        .order_by(
            Chaperone.id.asc()
        )
        .all()
    )

    chaperones = []

    for chaperone in chaperones_db:

        fullname = " ".join(
            part
            for part in [
                chaperone.fname,
                chaperone.mname,
                chaperone.lname
            ]
            if part
        ).strip()

        event = (
            db.query(Event)
            .filter(
                Event.id == chaperone.event_id
            )
            .first()
        )

        chaperones.append({
            "id": chaperone.id,
            "event_id": chaperone.event_id,
            "event_name":
                event.event_name
                if event
                else None,
            "fullname": fullname,
            "sex": chaperone.sex,
            "sector": chaperone.sector,
            "local_church":
                chaperone.local_church
        })


    # ========================================================
    # REGISTRATION TEAM ACCOUNTS
    # ========================================================

    users_db = (
        db.query(User)
        .filter(
            User.role == "Registration Team"
        )
        .order_by(
            User.id.asc()
        )
        .all()
    )

    team_accounts = []

    for user in users_db:

        fullname = " ".join(
            part
            for part in [
                user.fname,
                user.mname,
                user.lname
            ]
            if part
        ).strip()

        team_accounts.append({
            "id": user.id,
            "fullname": fullname,
            "username": user.username,
            "email": user.email,
            "sector": user.sector,
            "local_church":
                user.local_church
        })


    # ========================================================
    # STORE INVENTORY
    #
    # StoreItem.price is already PHP.
    # ========================================================

    store_items_db = (
        db.query(StoreItem)
        .filter(
            StoreItem.is_archived == 0
        )
        .order_by(
            StoreItem.id.asc()
        )
        .all()
    )

    store_items = [
        {
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "quantity": item.quantity,
            "price": item.price
        }
        for item in store_items_db
    ]


    # ========================================================
    # STORE PURCHASES
    #
    # Payment.amount is stored in CENTAVOS.
    # Convert to PHP once.
    # ========================================================

    store_payments = (
        db.query(Payment)
        .filter(
            func.lower(
                Payment.payment_type
            ) == "store"
        )
        .order_by(
            Payment.id.desc()
        )
        .all()
    )

    store_item_map = {
        item.id: item
        for item in store_items_db
    }

    store_purchases = []

    for payment in store_payments:

        store_item = store_item_map.get(
            payment.store_item_id
        )

        quantity = int(
            payment.store_quantity or 1
        )

        amount_php = (
            float(payment.amount or 0)
            / 100
        )

        store_purchases.append({
            "id": payment.id,
            "store_item_id":
                payment.store_item_id,
            "item_name":
                store_item.item_name
                if store_item
                else "Unknown Item",
            "quantity": quantity,
            "amount": amount_php,
            "status":
                payment.status or "Pending",
            "customer_name":
                payment.customer_name,
            "customer_contact":
                payment.customer_contact,
            "customer_email":
                payment.customer_email,
            "created_at":
                payment.created_at,
            "paid_at":
                payment.paid_at
        })


    # ========================================================
    # CASH SPONSORS
    #
    # donation_amount is CENTAVOS.
    # ========================================================

    cash_sponsors_db = (
        db.query(CashSponsorship)
        .order_by(
            CashSponsorship.id.desc()
        )
        .all()
    )

    sponsors = []

    for sponsor in cash_sponsors_db:

        sponsors.append({
            "type": "Cash",
            "id": sponsor.id,
            "sponsor_name":
                sponsor.sponsor_name,
            "tier":
                sponsor.selected_tier,
            "item_name": None,
            "quantity": None,
            "amount":
                float(
                    sponsor.donation_amount or 0
                ) / 100,
            "status":
                sponsor.payment_status
                or "Pending",
            "sector":
                sponsor.sector,
            "created_at":
                sponsor.created_at,
            "paid_at":
                sponsor.paid_at
        })


    # ========================================================
    # ITEM SPONSORS
    # ========================================================

    item_sponsors_db = (
        db.query(ItemSponsorship)
        .order_by(
            ItemSponsorship.id.desc()
        )
        .all()
    )

    for sponsor in item_sponsors_db:

        sponsors.append({
            "type": "Item",
            "id": sponsor.id,
            "sponsor_name":
                sponsor.sponsor_name,
            "tier": None,
            "item_name":
                sponsor.item_name,
            "quantity":
                sponsor.quantity,
            "amount": None,
            "status":
                sponsor.status or "Confirmed",
            "sector":
                sponsor.sector,
            "created_at":
                sponsor.created_at,
            "paid_at": None
        })


    # ========================================================
    # SPONSORSHIP INVENTORY
    # ========================================================

    inventory_db = (
        db.query(SponsorshipItem)
        .filter(
            SponsorshipItem.is_active == True
        )
        .order_by(
            SponsorshipItem.id.asc()
        )
        .all()
    )

    sponsor_inventory = []

    for item in inventory_db:

        remaining = int(
            item.remaining_quantity or 0
        )

        sponsor_inventory.append({
            "id": item.id,
            "item_name":
                item.item_name,
            "description":
                item.description,
            "total_quantity":
                int(item.total_quantity or 0),
            "remaining_quantity":
                remaining,
            "unit":
                item.unit or "piece",
            "available":
                remaining > 0
        })


    # ========================================================
    # CASH DONATION FUND
    #
    # CashDonationTotal.total_amount is already PESOS.
    # Do NOT divide it by 100.
    # ========================================================

    donation_total = (
        db.query(
            CashDonationTotal
        )
        .order_by(
            CashDonationTotal.id.asc()
        )
        .first()
    )

    remaining_donation_fund = float(
        donation_total.total_amount
        if donation_total
        else 0
    )


    # ========================================================
    # TOTAL CASH DONATIONS RECEIVED
    #
    # cash_total_added is already PESOS.
    #
    # Only positive values represent donations added to the
    # donation pool.
    # ========================================================

    total_cash_received = (
        db.query(
            func.coalesce(
                func.sum(
                    CashSponsorship.cash_total_added
                ),
                0
            )
        )
        .scalar()
        or 0
    )

    total_cash_received = float(
        total_cash_received
    )


    # ========================================================
    # FINDING SPONSOR PARTICIPANTS
    # ========================================================

    finding_sponsor_query = (
        db.query(Participant)
        .filter(
            Participant.is_archived == 0,
            func.lower(
                Participant.participant_type
            ) == "finding sponsor"
        )
    )

    finding_sponsor_participants = (
        finding_sponsor_query.count()
    )


    # ========================================================
    # SUCCESSFULLY SPONSORED PARTICIPANTS
    #
    # Finding Sponsor + T-shirt Paid + Lanyard Paid
    # ========================================================

    total_sponsored_participants = (
        db.query(Participant)
        .filter(
            Participant.is_archived == 0,

            func.lower(
                Participant.participant_type
            ) == "finding sponsor",

            func.lower(
                func.coalesce(
                    Participant.tshirt_status,
                    "Unpaid"
                )
            ) == "paid",

            func.lower(
                func.coalesce(
                    Participant.lanyard_status,
                    "Unpaid"
                )
            ) == "paid"
        )
        .count()
    )


    # ========================================================
    # USED DONATION FUND
    #
    # Received - Current Remaining
    # ========================================================

    total_used_donation_fund = max(
        0,
        total_cash_received -
        remaining_donation_fund
    )


    # ========================================================
    # SPONSOR COUNTS
    # ========================================================

    cash_sponsor_total = len(
        cash_sponsors_db
    )

    item_sponsor_total = len(
        item_sponsors_db
    )


    # ========================================================
    # EVENT REPORT
    # ========================================================

    events_db = (
        db.query(Event)
        .filter(
            Event.is_archived == 0
        )
        .order_by(
            Event.id.asc()
        )
        .all()
    )

    events = []

    for event in events_db:

        participant_count = (
            db.query(Participant)
            .filter(
                Participant.event_id == event.id,
                Participant.is_archived == 0
            )
            .count()
        )

        staff_count = (
            db.query(Staff)
            .filter(
                Staff.event_id == event.id,
                Staff.is_archived == 0
            )
            .count()
        )

        chaperone_count = (
            db.query(Chaperone)
            .filter(
                Chaperone.event_id == event.id,
                Chaperone.is_archived == 0
            )
            .count()
        )

        if today < event.registration_start:
            event_status = "Upcoming"

        elif (
            event.registration_start <= today
            and today <= event.registration_end
        ):
            event_status = "Registration Open"

        elif (
            event.kickoff_date <= today
            and today <= event.wrapup_date
        ):
            event_status = "Ongoing"

        elif today > event.wrapup_date:
            event_status = "Completed"

        else:
            event_status = "Upcoming"

        total_attendees = (
            participant_count
            + staff_count
            + chaperone_count
        )

        events.append({
            "id": event.id,
            "event_name":
                event.event_name,
            "registration_start":
                event.registration_start,
            "registration_end":
                event.registration_end,
            "kickoff_date":
                event.kickoff_date,
            "wrapup_date":
                event.wrapup_date,
            "status":
                event_status,
            "participants":
                participant_count,
            "staff":
                staff_count,
            "chaperones":
                chaperone_count,
            "total_attendees":
                total_attendees
        })


    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "success": True,

        "participants":
            participants,

        "staff":
            staff,

        "chaperones":
            chaperones,

        "team_accounts":
            team_accounts,

        "store_items":
            store_items,

        "store_purchases":
            store_purchases,

        "sponsors":
            sponsors,

        "sponsor_inventory":
            sponsor_inventory,

        "sponsor_stats": {
            "cash_donation_total":
                remaining_donation_fund,

            "total_sponsored_participants":
                total_sponsored_participants,

            "total_used_donation_fund":
                total_used_donation_fund,

            "remaining_donation_fund":
                remaining_donation_fund,

            "finding_sponsor_participants":
                finding_sponsor_participants,

            "item_sponsor_total":
                item_sponsor_total,

            "cash_sponsor_total":
                cash_sponsor_total,

            "sponsor_inventory_total":
                len(sponsor_inventory)
        },

        "events":
            events
    }
    
