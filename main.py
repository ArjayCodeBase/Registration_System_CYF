from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, UploadFile, File
from starlette.requests import ClientDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
import uuid
import shutil
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
import smtplib
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
    StaticFiles(directory="uploads"),
    name="uploads"
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import httpx
import base64

from fastapi_mail import (
    FastMail,
    MessageSchema,
    ConnectionConfig
)

from pydantic import EmailStr

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
# GMAIL CONFIGURATION
# ======================================================

GMAIL_USERNAME = os.getenv(
    "GMAIL_USERNAME"
)

GMAIL_APP_PASSWORD = os.getenv(
    "GMAIL_APP_PASSWORD"
)

GMAIL_FROM_NAME = os.getenv(
    "GMAIL_FROM_NAME",
    "Event Registration System"
)








mail_conf = ConnectionConfig(
    MAIL_USERNAME=GMAIL_USERNAME,
    MAIL_PASSWORD=GMAIL_APP_PASSWORD,
    MAIL_FROM=GMAIL_USERNAME,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)








# ======================================================
# SQLITE DATABASE
# ======================================================

DATABASE_URL = "sqlite:///./registration_system.db"

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











def migrate_cash_sponsorship_cash_total_added():

    with engine.connect() as connection:

        # ====================================================
        # CHECK EXISTING COLUMNS
        # ====================================================

        result = connection.execute(
            text("""
                PRAGMA table_info(cash_sponsorships)
            """)
        )

        columns = {
            row[1]: row
            for row in result
        }

        # ====================================================
        # COLUMN DOES NOT EXIST
        # ====================================================
        #
        # If the column does not exist at all, simply create
        # it as INTEGER.
        #
        # ====================================================

        if "cash_total_added" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE cash_sponsorships
                    ADD COLUMN cash_total_added
                    INTEGER NOT NULL DEFAULT 0
                """)
            )

            connection.commit()

            print(
                "Created cash_total_added INTEGER column."
            )

            return

        # ====================================================
        # EXISTING COLUMN
        #
        # SQLite cannot directly change BOOLEAN -> INTEGER.
        #
        # Rename the old column first.
        # ====================================================

        old_column = columns[
            "cash_total_added"
        ]

        old_type = str(
            old_column[2] or ""
        ).upper()

        print(
            "Existing cash_total_added type:",
            old_type
        )

        # ====================================================
        # ALREADY INTEGER
        # ====================================================

        if old_type in [
            "INTEGER",
            "INT",
            "BIGINT"
        ]:

            print(
                "cash_total_added is already INTEGER."
            )

            connection.commit()

            return

        # ====================================================
        # RENAME OLD BOOLEAN COLUMN
        # ====================================================

        connection.execute(
            text("""
                ALTER TABLE cash_sponsorships
                RENAME COLUMN cash_total_added
                TO cash_total_added_old
            """)
        )

        # ====================================================
        # CREATE CORRECT INTEGER COLUMN
        # ====================================================

        connection.execute(
            text("""
                ALTER TABLE cash_sponsorships
                ADD COLUMN cash_total_added
                INTEGER NOT NULL DEFAULT 0
            """)
        )

        # ====================================================
        # BACKFILL OLD PAID CASH SPONSORSHIPS
        # ====================================================
        #
        # Old records did not have cash_total_added.
        #
        # If an old sponsorship is already Paid, assume its
        # donation amount has already been received.
        #
        # donation_amount is stored in centavos.
        #
        # Example:
        #
        # donation_amount = 50000
        # cash_total_added = 500
        #
        # This prevents old paid sponsorships from being added
        # again when the webhook is triggered.
        #
        # ====================================================

        connection.execute(
            text("""
                UPDATE cash_sponsorships
                SET cash_total_added =
                    CAST(
                        COALESCE(
                            donation_amount,
                            0
                        ) / 100
                        AS INTEGER
                    )
                WHERE LOWER(
                    COALESCE(
                        payment_status,
                        ''
                    )
                ) = 'paid'
            """)
        )

        # ====================================================
        # OLD PENDING / FAILED RECORDS
        #
        # These should remain 0 because their donation has not
        # been added to CashDonationTotal.
        # ====================================================

        connection.execute(
            text("""
                UPDATE cash_sponsorships
                SET cash_total_added = 0
                WHERE LOWER(
                    COALESCE(
                        payment_status,
                        ''
                    )
                ) != 'paid'
            """)
        )

        # ====================================================
        # DROP OLD BOOLEAN COLUMN
        # ====================================================
        #
        # SQLite versions supporting DROP COLUMN can remove it.
        #
        # ====================================================

        try:

            connection.execute(
                text("""
                    ALTER TABLE cash_sponsorships
                    DROP COLUMN cash_total_added_old
                """)
            )

        except Exception as e:

            print(
                "WARNING: Could not drop old "
                "cash_total_added_old column:",
                repr(e)
            )

            print(
                "The old column can remain temporarily."
            )

        # ====================================================
        # COMMIT
        # ====================================================

        connection.commit()

        print(
            "cash_total_added successfully migrated "
            "to INTEGER."
        )







def migrate_staff_table():
    inspector = inspect(engine)

    columns = {
        column["name"]
        for column in inspector.get_columns("staff")
    }

    with engine.begin() as conn:

        if "position" not in columns:
            conn.execute(
                text("ALTER TABLE staff ADD COLUMN position VARCHAR")
            )

        if "sex" in columns:
            pass

        if "birthday" in columns:
            pass

        if "contact" in columns:
            pass

        if "local_church" in columns:
            pass

        if "sector" in columns:
            pass


# ============================================================
# MIGRATE CASH SPONSORSHIP COLUMNS
# ============================================================

def migrate_cash_sponsorship_columns():

    with engine.connect() as connection:

        # ----------------------------------------------------
        # CHECK EXISTING COLUMNS
        # ----------------------------------------------------

        result = connection.execute(
            text(
                "PRAGMA table_info(cash_sponsorships)"
            )
        )

        columns = [
            row[1]
            for row in result
        ]

        # ----------------------------------------------------
        # ADD CASH TOTAL ADDED
        # ----------------------------------------------------

        if "cash_total_added" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE cash_sponsorships
                    ADD COLUMN cash_total_added
                    BOOLEAN
                    DEFAULT 0
                    NOT NULL
                """)
            )

            connection.commit()

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # OLD PAID SPONSORSHIPS
        #
        # These records existed before
        # cash_total_added was created.
        #
        # Mark them as already added so the new
        # sponsorship logic does NOT add them again.
        # ----------------------------------------------------

        connection.execute(
            text("""
                UPDATE cash_sponsorships

                SET cash_total_added = 1

                WHERE
                    LOWER(
                        TRIM(
                            COALESCE(
                                payment_status,
                                ''
                            )
                        )
                    )

                    IN (
                        'paid',
                        'success',
                        'succeeded',
                        'completed'
                    )
            """)
        )

        # ----------------------------------------------------
        # OLD PENDING / FAILED RECORDS
        #
        # These should NOT be added to the cash total.
        # ----------------------------------------------------

        connection.execute(
            text("""
                UPDATE cash_sponsorships

                SET cash_total_added = 0

                WHERE
                    LOWER(
                        TRIM(
                            COALESCE(
                                payment_status,
                                ''
                            )
                        )
                    )

                    NOT IN (
                        'paid',
                        'success',
                        'succeeded',
                        'completed'
                    )
            """)
        )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        connection.commit()




# ============================================================
# MIGRATE STORE ITEM TABLE
# ============================================================

def migrate_store_item_columns():

    with engine.connect() as connection:

        result = connection.execute(
            text("PRAGMA table_info(store_items)")
        )

        columns = [
            row[1]
            for row in result
        ]

        # ----------------------------------------------------
        # CATEGORY
        # ----------------------------------------------------

        if "category" not in columns: 

            connection.execute(
                text("""
                    ALTER TABLE store_items
                    ADD COLUMN category
                    VARCHAR(50)
                    NOT NULL
                    DEFAULT 'others'
                """)
            )

        # ----------------------------------------------------
        # SIZES
        # ----------------------------------------------------

        if "sizes" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE store_items
                    ADD COLUMN sizes
                    TEXT
                """)
            )

        # ----------------------------------------------------
        # IMAGE
        # ----------------------------------------------------

        if "image_url" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE store_items
                    ADD COLUMN image_url
                    TEXT
                """)
            )

        # ----------------------------------------------------
        # COMMIT
        # ----------------------------------------------------

        connection.commit()







    
    
# ======================================================
# MIGRATE PAYMENT TABLE
# ======================================================

def migrate_payment_columns():

    with engine.connect() as connection:

        result = connection.execute(
            text("PRAGMA table_info(payments)")
        )

        columns = [
            row[1]
            for row in result
        ]

        # ----------------------------------------------
        # PAYMENT TYPE
        # ----------------------------------------------

        if "payment_type" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE payments
                    ADD COLUMN payment_type
                    VARCHAR(30)
                    NOT NULL
                    DEFAULT 'Participant'
                """)
            )

        # ----------------------------------------------
        # SPONSORSHIP TIER
        # ----------------------------------------------

        if "sponsorship_tier" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE payments
                    ADD COLUMN sponsorship_tier
                    VARCHAR(30)
                """)
            )

        # ----------------------------------------------
        # SPONSOR ID
        # ----------------------------------------------

        if "sponsor_id" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE payments
                    ADD COLUMN sponsor_id
                    INTEGER
                """)
            )

        # ----------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------

        if "description" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE payments
                    ADD COLUMN description
                    VARCHAR(500)
                """)
            )

        # ----------------------------------------------
        # CUSTOMER NAME
        # ----------------------------------------------

        if "customer_name" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE payments
                    ADD COLUMN customer_name
                    VARCHAR(150)
                """)
            )

        # ----------------------------------------------
        # CUSTOMER CONTACT
        # ----------------------------------------------

        if "customer_contact" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE payments
                    ADD COLUMN customer_contact
                    VARCHAR(50)
                """)
            )

        # ----------------------------------------------
        # CUSTOMER EMAIL
        # ----------------------------------------------

        if "customer_email" not in columns:

            connection.execute(
                text("""
                    ALTER TABLE payments
                    ADD COLUMN customer_email
                    VARCHAR(255)
                """)
            )

        connection.commit()


# ======================================================
# MAKE PARTICIPANT ID NULLABLE
#
# REQUIRED FOR STORE PAYMENTS
# ======================================================

def migrate_payment_participant_nullable():

    with engine.connect() as connection:

        # --------------------------------------------------
        # CHECK PAYMENTS TABLE
        # --------------------------------------------------

        result = connection.execute(
            text("""
                PRAGMA table_info(payments)
            """)
        )

        columns = list(result)

        participant_column = None

        for column in columns:

            # PRAGMA table_info:
            #
            # column[0] = cid
            # column[1] = name
            # column[2] = type
            # column[3] = notnull
            # column[4] = default
            # column[5] = primary key

            if column[1] == "participant_id":

                participant_column = column

                break

        # --------------------------------------------------
        # PARTICIPANT COLUMN NOT FOUND
        # --------------------------------------------------

        if participant_column is None:

            raise RuntimeError(
                "payments.participant_id column was not found."
            )

        # --------------------------------------------------
        # ALREADY NULLABLE
        # --------------------------------------------------

        if participant_column[3] == 0:

            print(
                "Payment migration: "
                "participant_id is already nullable."
            )

            return

        # --------------------------------------------------
        # GET ORIGINAL TABLE SQL
        # --------------------------------------------------

        result = connection.execute(
            text("""
                SELECT sql
                FROM sqlite_master
                WHERE type = 'table'
                AND name = 'payments'
            """)
        )

        row = result.fetchone()

        if not row or not row[0]:

            raise RuntimeError(
                "Unable to read payments table definition."
            )

        original_sql = row[0]

        # --------------------------------------------------
        # RENAME ORIGINAL TABLE
        # --------------------------------------------------

        connection.execute(
            text("""
                ALTER TABLE payments
                RENAME TO payments_old
            """)
        )

        # --------------------------------------------------
        # CHANGE PARTICIPANT_ID
        #
        # Remove NOT NULL from participant_id only.
        # --------------------------------------------------

        new_sql = original_sql

        replacements = [

            (
                '"participant_id" INTEGER NOT NULL',
                '"participant_id" INTEGER'
            ),

            (
                '`participant_id` INTEGER NOT NULL',
                '`participant_id` INTEGER'
            ),

            (
                'participant_id INTEGER NOT NULL',
                'participant_id INTEGER'
            ),

            (
                '"participant_id" INTEGER NOT NULL DEFAULT',
                '"participant_id" INTEGER DEFAULT'
            ),

            (
                '`participant_id` INTEGER NOT NULL DEFAULT',
                '`participant_id` INTEGER DEFAULT'
            ),

            (
                'participant_id INTEGER NOT NULL DEFAULT',
                'participant_id INTEGER DEFAULT'
            )
        ]

        for old_text, new_text in replacements:

            new_sql = new_sql.replace(
                old_text,
                new_text
            )

        # --------------------------------------------------
        # CHANGE TABLE NAME
        # --------------------------------------------------

        new_sql = new_sql.replace(
            '"payments"',
            '"payments_new"',
            1
        )

        new_sql = new_sql.replace(
            '`payments`',
            '`payments_new`',
            1
        )

        # Handle unquoted CREATE TABLE payments
        if (
            "CREATE TABLE payments_new"
            not in new_sql
        ):

            new_sql = new_sql.replace(
                "CREATE TABLE payments",
                "CREATE TABLE payments_new",
                1
            )

        # --------------------------------------------------
        # VERIFY PARTICIPANT_ID IS NOW NULLABLE
        # --------------------------------------------------

        if (
            'participant_id INTEGER NOT NULL'
            in new_sql
            or
            '"participant_id" INTEGER NOT NULL'
            in new_sql
            or
            '`participant_id` INTEGER NOT NULL'
            in new_sql
        ):

            # Roll back before raising the error.
            connection.rollback()

            raise RuntimeError(
                "Unable to make payments.participant_id nullable. "
                "The existing SQLite table definition has an "
                "unexpected format."
            )

        # --------------------------------------------------
        # CREATE NEW PAYMENTS TABLE
        # --------------------------------------------------

        connection.execute(
            text(new_sql)
        )

        # --------------------------------------------------
        # GET COLUMN NAMES
        # --------------------------------------------------

        column_result = connection.execute(
            text("""
                PRAGMA table_info(payments_old)
            """)
        )

        column_names = [
            row[1]
            for row in column_result
        ]

        if not column_names:

            connection.rollback()

            raise RuntimeError(
                "Unable to read columns from payments_old."
            )

        column_list = ", ".join(
            f'"{column}"'
            for column in column_names
        )

        # --------------------------------------------------
        # COPY EXISTING PAYMENT DATA
        # --------------------------------------------------

        connection.execute(
            text(
                f"""
                INSERT INTO payments_new (
                    {column_list}
                )
                SELECT
                    {column_list}
                FROM payments_old
                """
            )
        )

        # --------------------------------------------------
        # REMOVE OLD TABLE
        # --------------------------------------------------

        connection.execute(
            text("""
                DROP TABLE payments_old
            """)
        )

        # --------------------------------------------------
        # RENAME NEW TABLE
        # --------------------------------------------------

        connection.execute(
            text("""
                ALTER TABLE payments_new
                RENAME TO payments
            """)
        )

        connection.commit()

        print(
            "Payment migration: "
            "participant_id is now nullable."
        )


# ======================================================
# STAFF DATABASE MIGRATION
# ======================================================

def migrate_staff_columns():
    """Add Staff.position and allow profile fields to remain empty for admin-created placeholders."""
    from sqlalchemy import text

    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(staff)")).fetchall()
        if not columns:
            return

        names = {row[1] for row in columns}
        if "position" not in names:
            connection.execute(text("ALTER TABLE staff ADD COLUMN position VARCHAR(100)"))

        # SQLite cannot directly change NOT NULL columns. Rebuild only when the
        # existing staff table still has the old NOT NULL profile columns.
        info = connection.execute(text("PRAGMA table_info(staff)")).fetchall()
        notnull = {row[1]: row[3] for row in info}
        needs_rebuild = any(notnull.get(col) == 1 for col in [
            "sex", "birthday", "contact", "local_church", "sector"
        ])

        if not needs_rebuild:
            return

        connection.execute(text("PRAGMA foreign_keys=OFF"))
        connection.execute(text("DROP TABLE IF EXISTS staff_new"))
        connection.execute(text("""
            CREATE TABLE staff_new (
                id INTEGER PRIMARY KEY,
                event_id INTEGER NOT NULL,
                fname VARCHAR(100) NOT NULL,
                mname VARCHAR(100),
                lname VARCHAR(100) NOT NULL,
                position VARCHAR(100) NOT NULL DEFAULT '',
                sex VARCHAR(20),
                birthday DATE,
                contact VARCHAR(20),
                local_church VARCHAR(150),
                sector VARCHAR(100),
                is_archived INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        connection.execute(text("""
            INSERT INTO staff_new
            (id,event_id,fname,mname,lname,position,sex,birthday,contact,local_church,sector,is_archived,created_at,updated_at)
            SELECT id,event_id,fname,mname,lname,COALESCE(position,''),sex,birthday,contact,local_church,sector,is_archived,created_at,updated_at
            FROM staff
        """))
        connection.execute(text("DROP TABLE staff"))
        connection.execute(text("ALTER TABLE staff_new RENAME TO staff"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_staff_id ON staff (id)"))
        connection.execute(text("PRAGMA foreign_keys=ON"))


# ======================================================
# CREATE TABLES
# ======================================================

Base.metadata.create_all(
    bind=engine
)


# ======================================================
# RUN STAFF MIGRATION
# ======================================================

migrate_staff_columns()


# ======================================================
# RUN PAYMENT MIGRATIONS
# ======================================================

migrate_payment_columns()


# ======================================================
# MAKE STORE PAYMENTS POSSIBLE
# ======================================================

migrate_payment_participant_nullable()

migrate_store_item_columns()

migrate_cash_sponsorship_columns()

migrate_staff_table()






























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
# ======================================================

class PaymentCreateSchema(BaseModel):

    participant_id: int

    tshirt_selected: bool = False

    lanyard_selected: bool = False

    tshirt_size: Optional[str] = None


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
# STORE SCHEMAS
# ============================================================

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
# STORE PURCHASE SCHEMA
# ============================================================

class StorePurchaseSchema(BaseModel):
    store_item_id: int
    quantity: int = 1

    customer_name: str
    customer_contact: str
    customer_email: str

    size: str | None = None



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

GMAIL_USERNAME = os.getenv(
    "GMAIL_USERNAME"
)

GMAIL_APP_PASSWORD = os.getenv(
    "GMAIL_APP_PASSWORD"
)

GMAIL_FROM_NAME = os.getenv(
    "GMAIL_FROM_NAME",
    "Event Registration System"
)

CONTACT_RECEIVER = (
    "matulacarianjay1@gmail.com"
)


# ==========================================================
# SEND CONTACT EMAIL
# ==========================================================

def send_contact_email(
    contact: ContactRequest
):

    if not GMAIL_USERNAME:
        raise RuntimeError(
            "GMAIL_USERNAME is not configured."
        )

    if not GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "GMAIL_APP_PASSWORD is not configured."
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
    # Create email
    # ------------------------------------------------------

    email_message = EmailMessage()


    # IMPORTANT:
    #
    # Do NOT put "\n" inside Subject.
    #
    # This is correct:
    #
    # Subject: Contact Us Message - User Subject
    #

    email_message["Subject"] = (
        f"Contact Us Message - {subject}"
    )


    email_message["From"] = (
        f"{GMAIL_FROM_NAME} <{GMAIL_USERNAME}>"
    )


    email_message["To"] = (
        CONTACT_RECEIVER
    )


    email_message["Reply-To"] = (
        sender_email
    )


    # ------------------------------------------------------
    # Email body
    # ------------------------------------------------------

    email_body = f"""
Contact Us Message

Name:
{name}

Email:
{sender_email}

Subject:
{subject}

Message:
{message}

--------------------------------------------------
This message was submitted through the
CYF Registration System Contact Us form.
"""


    email_message.set_content(
        email_body.strip()
    )


    # ------------------------------------------------------
    # Send through Gmail SMTP
    # ------------------------------------------------------

    with smtplib.SMTP(
        "smtp.gmail.com",
        587,
        timeout=30
    ) as server:

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            GMAIL_USERNAME,
            GMAIL_APP_PASSWORD.replace(" ", "")
        )

        server.send_message(
            email_message
        )

# ============================================================
# ITEM SPONSORSHIP RESPONSE
# ============================================================

from typing import Optional

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
    # CREATE MESSAGE
    # --------------------------------------------------

    message = MessageSchema(

        subject=subject,

        recipients=[
            participant.email
        ],

        body=html,

        subtype="html"
    )

    # --------------------------------------------------
    # SEND
    # --------------------------------------------------

    try:

        fm = FastMail(mail_conf)

        await fm.send_message(message)

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

    message = MessageSchema(

        subject=(
            "Payment Confirmed - "
            f"{participant.registration_number}"
        ),

        recipients=[
            participant.email
        ],

        body=html_body,

        subtype="html"
    )

    fm = FastMail(
        mail_conf
    )

    await fm.send_message(
        message
    )

    print(
        f"Payment confirmation sent to "
        f"{participant.email}"
    )


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
    # CREATE MESSAGE
    # ==================================================

    message = MessageSchema(

        subject=(
            "Registration Completed Through Sponsorship - "
            f"{participant.registration_number}"
        ),

        recipients=[
            participant.email
        ],

        body=html_body,

        subtype="html"
    )


    # ==================================================
    # USE YOUR EXISTING MAIL CONFIGURATION
    # ==================================================

    fm = FastMail(
        mail_conf
    )


    await fm.send_message(
        message
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

    sponsor_name = (
        sponsor.fname
        or ""
    )

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

    message = f"""
Dear {sponsor_name},

Thank you for your generous donation.

Sponsorship Tier:
{tier}

Donation Amount:
₱{amount:,.2f}

Your sponsorship payment has been successfully received.

We sincerely appreciate your support.

Thank you,
CYF Registration Team
"""

    # Use your existing email sending function here.
    # Example:
    #
    # await send_email(
    #     to=sponsor.email,
    #     subject=subject,
    #     body=message
    # )

    print(
        "Sponsor confirmation email prepared for:",
        sponsor.email
    )

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

        # --------------------------------------------------
        # GET INFORMATION
        # --------------------------------------------------

        sponsor_name = getattr(
            sponsorship,
            "sponsor_name",
            "Sponsor"
        )

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

        # Your database stores the donation amount
        # in centavos, so convert it back to PHP.

        try:

            donation_amount_php = (
                Decimal(
                    str(donation_amount)
                ) / Decimal("100")
            )

        except Exception:

            donation_amount_php = Decimal("0.00")

        payment_status = getattr(
            payment,
            "status",
            "Paid"
        )

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
        # EMAIL MESSAGE
        # --------------------------------------------------

        body = f"""
Dear {sponsor_name},

Thank you for your generous support of the CYF ministry.

We are pleased to confirm that your cash sponsorship
payment has been successfully received.

SPONSORSHIP DETAILS
----------------------------------------
Name: {sponsor_name}
Sponsorship Tier: {tier}
Donation Amount: ₱{donation_amount_php:,.2f}
Payment Status: {payment_status}
"""

        if reference:

            body += f"""
PayMongo Reference: {reference}
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
        # SEND EMAIL
        # --------------------------------------------------

        message = MIMEMultipart()

        message["From"] = (
            f"{GMAIL_FROM_NAME} <{GMAIL_USERNAME}>"
        )

        message["To"] = sponsor_email

        message["Subject"] = subject

        message.attach(
            MIMEText(
                body,
                "plain",
                "utf-8"
            )
        )

        # --------------------------------------------------
        # GMAIL SMTP
        # --------------------------------------------------

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as server:

            server.starttls()

            server.login(
                GMAIL_USERNAME,
                GMAIL_APP_PASSWORD
            )

            server.sendmail(
                GMAIL_USERNAME,
                sponsor_email,
                message.as_string()
            )

        print(
            "Cash sponsorship confirmation email sent to:",
            sponsor_email
        )

        return True

    except Exception as e:

        print(
            "Cash sponsorship confirmation email failed:",
            repr(e)
        )

        return False



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

We are pleased to confirm that your item donation sponsorship has been successfully recorded.

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

Thank you again for your generosity and willingness to support CYF events.

Your contribution will help provide the necessary resources and materials for our youth ministry activities.

We sincerely appreciate your support.

God bless you!

CYF Registration System
"""

        # ----------------------------------------------------
        # SEND EMAIL
        # ----------------------------------------------------

        msg = MIMEMultipart()

        msg["From"] = (
            f"{GMAIL_FROM_NAME} "
            f"<{GMAIL_USERNAME}>"
        )

        msg["To"] = recipient_email

        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                body,
                "plain",
                "utf-8"
            )
        )

        # ----------------------------------------------------
        # GMAIL SMTP
        # ----------------------------------------------------

        with smtplib.SMTP(
            "smtp.gmail.com", 
            587
        ) as server:

            server.starttls()

            server.login(
                GMAIL_USERNAME,
                GMAIL_APP_PASSWORD
            )

            server.sendmail(
                GMAIL_USERNAME,
                recipient_email,
                msg.as_string()
            )

        print(
            "Item sponsorship confirmation email sent to:",
            recipient_email
        )

        return True

    except Exception as e:

        print(
            "Item sponsorship confirmation email failed:",
            e
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

    participants = db.query(Participant).filter(
        Participant.is_archived == 0
    ).all()

    result = []

    keyword = (keyword or "").strip().lower()

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
        # SAFE STRING VALUES
        # ==================================================

        registration_number = str(
            participant.registration_number or ""
        ).lower()

        email = str(
            participant.email or ""
        ).lower()

        contact_number = str(
            participant.contact_number or ""
        ).lower()

        event_name = str(
            participant.event_name or ""
        ).lower()

        registration_phase = str(
            participant.registration_phase or ""
        ).lower()

        registration_status = str(
            participant.registration_status or ""
        ).lower()

        participant_type = str(
            participant.participant_type or ""
        ).strip()

        participant_type_lower = participant_type.lower()

        tshirt_status = str(
            participant.tshirt_status or "Unpaid"
        )

        lanyard_status = str(
            participant.lanyard_status or "Unpaid"
        )

        tshirt_status_lower = tshirt_status.lower()
        lanyard_status_lower = lanyard_status.lower()

        # ==================================================
        # DETERMINE PARTICIPANT TYPE
        # ==================================================

        is_sponsor_participant = (
            participant_type_lower
            == "finding sponsor"
        )

        # ==================================================
        # MERCHANDISE / PAYMENT STATUS
        # ==================================================
        #
        # REGULAR PARTICIPANT
        #
        # Lanyard paid + shirt paid
        #       -> Paid
        #
        # Lanyard paid + shirt unpaid
        #       -> Partial
        #
        # Nothing paid
        #       -> Unpaid
        #
        #
        # FINDING SPONSOR
        #
        # No payment button should be displayed.
        #
        # Sponsorship is handled separately.
        #
        # ==================================================

        if is_sponsor_participant:

            # ----------------------------------------------
            # SPONSORSHIP STATUS
            # ----------------------------------------------

            sponsorship_status = "Sponsored in Review"

            # ----------------------------------------------
            # CHECK MERCHANDISE
            # ----------------------------------------------

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

            # ----------------------------------------------
            # NORMAL PARTICIPANT
            # ----------------------------------------------

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

        participant_tier_lower = str(
            participant_tier or ""
        ).lower()

        # ==================================================
        # SEARCH
        # ==================================================

        searchable_values = [

            fullname_lower,

            registration_number,

            email,

            contact_number,

            event_name,

            registration_phase,

            registration_status,

            participant_type_lower,

            payment_status.lower(),

            tshirt_status_lower,

            lanyard_status_lower,

            participant_tier_lower,

            str(
                sponsorship_status or ""
            ).lower(),

            str(
                merchandise_status or ""
            ).lower()

        ]

        matched = any(
            keyword in value
            for value in searchable_values
        )

        if not matched:
            continue

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
                participant.tshirt_status
                or "Unpaid",

            "lanyard_status":
                participant.lanyard_status
                or "Unpaid",

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

    # ==================================================
    # FIND PARTICIPANT
    # ==================================================

    participant = db.query(Participant).filter(
        Participant.id == participant_id,
        Participant.is_archived == 0
    ).first()

    if not participant:

        raise HTTPException(
            status_code=404,
            detail="Participant not found."
        )

    # ==================================================
    # PARTICIPANT FULL NAME
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
    # GET ACTIVE REGISTRATION ITEMS
    # ==================================================

    registration_items = (
        db.query(RegistrationItem)
        .filter(
            RegistrationItem.is_active == True
        )
        .all()
    )

    # ==================================================
    # FIND T-SHIRT
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
    # FIND LANYARD
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
    # PRICES
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
    # GET PAYMENTS
    # ==================================================

    payments = (
        db.query(Payment)
        .filter(
            Payment.participant_id == participant.id
        )
        .order_by(
            Payment.created_at.desc()
        )
        .all()
    )

    # ==================================================
    # SUCCESSFUL PAYMENT STATUSES
    # ==================================================

    successful_statuses = [
        "paid",
        "success",
        "succeeded",
        "completed"
    ]

    # ==================================================
    # CHECK SUCCESSFUL T-SHIRT PAYMENT
    # ==================================================

    tshirt_paid = any(

        bool(p.tshirt_selected)

        and str(
            p.status or ""
        ).lower() in successful_statuses

        for p in payments

    )

    # ==================================================
    # CHECK SUCCESSFUL LANYARD PAYMENT
    # ==================================================

    lanyard_paid = any(

        bool(p.lanyard_selected)

        and str(
            p.status or ""
        ).lower() in successful_statuses

        for p in payments

    )

    # ==================================================
    # FALLBACK TO PARTICIPANT STATUS
    # ==================================================

    if str(
        participant.tshirt_status or ""
    ).lower() == "paid":

        tshirt_paid = True

    if str(
        participant.lanyard_status or ""
    ).lower() == "paid":

        lanyard_paid = True

    # ==================================================
    # UPDATE PARTICIPANT STATUS
    # ==================================================

    participant.tshirt_status = (
        "Paid"
        if tshirt_paid
        else "Unpaid"
    )

    participant.lanyard_status = (
        "Paid"
        if lanyard_paid
        else "Unpaid"
    )

    participant.updated_at = datetime.datetime.now()

    db.commit()

    # ==================================================
    # RETURN PAYMENT STATUS
    # ==================================================

    return {

        # ==================================================
        # PARTICIPANT INFORMATION
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
                else "Unpaid"

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
                else "Unpaid"

        },

        # ==================================================
        # PAYMENTS
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
                        p.tshirt_selected
                    ),

                "lanyard_selected":
                    bool(
                        p.lanyard_selected
                    ),

                "tshirt_size":
                    p.tshirt_size,

                "checkout_url":
                    p.checkout_url,

                "paymongo_reference":
                    p.paymongo_reference,

                "created_at":
                    p.created_at,

                "paid_at":
                    p.paid_at

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
# ======================================================

@app.post("/create_payment")
def create_payment(
    data: PaymentCreateSchema,
    db: Session = Depends(get_db)
):

    # ==================================================
    # DEBUG REQUEST
    # ==================================================

    print()
    print("=" * 70)
    print("CREATE PAYMENT REQUEST")
    print("=" * 70)

    print("Participant ID:", data.participant_id)
    print("Raw T-Shirt:", getattr(data, "tshirt", None))
    print("Raw Lanyard:", getattr(data, "lanyard", None))
    print("Raw T-Shirt Selected:", getattr(data, "tshirt_selected", None))
    print("Raw Lanyard Selected:", getattr(data, "lanyard_selected", None))
    print("T-Shirt Size:", getattr(data, "tshirt_size", None))

    print("=" * 70)


    # ==================================================
    # FIND PARTICIPANT
    # ==================================================

    participant = (
        db.query(Participant)
        .filter(
            Participant.id == data.participant_id,
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
    # NORMALIZE ITEM SELECTION
    #
    # Supports:
    #
    # data.tshirt
    # data.lanyard
    #
    # and also:
    #
    # data.tshirt_selected
    # data.lanyard_selected
    # ==================================================

    tshirt_value = getattr(
        data,
        "tshirt",
        None
    )

    lanyard_value = getattr(
        data,
        "lanyard",
        None
    )


    # If tshirt/lanyard are not present,
    # try tshirt_selected/lanyard_selected.

    if tshirt_value is None:

        tshirt_value = getattr(
            data,
            "tshirt_selected",
            False
        )


    if lanyard_value is None:

        lanyard_value = getattr(
            data,
            "lanyard_selected",
            False
        )


    tshirt_requested = bool(
        tshirt_value
    )

    lanyard_requested = bool(
        lanyard_value
    )


    print(
        "T-Shirt requested:",
        tshirt_requested
    )

    print(
        "Lanyard requested:",
        lanyard_requested
    )


    # ==================================================
    # MAKE SURE SOMETHING WAS SELECTED
    # ==================================================

    if (
        not tshirt_requested
        and not lanyard_requested
    ):

        raise HTTPException(
            status_code=400,
            detail="Please select at least one registration item."
        )


    # ==================================================
    # GET ALL PAYMENTS FOR PARTICIPANT
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
    # SUCCESSFUL PAYMENT STATUSES
    # ==================================================

    successful_statuses = {

        "paid",
        "success",
        "succeeded",
        "completed"

    }


    # ==================================================
    # CHECK SUCCESSFULLY PAID T-SHIRT
    # ==================================================

    tshirt_paid = False


    for payment in payments:

        payment_status = str(
            payment.status or ""
        ).strip().lower()


        if (
            payment.tshirt_selected
            and payment_status in successful_statuses
        ):

            tshirt_paid = True

            break


    # ==================================================
    # CHECK SUCCESSFULLY PAID LANYARD
    # ==================================================

    lanyard_paid = False


    for payment in payments:

        payment_status = str(
            payment.status or ""
        ).strip().lower()


        if (
            payment.lanyard_selected
            and payment_status in successful_statuses
        ):

            lanyard_paid = True

            break


    # ==================================================
    # ALSO CHECK PARTICIPANT STATUS
    #
    # Only use this if there are no payment records
    # representing the item.
    #
    # This keeps compatibility with your existing system.
    # ==================================================

    if not payments:

        if str(
            participant.tshirt_status or ""
        ).strip().lower() == "paid":

            tshirt_paid = True


        if str(
            participant.lanyard_status or ""
        ).strip().lower() == "paid":

            lanyard_paid = True


    # ==================================================
    # DEBUG PAYMENT STATUS
    # ==================================================

    print()
    print("=" * 70)
    print("PAYMENT STATUS CHECK")
    print("=" * 70)

    print(
        "Participant T-Shirt Status:",
        participant.tshirt_status
    )

    print(
        "Participant Lanyard Status:",
        participant.lanyard_status
    )

    print(
        "T-Shirt Paid:",
        tshirt_paid
    )

    print(
        "Lanyard Paid:",
        lanyard_paid
    )

    print("=" * 70)


    # ==================================================
    # REMOVE ITEMS THAT ARE ALREADY PAID
    # ==================================================

    if tshirt_requested and tshirt_paid:

        tshirt_requested = False

        print(
            "T-Shirt removed because it is already paid."
        )


    if lanyard_requested and lanyard_paid:

        lanyard_requested = False

        print(
            "Lanyard removed because it is already paid."
        )


    # ==================================================
    # CHECK REMAINING ITEMS
    # ==================================================

    if (
        not tshirt_requested
        and not lanyard_requested
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                "All selected items have already been paid."
            )

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

            raise HTTPException(

                status_code=400,

                detail=(
                    "Please select a T-shirt size."
                )

            )


        tshirt_size = (
            requested_size
            .strip()
            .upper()
        )


        allowed_sizes = [

            "M",
            "L",
            "XL"

        ]


        if tshirt_size not in allowed_sizes:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Invalid T-shirt size. "
                    "Please select M, L, or XL."
                )

            )


    # ==================================================
    # PRICES
    # ==================================================

    TSHIRT_PRICE = 35000

    LANYARD_PRICE = 9000


    # ==================================================
    # CALCULATE AMOUNT
    # ==================================================

    amount = 0

    selected_items = []


    if tshirt_requested:

        amount += TSHIRT_PRICE

        selected_items.append(
            f"T-Shirt ({tshirt_size})"
        )


    if lanyard_requested:

        amount += LANYARD_PRICE

        selected_items.append(
            "Lanyard"
        )


    # ==================================================
    # VALIDATE AMOUNT
    # ==================================================

    if amount <= 0:

        raise HTTPException(

            status_code=400,

            detail=(
                "There is no remaining amount to pay."
            )

        )


    # ==================================================
    # FIND EXISTING PENDING PAYMENT
    #
    # IMPORTANT:
    # Ignore old Unpaid/Failed payments.
    # Only reuse an active Pending payment.
    # ==================================================

    existing_payment = (
        db.query(Payment)
        .filter(

            Payment.participant_id ==
            participant.id,

            Payment.status ==
            "Pending",

            Payment.tshirt_selected ==
            int(tshirt_requested),

            Payment.lanyard_selected ==
            int(lanyard_requested)

        )
        .first()
    )


    # ==================================================
    # RETURN EXISTING CHECKOUT LINK
    # ==================================================

    if existing_payment:

        if existing_payment.checkout_url:

            print(
                "Existing pending payment found:",
                existing_payment.id
            )


            return {

                "message":
                    "A payment link already exists.",

                "payment_id":
                    existing_payment.id,

                "participant_id":
                    participant.id,

                "registration_number":
                    participant.registration_number,

                "items":
                    selected_items,

                "tshirt_size":
                    existing_payment.tshirt_size,

                "amount":
                    existing_payment.amount,

                "amount_display":
                    (
                        f"₱"
                        f"{(
                            existing_payment.amount or 0
                        ) / 100:,.2f}"
                    ),

                "currency":
                    existing_payment.currency,

                "status":
                    existing_payment.status,

                "checkout_url":
                    existing_payment.checkout_url,

                "paymongo_link_id":
                    existing_payment.paymongo_link_id,

                "paymongo_reference":
                    existing_payment.paymongo_reference

            }


    # ==================================================
    # FIND FULL NAME
    # ==================================================

    fullname = (
        f"{participant.fname or ''} "
        f"{participant.mname or ''} "
        f"{participant.lname or ''}"
    ).strip()


    # ==================================================
    # CREATE LOCAL PAYMENT
    # ==================================================

    payment = Payment(

        participant_id =
            participant.id,

        amount =
            amount,

        currency =
            "PHP",

        status =
            "Pending",

        tshirt_selected =
            int(tshirt_requested),

        lanyard_selected =
            int(lanyard_requested),

        tshirt_size =
            tshirt_size

    )


    db.add(payment)

    db.commit()

    db.refresh(payment)


    # ==================================================
    # PAYMONGO DESCRIPTION
    # ==================================================

    description = (

        "CYF Merchandise Payment - "

        f"{participant.registration_number}"

    )


    # ==================================================
    # PAYMONGO REMARKS
    # ==================================================

    remarks = (

        f"Participant: {fullname} | "

        f"Registration: "
        f"{participant.registration_number} | "

        f"Items: "
        f"{', '.join(selected_items)}"

    )


    # ==================================================
    # PAYMONGO URL
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
            amount,

        "currency":
            "PHP",

        "description":
            description,

        "remarks":
            remarks,

        "metadata": {

            "participant_id":
                str(participant.id),

            "payment_id":
                str(payment.id),

            "registration_number":
                participant.registration_number,

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

        f"cyf-payment-"
        f"{payment.id}-"
        f"{uuid.uuid4()}"

    )


    # ==================================================
    # DEBUG PAYMONGO REQUEST
    # ==================================================

    print()
    print("=" * 70)
    print("PAYMONGO CREATE PAYMENT")
    print("=" * 70)

    print(
        "Participant ID:",
        participant.id
    )

    print(
        "Payment ID:",
        payment.id
    )

    print(
        "Items:",
        selected_items
    )

    print(
        "Amount:",
        amount
    )

    print(
        "Amount Display:",
        f"₱{amount / 100:,.2f}"
    )

    print(
        "URL:",
        url
    )

    print(
        "Payload:"
    )

    print(
        json.dumps(
            payload,
            indent=4
        )
    )

    print("=" * 70)


    # ==================================================
    # SEND REQUEST TO PAYMONGO
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
    # PAYMONGO RESPONSE
    # ==================================================

    print()
    print("=" * 70)

    print(
        "PAYMONGO STATUS:",
        response.status_code
    )

    print(
        "PAYMONGO RESPONSE:"
    )

    print(
        response.text
    )

    print("=" * 70)


    # ==================================================
    # HANDLE PAYMONGO ERROR
    # ==================================================

    if not response.ok:

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
    # PARSE RESPONSE
    # ==================================================

    try:

        paymongo_data = response.json()

    except Exception:

        payment.status = "Failed"

        db.commit()


        raise HTTPException(

            status_code=502,

            detail=(
                "PayMongo returned "
                "an invalid JSON response."
            )

        )


    # ==================================================
    # GET DATA
    # ==================================================

    link_data = paymongo_data.get(
        "data",
        {}
    )


    if not link_data:

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
    # GET LINK ID
    # ==================================================

    paymongo_link_id = (
        link_data.get("id")
    )


    # ==================================================
    # GET ATTRIBUTES
    # ==================================================

    link_attributes = (
        link_data.get(
            "attributes",
            {}
        )
    )


    # ==================================================
    # GET CHECKOUT URL
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
    # GET REFERENCE
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
    # SAVE PAYMONGO INFORMATION
    # ==================================================

    payment.paymongo_link_id = (
        paymongo_link_id
    )

    payment.paymongo_reference = (
        paymongo_reference
    )

    payment.checkout_url = (
        checkout_url
    )

    payment.status = "Pending"


    db.commit()

    db.refresh(payment)


    # ==================================================
    # SUCCESS
    # ==================================================

    print()
    print("=" * 70)
    print("PAYMENT CREATED SUCCESSFULLY")
    print("=" * 70)

    print(
        "Payment ID:",
        payment.id
    )

    print(
        "Participant ID:",
        participant.id
    )

    print(
        "Items:",
        selected_items
    )

    print(
        "Amount:",
        amount
    )

    print(
        "PayMongo Link ID:",
        paymongo_link_id
    )

    print(
        "Checkout URL:",
        checkout_url
    )

    print(
        "Reference:",
        paymongo_reference
    )

    print("=" * 70)


    # ==================================================
    # RETURN
    # ==================================================

    return {

        "message":
            "Payment link created successfully.",

        "payment_id":
            payment.id,

        "participant_id":
            participant.id,

        "registration_number":
            participant.registration_number,

        "items":
            selected_items,

        "tshirt_size":
            tshirt_size,

        "amount":
            amount,

        "amount_display":
            f"₱{amount / 100:,.2f}",

        "currency":
            "PHP",

        "status":
            payment.status,

        "checkout_url":
            checkout_url,

        "paymongo_link_id":
            paymongo_link_id,

        "paymongo_reference":
            paymongo_reference

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


























## ======================================================
# PAYMONGO WEBHOOK
# ======================================================
#
# Handles:
#
# 1. Normal participant payments
# 2. Store payments
# 3. Cash sponsorship payments
# 4. Automatically adds successful cash donations
#    to CashDonationTotal
# 5. Automatically sponsors Finding Sponsor participants
# 6. Automatically emails sponsored participants
#
# IMPORTANT:
# cash_total_added is now INTEGER, not Boolean.
#
# cash_total_added:
#     0   = donation has not been added
#     > 0 = amount added to donation pool in pesos
#
# ======================================================


# ============================================================
# PAYMONGO WEBHOOK
# ============================================================
#
# Handles:
#
# 1. Participant payments
# 2. Store payments
# 3. Cash sponsorship payments
# 4. Cash donation total
# 5. Finding Sponsor queue
#
# Supported PayMongo events:
#
#     link.payment.paid
#     payment.paid
#
# ============================================================


# ======================================================
# PAYMONGO WEBHOOK
# ======================================================
#
# Handles:
#
# 1. Participant payments
# 2. Store payments
# 3. Cash sponsorship payments
# 4. Cash donation total
# 5. Finding Sponsor queue
#
# IMPORTANT:
#
# PayMongo may send:
#
#     link.payment.paid
#
# or:
#
#     payment.paid
#
# For payment.paid, the resource ID is the PayMongo
# PAYMENT ID, not the Payment Link ID.
#
# Cash sponsorship is matched using:
#
#     1. sponsorship_id metadata
#     2. paymongo_reference
#     3. paymongo_link_id
#
# ======================================================


@app.post("/webhooks/paymongo")
async def paymongo_webhook(
    request: Request,
    db: Session = Depends(get_db)
):

    print("\n")
    print("=" * 70)
    print("PAYMONGO WEBHOOK RECEIVED")
    print("=" * 70)

    # ======================================================
    # 1. READ RAW BODY
    # ======================================================

    try:

        raw_body = await request.body()

    except ClientDisconnect:

        print("=" * 70)
        print("PAYMONGO CLIENT DISCONNECTED")
        print("Webhook body could not be completely received.")
        print("=" * 70)

        # There is no safe way to process a partially
        # received webhook body.

        return JSONResponse(
            status_code=400,
            content={
                "received": False,
                "processed": False,
                "message": "Webhook client disconnected."
            }
        )

    except Exception as e:

        print("=" * 70)
        print("ERROR READING WEBHOOK BODY")
        print("Error:", repr(e))
        print("=" * 70)

        return JSONResponse(
            status_code=400,
            content={
                "received": False,
                "processed": False,
                "message": "Unable to read webhook body."
            }
        )

    print(
        "Raw webhook received."
    )

    print(
        "Body length:",
        len(raw_body)
    )

    if not raw_body:

        print(
            "ERROR: Empty webhook body."
        )

        return JSONResponse(
            status_code=400,
            content={
                "received": False,
                "processed": False,
                "message": "Empty webhook body."
            }
        )

    # ======================================================
    # 2. GET SIGNATURE
    # ======================================================

    signature_header = request.headers.get(
        "Paymongo-Signature"
    )

    if not signature_header:

        print(
            "ERROR: Missing Paymongo-Signature."
        )

        return JSONResponse(
            status_code=401,
            content={
                "received": False,
                "processed": False,
                "message": "Missing PayMongo signature."
            }
        )

    print(
        "Paymongo-Signature:",
        signature_header
    )

    # ======================================================
    # 3. VERIFY SIGNATURE
    # ======================================================

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

        timestamp = parts.get(
            "t"
        )

        test_signature = parts.get(
            "te",
            ""
        )

        live_signature = parts.get(
            "li",
            ""
        )

        if not timestamp:

            print(
                "ERROR: Missing webhook timestamp."
            )

            return JSONResponse(
                status_code=401,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Missing webhook timestamp."
                }
            )

        # ==================================================
        # TIMESTAMP VALIDATION
        # ==================================================

        try:

            timestamp_int = int(
                timestamp
            )

        except (
            ValueError,
            TypeError
        ):

            print(
                "ERROR: Invalid webhook timestamp."
            )

            return JSONResponse(
                status_code=401,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Invalid webhook timestamp."
                }
            )

        current_timestamp = int(
            time.time()
        )

        difference = abs(
            current_timestamp -
            timestamp_int
        )

        print(
            "Webhook timestamp difference:",
            difference,
            "seconds"
        )

        if difference > 300:

            print(
                "ERROR: Webhook timestamp expired."
            )

            return JSONResponse(
                status_code=401,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Webhook timestamp expired."
                }
            )

        # ==================================================
        # SIGNED PAYLOAD
        # ==================================================

        signed_payload = (
            f"{timestamp}."
        ).encode(
            "utf-8"
        ) + raw_body

        if not PAYMONGO_WEBHOOK_SECRET:

            print(
                "ERROR: PAYMONGO_WEBHOOK_SECRET "
                "is not configured."
            )

            return JSONResponse(
                status_code=500,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Webhook secret is not configured."
                }
            )

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

            print(
                "ERROR: Missing PayMongo signature value."
            )

            return JSONResponse(
                status_code=401,
                content={
                    "received": False,
                    "processed": False,
                    "message": "Missing PayMongo signature value."
                }
            )

        if not hmac.compare_digest(
            expected_signature,
            provided_signature
        ):

            print(
                "ERROR: Invalid PayMongo webhook signature."
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

        print("=" * 70)
        print(
            "WEBHOOK SIGNATURE VERIFICATION ERROR"
        )

        print(
            "Error:",
            repr(e)
        )

        print("=" * 70)

        return JSONResponse(
            status_code=401,
            content={
                "received": False,
                "processed": False,
                "message": "Invalid PayMongo webhook signature."
            }
        )

    # ======================================================
    # 4. PARSE JSON
    # ======================================================

    try:

        payload = json.loads(
            raw_body.decode(
                "utf-8"
            )
        )

    except Exception as e:

        print("=" * 70)
        print(
            "WEBHOOK JSON PARSE ERROR"
        )

        print(
            "Error:",
            repr(e)
        )

        print("=" * 70)

        return JSONResponse(
            status_code=400,
            content={
                "received": False,
                "processed": False,
                "message": "Invalid JSON payload."
            }
        )

    # ======================================================
    # 5. EVENT DATA
    # ======================================================

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

    print("=" * 70)
    print("PAYMONGO EVENT")

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

    print("=" * 70)

    # ======================================================
    # 6. ONLY PROCESS PAYMENT SUCCESS EVENTS
    # ======================================================

    supported_events = {
        "payment.paid",
        "link.payment.paid"
    }

    if event_type not in supported_events:

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

    # ======================================================
    # 7. RESOURCE
    # ======================================================

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

    # ======================================================
    # 8. METADATA
    # ======================================================

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

    # ======================================================
    # 9. SPONSORSHIP ID
    # ======================================================

    sponsorship_id = (
        metadata.get(
            "sponsorship_id"
        )
    )

    if sponsorship_id:

        sponsorship_id = str(
            sponsorship_id
        ).strip()

    print(
        "Metadata Sponsorship ID:",
        sponsorship_id
    )

    # ======================================================
    # 10. PAYMONGO REFERENCE
    # ======================================================
    #
    # Your actual payment.paid events contain:
    #
    # metadata:
    # {
    #     "pm_reference_number": "JDXaig6"
    # }
    #
    # Therefore this is extremely important.
    #
    # ======================================================

    paymongo_reference = (

        metadata.get(
            "pm_reference_number"
        )

        or

        metadata.get(
            "reference_number"
        )

        or

        resource_attributes.get(
            "external_reference_number"
        )

        or

        resource_attributes.get(
            "reference_number"
        )

    )

    if paymongo_reference:

        paymongo_reference = str(
            paymongo_reference
        ).strip()

    else:

        paymongo_reference = None

    print(
        "PayMongo Reference:",
        paymongo_reference
    )

    # ======================================================
    # 11. PAYMONGO PAYMENT ID
    # ======================================================

    paymongo_payment_id = None

    if event_type == "payment.paid":

        paymongo_payment_id = (
            resource_id
        )

    if not paymongo_payment_id:

        paymongo_payment_id = (
            metadata.get(
                "paymongo_payment_id"
            )
        )

    if paymongo_payment_id:

        paymongo_payment_id = str(
            paymongo_payment_id
        ).strip()

    print(
        "PayMongo Payment ID:",
        paymongo_payment_id
    )

    # ======================================================
    # 12. PAYMONGO LINK ID
    # ======================================================

    paymongo_link_id = None

    if event_type == "link.payment.paid":

        paymongo_link_id = (
            resource_id
        )

    if not paymongo_link_id:

        paymongo_link_id = (
            metadata.get(
                "paymongo_link_id"
            )
        )

    if not paymongo_link_id:

        paymongo_link_id = (
            resource_attributes.get(
                "link_id"
            )
        )

    if paymongo_link_id:

        paymongo_link_id = str(
            paymongo_link_id
        ).strip()

    print(
        "PayMongo Link ID:",
        paymongo_link_id
    )

    # ======================================================
    # 13. PAYMENT AMOUNT
    # ======================================================

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

    print(
        "PayMongo Amount:",
        paymongo_amount,
        "centavos"
    )

    # ======================================================
    # ======================================================
    # CASH SPONSORSHIP
    # ======================================================
    # ======================================================

    cash_sponsorship = None

    # ======================================================
    # 14. FIND CASH SPONSORSHIP BY ID
    # ======================================================

    if sponsorship_id:

        print(
            "Searching CashSponsorship "
            "by Sponsorship ID..."
        )

        try:

            cash_sponsorship = (
                db.query(
                    CashSponsorship
                )
                .filter(
                    CashSponsorship.id ==
                    int(sponsorship_id)
                )
                .first()
            )

        except (
            ValueError,
            TypeError
        ):

            cash_sponsorship = None

    # ======================================================
    # 15. FIND BY PAYMONGO REFERENCE
    # ======================================================
    #
    # THIS IS THE MOST IMPORTANT MATCH FOR YOUR CURRENT
    # PAYMONGO WEBHOOK PAYLOAD.
    #
    # ======================================================

    if (
        not cash_sponsorship
        and
        paymongo_reference
        and
        hasattr(
            CashSponsorship,
            "paymongo_reference"
        )
    ):

        print(
            "Searching CashSponsorship "
            "by PayMongo Reference..."
        )

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

    # ======================================================
    # 16. FIND BY PAYMONGO PAYMENT ID
    # ======================================================

    if (
        not cash_sponsorship
        and
        paymongo_payment_id
        and
        hasattr(
            CashSponsorship,
            "paymongo_payment_id"
        )
    ):

        print(
            "Searching CashSponsorship "
            "by PayMongo Payment ID..."
        )

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

    # ======================================================
    # 17. FIND BY PAYMONGO LINK ID
    # ======================================================

    if (
        not cash_sponsorship
        and
        paymongo_link_id
        and
        hasattr(
            CashSponsorship,
            "paymongo_link_id"
        )
    ):

        print(
            "Searching CashSponsorship "
            "by PayMongo Link ID..."
        )

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

    # ======================================================
    # ======================================================
    # PROCESS CASH SPONSORSHIP
    # ======================================================
    # ======================================================

    if cash_sponsorship:

        print("=" * 70)
        print(
            "CASH SPONSORSHIP FOUND"
        )

        print(
            "Sponsorship ID:",
            cash_sponsorship.id
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

        print("=" * 70)

        # ==================================================
        # 18. SAVE PAYMONGO IDENTIFIERS FIRST
        # ==================================================

        if (
            paymongo_reference
            and
            hasattr(
                cash_sponsorship,
                "paymongo_reference"
            )
        ):

            cash_sponsorship.paymongo_reference = (
                paymongo_reference
            )

        if (
            paymongo_payment_id
            and
            hasattr(
                cash_sponsorship,
                "paymongo_payment_id"
            )
        ):

            cash_sponsorship.paymongo_payment_id = (
                paymongo_payment_id
            )

        if (
            paymongo_link_id
            and
            hasattr(
                cash_sponsorship,
                "paymongo_link_id"
            )
        ):

            cash_sponsorship.paymongo_link_id = (
                paymongo_link_id
            )

        # ==================================================
        # 19. CURRENT STATUS
        # ==================================================

        current_status = str(
            getattr(
                cash_sponsorship,
                "payment_status",
                ""
            )
            or ""
        ).strip().lower()

        print(
            "Current Payment Status:",
            current_status
        )

        # ==================================================
        # 20. IDEMPOTENCY
        # ==================================================
        #
        # If PayMongo sends the same payment.paid event again,
        # DO NOT ADD THE MONEY AGAIN.
        #
        # ==================================================

        if current_status == "paid":

            print("=" * 70)
            print(
                "CASH SPONSORSHIP ALREADY PAID"
            )

            print(
                "No additional donation will be added."
            )

            print("=" * 70)

            db.commit()

            return {

                "received": True,

                "processed": True,

                "already_processed": True,

                "payment_type":
                    "sponsor_package",

                "event_id":
                    event_id,

                "sponsorship_id":
                    cash_sponsorship.id,

                "payment_status":
                    cash_sponsorship.payment_status,

                "cash_total_added":
                    float(
                        getattr(
                            cash_sponsorship,
                            "cash_total_added",
                            0
                        )
                        or 0
                    ),

                "paymongo_reference":
                    getattr(
                        cash_sponsorship,
                        "paymongo_reference",
                        paymongo_reference
                    ),

                "paymongo_payment_id":
                    getattr(
                        cash_sponsorship,
                        "paymongo_payment_id",
                        paymongo_payment_id
                    ),

                "paymongo_link_id":
                    getattr(
                        cash_sponsorship,
                        "paymongo_link_id",
                        paymongo_link_id
                    )
            }

        # ==================================================
        # 21. GET DONATION AMOUNT
        # ==================================================

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

        print(
            "Donation Amount from DB:",
            donation_amount,
            "centavos"
        )

        if donation_amount <= 0:

            db.rollback()

            return {

                "received":
                    True,

                "processed":
                    False,

                "payment_type":
                    "sponsor_package",

                "sponsorship_id":
                    cash_sponsorship.id,

                "message":
                    "Invalid donation amount."
            }

        # ==================================================
        # 22. VERIFY PAYMONGO AMOUNT
        # ==================================================

        if (
            paymongo_amount > 0
            and
            paymongo_amount != donation_amount
        ):

            print("=" * 70)
            print(
                "PAYMENT AMOUNT MISMATCH"
            )

            print(
                "Expected:",
                donation_amount
            )

            print(
                "PayMongo:",
                paymongo_amount
            )

            print("=" * 70)

            db.rollback()

            return {

                "received":
                    True,

                "processed":
                    False,

                "payment_type":
                    "sponsor_package",

                "sponsorship_id":
                    cash_sponsorship.id,

                "message":
                    "Payment amount does not match sponsorship amount."
            }

        # ==================================================
        # 23. CONVERT TO PESOS
        # ==================================================

        donation_amount_pesos = (
            donation_amount / 100
        )

        print(
            "Donation Amount:",
            f"₱{donation_amount_pesos:,.2f}"
        )

        # ==================================================
        # 24. FIND CASH DONATION TOTAL
        # ==================================================

        donation_total = (
            db.query(
                CashDonationTotal
            )
            .order_by(
                CashDonationTotal.id.asc()
            )
            .first()
        )

        # ==================================================
        # 25. CREATE TOTAL IF MISSING
        # ==================================================

        if not donation_total:

            donation_total = CashDonationTotal(
                total_amount=0
            )

            db.add(
                donation_total
            )

            db.flush()

        # ==================================================
        # 26. CURRENT TOTAL
        # ==================================================

        try:

            current_cash_total = float(
                donation_total.total_amount or 0
            )

        except (
            ValueError,
            TypeError
        ):

            current_cash_total = 0.0

        print(
            "Current Cash Donation Total:",
            current_cash_total
        )

        # ==================================================
        # 27. ADD DONATION
        # ==================================================

        new_cash_total = (
            current_cash_total +
            donation_amount_pesos
        )

        print(
            "New Cash Donation Total:",
            new_cash_total
        )

        donation_total.total_amount = (
            new_cash_total
        )

        if hasattr(
            donation_total,
            "updated_at"
        ):

            donation_total.updated_at = (
                datetime.datetime.now()
            )

        # ==================================================
        # 28. MARK CASH SPONSORSHIP PAID
        # ==================================================

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

        # ==================================================
        # 29. SAVE EXACT AMOUNT ADDED
        # ==================================================

        if hasattr(
            cash_sponsorship,
            "cash_total_added"
        ):

            cash_sponsorship.cash_total_added = (
                donation_amount_pesos
            )

        # ==================================================
        # 30. COMMIT IMMEDIATELY
        # ==================================================
        #
        # THIS IS THE IMPORTANT PERFORMANCE CHANGE.
        #
        # The database becomes Paid BEFORE email and
        # finding-sponsor processing.
        #
        # Therefore frontend polling can immediately
        # detect the successful payment.
        #
        # ==================================================

        print("=" * 70)
        print(
            "COMMITTING PAYMENT SUCCESS"
        )
        print("=" * 70)

        try:

            db.commit()

        except Exception as e:

            db.rollback()

            print("=" * 70)
            print(
                "DATABASE COMMIT FAILED"
            )

            print(
                "Error:",
                repr(e)
            )

            print("=" * 70)

            return JSONResponse(
                status_code=500,
                content={
                    "received": True,
                    "processed": False,
                    "payment_type": "sponsor_package",
                    "sponsorship_id": cash_sponsorship.id,
                    "message": "Database update failed."
                }
            )

        db.refresh(
            cash_sponsorship
        )

        db.refresh(
            donation_total
        )

        # ==================================================
        # 31. SAFE VALUES AFTER COMMIT
        # ==================================================

        try:

            saved_cash_total_added = float(
                getattr(
                    cash_sponsorship,
                    "cash_total_added",
                    donation_amount_pesos
                )
                or 0
            )

        except (
            ValueError,
            TypeError
        ):

            saved_cash_total_added = (
                donation_amount_pesos
            )

        try:

            saved_total = float(
                donation_total.total_amount or 0
            )

        except (
            ValueError,
            TypeError
        ):

            saved_total = (
                new_cash_total
            )

        # ==================================================
        # 32. SUCCESS LOG
        # ======================================================

        print("=" * 70)
        print(
            "CASH DONATION SUCCESSFULLY PROCESSED"
        )

        print(
            "Sponsorship ID:",
            cash_sponsorship.id
        )

        print(
            "Payment Status:",
            cash_sponsorship.payment_status
        )

        print(
            "Donation:",
            f"₱{donation_amount_pesos:,.2f}"
        )

        print(
            "Previous Total:",
            f"₱{current_cash_total:,.2f}"
        )

        print(
            "New Total:",
            f"₱{saved_total:,.2f}"
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

        print("=" * 70)

        # ==================================================
        # 33. EMAIL
        # ==================================================
        #
        # The payment is ALREADY committed at this point.
        #
        # If email fails, payment remains Paid.
        #
        # ==================================================

        sponsor_email_sent = False

        sponsor_email = getattr(
            cash_sponsorship,
            "email",
            None
        )

        if sponsor_email:

            try:

                email_function = globals().get(
                    "send_cash_sponsorship_confirmation_email"
                )

                if email_function:

                    await email_function(
                        cash_sponsorship,
                        None
                    )

                    sponsor_email_sent = True

                    print(
                        "Cash sponsorship confirmation email sent."
                    )

            except Exception as e:

                print("=" * 70)
                print(
                    "CASH SPONSORSHIP EMAIL FAILED"
                )

                print(
                    "Error:",
                    repr(e)
                )

                print("=" * 70)

        # ==================================================
        # 34. FINDING SPONSOR QUEUE
        # ==================================================

        queue_result = None
        queue_processed = False

        try:

            queue_function = globals().get(
                "process_finding_sponsor_queue_logic"
            )

            if queue_function:

                queue_result = await queue_function(
                    db
                )

                queue_processed = True

                print("=" * 70)
                print(
                    "FINDING SPONSOR QUEUE PROCESSED"
                )

                print(
                    "Queue Result:",
                    queue_result
                )

                print("=" * 70)

            else:

                queue_result = {
                    "success": False,
                    "message":
                        "Queue processing function is not defined."
                }

        except Exception as e:

            print("=" * 70)
            print(
                "FINDING SPONSOR QUEUE FAILED"
            )

            print(
                "Error:",
                repr(e)
            )

            print("=" * 70)

            queue_result = {

                "success":
                    False,

                "message":
                    "Donation was successful, "
                    "but sponsorship processing failed.",

                "error":
                    str(e)
            }

        # ==================================================
        # 35. FINAL CASH RESPONSE
        # ==================================================

        return {

            "received":
                True,

            "processed":
                True,

            "payment_type":
                "sponsor_package",

            "event_id":
                event_id,

            "sponsorship_id":
                cash_sponsorship.id,

            "payment_status":
                cash_sponsorship.payment_status,

            "donation_amount":
                donation_amount_pesos,

            "donation_amount_display":
                f"₱{donation_amount_pesos:,.2f}",

            "cash_total_added":
                saved_cash_total_added,

            "cash_total_added_display":
                f"₱{saved_cash_total_added:,.2f}",

            "previous_cash_donation_total":
                current_cash_total,

            "previous_cash_donation_total_display":
                f"₱{current_cash_total:,.2f}",

            "cash_donation_total":
                saved_total,

            "cash_donation_total_display":
                f"₱{saved_total:,.2f}",

            "paymongo_link_id":
                getattr(
                    cash_sponsorship,
                    "paymongo_link_id",
                    paymongo_link_id
                ),

            "paymongo_payment_id":
                getattr(
                    cash_sponsorship,
                    "paymongo_payment_id",
                    paymongo_payment_id
                ),

            "paymongo_reference":
                getattr(
                    cash_sponsorship,
                    "paymongo_reference",
                    paymongo_reference
                ),

            "sponsor_email_sent":
                sponsor_email_sent,

            "queue_processed":
                queue_processed,

            "queue_result":
                queue_result
        }

    # ======================================================
    # ======================================================
    # NORMAL PAYMENT
    # ======================================================
    # ======================================================

    payment = None

    # ======================================================
    # 36. FIND NORMAL PAYMENT BY INTERNAL PAYMENT ID
    # ======================================================

    internal_payment_id = metadata.get(
        "payment_id"
    )

    if internal_payment_id:

        internal_payment_id = str(
            internal_payment_id
        ).strip()

        print(
            "Internal Payment ID:",
            internal_payment_id
        )

        try:

            payment = (
                db.query(
                    Payment
                )
                .filter(
                    Payment.id ==
                    int(internal_payment_id)
                )
                .first()
            )

        except (
            ValueError,
            TypeError
        ):

            payment = None

    # ======================================================
    # 37. FIND NORMAL PAYMENT BY REFERENCE
    # ======================================================

    if (
        not payment
        and
        paymongo_reference
        and
        hasattr(
            Payment,
            "paymongo_reference"
        )
    ):

        print(
            "Searching local Payment "
            "by PayMongo Reference..."
        )

        payment = (
            db.query(
                Payment
            )
            .filter(
                Payment.paymongo_reference ==
                paymongo_reference
            )
            .first()
        )

    # ======================================================
    # 38. FIND NORMAL PAYMENT BY PAYMENT ID
    # ======================================================

    if (
        not payment
        and
        paymongo_payment_id
        and
        hasattr(
            Payment,
            "paymongo_payment_id"
        )
    ):

        print(
            "Searching local Payment "
            "by PayMongo Payment ID..."
        )

        payment = (
            db.query(
                Payment
            )
            .filter(
                Payment.paymongo_payment_id ==
                paymongo_payment_id
            )
            .first()
        )

    # ======================================================
    # 39. FIND NORMAL PAYMENT BY LINK ID
    # ======================================================

    if (
        not payment
        and
        paymongo_link_id
        and
        hasattr(
            Payment,
            "paymongo_link_id"
        )
    ):

        print(
            "Searching local Payment "
            "by PayMongo Link ID..."
        )

        payment = (
            db.query(
                Payment
            )
            .filter(
                Payment.paymongo_link_id ==
                paymongo_link_id
            )
            .first()
        )

    # ======================================================
    # 40. NO NORMAL PAYMENT FOUND
    # ======================================================

    if not payment:

        print("=" * 70)
        print(
            "NO MATCHING LOCAL PAYMENT FOUND"
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

        print("=" * 70)

        return {

            "received":
                True,

            "processed":
                False,

            "event_id":
                event_id,

            "paymongo_reference":
                paymongo_reference,

            "paymongo_payment_id":
                paymongo_payment_id,

            "paymongo_link_id":
                paymongo_link_id,

            "message":
                "No matching local payment found."
        }

    # ======================================================
    # 41. NORMAL PAYMENT FOUND
    # ======================================================

    print("=" * 70)
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

    print("=" * 70)

    # ======================================================
    # 42. SAVE PAYMONGO IDENTIFIERS
    # ======================================================

    if (
        paymongo_link_id
        and
        hasattr(
            payment,
            "paymongo_link_id"
        )
    ):

        payment.paymongo_link_id = (
            paymongo_link_id
        )

    if (
        paymongo_payment_id
        and
        hasattr(
            payment,
            "paymongo_payment_id"
        )
    ):

        payment.paymongo_payment_id = (
            paymongo_payment_id
        )

    if (
        paymongo_reference
        and
        hasattr(
            payment,
            "paymongo_reference"
        )
    ):

        payment.paymongo_reference = (
            paymongo_reference
        )

    # ======================================================
    # 43. PAYMENT TYPE
    # ======================================================

    payment_type = str(
        getattr(
            payment,
            "payment_type",
            ""
        )
        or ""
    ).strip().lower()

    # ======================================================
    # 44. PARTICIPANT PAYMENT
    # ======================================================

    if payment_type == "participant":

        participant_id = getattr(
            payment,
            "participant_id",
            None
        )

        if not participant_id:

            db.rollback()

            return {

                "received":
                    True,

                "processed":
                    False,

                "payment_type":
                    "participant",

                "payment_id":
                    payment.id,

                "message":
                    "Participant ID is missing."
            }

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

            db.rollback()

            return {

                "received":
                    True,

                "processed":
                    False,

                "payment_type":
                    "participant",

                "payment_id":
                    payment.id,

                "participant_id":
                    participant_id,

                "message":
                    "Participant not found."
            }

        # ==================================================
        # IDEMPOTENCY
        # ==================================================

        current_status = str(
            getattr(
                payment,
                "status",
                ""
            )
            or ""
        ).strip().lower()

        if current_status == "paid":

            db.commit()

            return {

                "received":
                    True,

                "processed":
                    True,

                "already_processed":
                    True,

                "payment_type":
                    "participant",

                "payment_id":
                    payment.id,

                "participant_id":
                    participant.id,

                "payment_status":
                    payment.status
            }

        # ==================================================
        # MARK PAID
        # ==================================================

        payment.status = "Paid"

        if hasattr(
            payment,
            "paid_at"
        ):

            payment.paid_at = (
                datetime.datetime.now()
            )

        # ==================================================
        # T-SHIRT
        # ==================================================

        if getattr(
            payment,
            "tshirt_selected",
            0
        ):

            if hasattr(
                participant,
                "tshirt_status"
            ):

                participant.tshirt_status = (
                    "Paid"
                )

            tshirt_size = getattr(
                payment,
                "tshirt_size",
                None
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

        # ==================================================
        # LANYARD
        # ==================================================

        if getattr(
            payment,
            "lanyard_selected",
            0
        ):

            if hasattr(
                participant,
                "lanyard_status"
            ):

                participant.lanyard_status = (
                    "Paid"
                )

            if hasattr(
                participant,
                "registration_status"
            ):

                participant.registration_status = (
                    "Confirmed"
                )

        if hasattr(
            participant,
            "updated_at"
        ):

            participant.updated_at = (
                datetime.datetime.now()
            )

        # ==================================================
        # COMMIT
        # ==================================================

        try:

            db.commit()

        except Exception as e:

            db.rollback()

            print(
                "Participant payment commit failed:",
                repr(e)
            )

            return JSONResponse(
                status_code=500,
                content={
                    "received": True,
                    "processed": False,
                    "payment_type": "participant",
                    "payment_id": payment.id,
                    "message": "Database update failed."
                }
            )

        db.refresh(
            payment
        )

        db.refresh(
            participant
        )

        print("=" * 70)
        print(
            "PARTICIPANT PAYMENT SUCCESSFULLY PROCESSED"
        )

        print(
            "Payment ID:",
            payment.id
        )

        print(
            "Participant ID:",
            participant.id
        )

        print("=" * 70)

        return {

            "received":
                True,

            "processed":
                True,

            "payment_type":
                "participant",

            "payment_id":
                payment.id,

            "participant_id":
                participant.id,

            "payment_status":
                payment.status,

            "registration_status":
                getattr(
                    participant,
                    "registration_status",
                    None
                ),

            "paymongo_link_id":
                getattr(
                    payment,
                    "paymongo_link_id",
                    paymongo_link_id
                ),

            "paymongo_payment_id":
                getattr(
                    payment,
                    "paymongo_payment_id",
                    paymongo_payment_id
                ),

            "paymongo_reference":
                getattr(
                    payment,
                    "paymongo_reference",
                    paymongo_reference
                )
        }

    # ======================================================
    # 45. STORE PAYMENT
    # ======================================================

    elif payment_type == "store":

        current_status = str(
            getattr(
                payment,
                "status",
                ""
            )
            or ""
        ).strip().lower()

        if current_status == "paid":

            db.commit()

            return {

                "received":
                    True,

                "processed":
                    True,

                "already_processed":
                    True,

                "payment_type":
                    "store",

                "payment_id":
                    payment.id,

                "payment_status":
                    payment.status
            }

        store_item_id = getattr(
            payment,
            "store_item_id",
            None
        )

        if not store_item_id:

            db.rollback()

            return {

                "received":
                    True,

                "processed":
                    False,

                "payment_type":
                    "store",

                "payment_id":
                    payment.id,

                "message":
                    "Store item ID is missing."
            }

        try:

            store_quantity = int(
                getattr(
                    payment,
                    "store_quantity",
                    1
                )
                or 1
            )

        except (
            ValueError,
            TypeError
        ):

            store_quantity = 1

        if store_quantity <= 0:

            db.rollback()

            return {

                "received":
                    True,

                "processed":
                    False,

                "payment_type":
                    "store",

                "payment_id":
                    payment.id,

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
            .first()
        )

        if not store_item:

            db.rollback()

            return {

                "received":
                    True,

                "processed":
                    False,

                "payment_type":
                    "store",

                "payment_id":
                    payment.id,

                "message":
                    "Store item not found."
            }

        if store_item.quantity < store_quantity:

            db.rollback()

            return {

                "received":
                    True,

                "processed":
                    False,

                "payment_type":
                    "store",

                "payment_id":
                    payment.id,

                "message":
                    "Insufficient inventory."
            }

        # ==================================================
        # MARK PAID
        # ==================================================

        payment.status = "Paid"

        if hasattr(
            payment,
            "paid_at"
        ):

            payment.paid_at = (
                datetime.datetime.now()
            )

        # ==================================================
        # UPDATE INVENTORY
        # ==================================================

        store_item.quantity = (
            store_item.quantity -
            store_quantity
        )

        if hasattr(
            store_item,
            "updated_at"
        ):

            store_item.updated_at = (
                datetime.datetime.now()
            )

        # ==================================================
        # COMMIT
        # ==================================================

        try:

            db.commit()

        except Exception as e:

            db.rollback()

            print(
                "Store payment commit failed:",
                repr(e)
            )

            return JSONResponse(
                status_code=500,
                content={
                    "received": True,
                    "processed": False,
                    "payment_type": "store",
                    "payment_id": payment.id,
                    "message": "Database update failed."
                }
            )

        db.refresh(
            payment
        )

        db.refresh(
            store_item
        )

        print("=" * 70)
        print(
            "STORE PAYMENT SUCCESSFULLY PROCESSED"
        )

        print(
            "Payment ID:",
            payment.id
        )

        print(
            "Item:",
            store_item.item_name
        )

        print(
            "Quantity:",
            store_quantity
        )

        print(
            "Remaining Inventory:",
            store_item.quantity
        )

        print("=" * 70)

        return {

            "received":
                True,

            "processed":
                True,

            "payment_type":
                "store",

            "payment_id":
                payment.id,

            "store_item_id":
                store_item.id,

            "item_name":
                store_item.item_name,

            "quantity":
                store_quantity,

            "size":
                getattr(
                    payment,
                    "store_size",
                    None
                ),

            "remaining_inventory":
                store_item.quantity,

            "payment_status":
                payment.status,

            "paymongo_link_id":
                getattr(
                    payment,
                    "paymongo_link_id",
                    paymongo_link_id
                ),

            "paymongo_payment_id":
                getattr(
                    payment,
                    "paymongo_payment_id",
                    paymongo_payment_id
                ),

            "paymongo_reference":
                getattr(
                    payment,
                    "paymongo_reference",
                    paymongo_reference
                )
        }

    # ======================================================
    # 46. UNKNOWN PAYMENT TYPE
    # ======================================================

    else:

        print("=" * 70)
        print(
            "UNKNOWN PAYMENT TYPE"
        )

        print(
            "Payment Type:",
            payment_type
        )

        print(
            "Payment ID:",
            payment.id
        )

        print("=" * 70)

        db.rollback()

        return {

            "received":
                True,

            "processed":
                False,

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

    payment_id = payment_id.strip()

    print("=" * 70)
    print("CHECKING SPONSORSHIP PAYMENT STATUS")
    print("Requested Payment / Link ID:", payment_id)
    print("=" * 70)

    sponsorship = None

    # ======================================================
    # 1. SEARCH BY PAYMONGO LINK ID
    # ======================================================

    if hasattr(
        CashSponsorship,
        "paymongo_link_id"
    ):

        sponsorship = (
            db.query(CashSponsorship)
            .filter(
                CashSponsorship.paymongo_link_id ==
                payment_id
            )
            .first()
        )

    # ======================================================
    # 2. SEARCH BY PAYMONGO PAYMENT ID
    # ======================================================

    if (
        not sponsorship
        and
        hasattr(
            CashSponsorship,
            "paymongo_payment_id"
        )
    ):

        sponsorship = (
            db.query(CashSponsorship)
            .filter(
                CashSponsorship.paymongo_payment_id ==
                payment_id
            )
            .first()
        )

    # ======================================================
    # 3. SEARCH BY PAYMONGO REFERENCE
    # ======================================================

    if (
        not sponsorship
        and
        hasattr(
            CashSponsorship,
            "paymongo_reference"
        )
    ):

        sponsorship = (
            db.query(CashSponsorship)
            .filter(
                CashSponsorship.paymongo_reference ==
                payment_id
            )
            .first()
        )

    # ======================================================
    # NOT FOUND
    # ======================================================

    if not sponsorship:

        print("=" * 70)
        print("SPONSORSHIP NOT FOUND")
        print(
            "Requested ID:",
            payment_id
        )
        print("=" * 70)

        return {

            "success": True,

            "found": False,

            "paid": False,

            "payment_status":
                "Pending",

            "message":
                "Sponsorship payment not found."

        }

    # ======================================================
    # CURRENT DATABASE STATUS
    # ======================================================

    status = str(
        getattr(
            sponsorship,
            "payment_status",
            "Pending"
        )
        or "Pending"
    ).strip()

    paid = (
        status.lower() == "paid"
    )

    # ======================================================
    # DONATION AMOUNT
    # ======================================================

    try:

        donation_amount_centavos = int(
            getattr(
                sponsorship,
                "donation_amount",
                0
            )
            or 0
        )

    except (
        ValueError,
        TypeError
    ):

        donation_amount_centavos = 0

    donation_amount_pesos = (
        donation_amount_centavos / 100
    )

    # ======================================================
    # CASH TOTAL ADDED
    # ======================================================

    try:

        cash_total_added = float(
            getattr(
                sponsorship,
                "cash_total_added",
                0
            )
            or 0
        )

    except (
        ValueError,
        TypeError
    ):

        cash_total_added = 0.0

    # ======================================================
    # DISPLAY
    # ======================================================

    print("=" * 70)
    print("SPONSORSHIP FOUND")

    print(
        "Sponsorship ID:",
        sponsorship.id
    )

    print(
        "Requested ID:",
        payment_id
    )

    print(
        "PayMongo Link ID:",
        getattr(
            sponsorship,
            "paymongo_link_id",
            None
        )
    )

    print(
        "PayMongo Payment ID:",
        getattr(
            sponsorship,
            "paymongo_payment_id",
            None
        )
    )

    print(
        "PayMongo Reference:",
        getattr(
            sponsorship,
            "paymongo_reference",
            None
        )
    )

    print(
        "Payment Status:",
        status
    )

    print(
        "Paid:",
        paid
    )

    print(
        "Donation Amount:",
        f"₱{donation_amount_pesos:,.2f}"
    )

    print(
        "Cash Total Added:",
        f"₱{cash_total_added:,.2f}"
    )

    print("=" * 70)

    # ======================================================
    # IMPORTANT
    # ======================================================
    #
    # DO NOT call PayMongo here to determine whether
    # the sponsorship is paid.
    #
    # The webhook has already verified payment.paid
    # and updated the database.
    #
    # Database status is the source of truth.
    #
    # ======================================================

    if paid:

        print("=" * 70)
        print("PAYMENT CONFIRMED AS PAID")
        print(
            "Sponsorship ID:",
            sponsorship.id
        )
        print(
            "Cash Total Added:",
            cash_total_added
        )
        print("=" * 70)

    else:

        print("=" * 70)
        print("PAYMENT STILL PENDING")
        print(
            "Sponsorship ID:",
            sponsorship.id
        )
        print(
            "Payment Status:",
            status
        )
        print(
            "Donation Amount:",
            donation_amount_pesos
        )
        print(
            "Cash Total Added:",
            cash_total_added
        )
        print("=" * 70)

    # ======================================================
    # FINAL RESPONSE
    # ======================================================

    return {

        "success":
            True,

        "found":
            True,

        "sponsorship_id":
            sponsorship.id,

        "payment_status":
            status,

        "paid":
            paid,

        "paymongo_link_id":
            getattr(
                sponsorship,
                "paymongo_link_id",
                None
            ),

        "paymongo_payment_id":
            getattr(
                sponsorship,
                "paymongo_payment_id",
                None
            ),

        "paymongo_reference":
            getattr(
                sponsorship,
                "paymongo_reference",
                None
            ),

        "payment_url":
            getattr(
                sponsorship,
                "payment_url",
                None
            ),

        "donation_amount":
            donation_amount_pesos,

        "donation_amount_display":
            f"₱{donation_amount_pesos:,.2f}",

        "cash_total_added":
            cash_total_added,

        "cash_total_added_display":
            f"₱{cash_total_added:,.2f}",

        "cash_donation_total_updated":
            paid and cash_total_added > 0

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
# ============================================================

@app.post("/store/purchase")
def create_store_purchase(
    data: StorePurchaseSchema,
    db: Session = Depends(get_db)
):

    # ========================================================
    # VALIDATE CUSTOMER INFORMATION
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
    # FIND STORE ITEM
    # ========================================================

    item = (
        db.query(StoreItem)
        .filter(
            StoreItem.id == data.store_item_id,
            StoreItem.is_archived == False
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Store item not found."
        )

    # ========================================================
    # NORMALIZE CATEGORY
    # ========================================================

    category = (
        item.category or "others"
    ).strip().lower()

    allowed_categories = {
        "clothes",
        "souvenir",
        "others"
    }

    if category not in allowed_categories:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid store item category. "
                "Allowed categories are: "
                "clothes, souvenir, others."
            )
        )

    # ========================================================
    # CHECK INVENTORY
    # ========================================================

    if item.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="This item is currently out of stock."
        )

    # ========================================================
    # CHECK PURCHASE QUANTITY
    # ========================================================

    if data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be at least 1."
        )

    if data.quantity > item.quantity:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Only {item.quantity} "
                f"item(s) remaining."
            )
        )

    # ========================================================
    # SIZE VALIDATION
    #
    # CLOTHES REQUIRE A SIZE.
    #
    # Default:
    # S
    # M
    # L
    # XL
    # 2XL
    # ========================================================

    selected_size = None

    if category == "clothes":

        if not data.size:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Please select a size "
                    "for this clothing item."
                )
            )

        selected_size = (
            str(data.size)
            .strip()
            .upper()
        )

        default_clothing_sizes = [
            "S",
            "M",
            "L",
            "XL",
            "2XL"
        ]

        available_sizes = []

        # ----------------------------------------------------
        # READ SIZES FROM DATABASE
        # ----------------------------------------------------

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
                        "The clothing item's "
                        "size configuration is invalid."
                    )
                )

        # ----------------------------------------------------
        # USE DEFAULT SIZES IF NONE SAVED
        # ----------------------------------------------------

        if not available_sizes:

            available_sizes = (
                default_clothing_sizes
            )

        # ----------------------------------------------------
        # CHECK SELECTED SIZE
        # ----------------------------------------------------

        if selected_size not in available_sizes:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid size '{selected_size}'. "
                    f"Available sizes: "
                    f"{', '.join(available_sizes)}."
                )
            )

    else:

        # Non-clothing items do not use sizes.
        selected_size = None

    # ========================================================
    # CALCULATE TOTAL
    # ========================================================

    total_php = (
        float(item.price) *
        int(data.quantity)
    )

    if total_php <= 0:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment amount."
        )

    # ========================================================
    # PAYMONGO AMOUNT
    #
    # Example:
    #
    # ₱350.00
    #
    # becomes:
    #
    # 35000 centavos
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
    # PAYMENT DESCRIPTION
    # ========================================================

    if selected_size:

        payment_description = (
            f"{item.item_name} "
            f"x {data.quantity} "
            f"({selected_size})"
        )

    else:

        payment_description = (
            f"{item.item_name} "
            f"x {data.quantity}"
        )

    # ========================================================
    # CREATE PAYMENT RECORD
    #
    # Store customers are NOT participants.
    #
    # participant_id = None
    # ========================================================

    payment = Payment(

    # ==================================================
    # STORE PAYMENT
    # ==================================================

    participant_id=None,

    payment_type="Store",

    # ==================================================
    # STORE PURCHASE INFORMATION
    # ==================================================

    store_item_id=item.id,

    store_quantity=data.quantity,

    store_size=selected_size,

    # Keep this field too for compatibility with
    # existing participant/t-shirt logic.
    tshirt_size=selected_size,

    # ==================================================
    # PAYMENT
    # ==================================================

    amount=paymongo_amount,

    currency="PHP",

    status="Pending",

    description=payment_description,

    # ==================================================
    # CUSTOMER
    # ==================================================

    customer_name=customer_name,

    customer_contact=customer_contact,

    customer_email=customer_email
)
    db.add(payment)

    db.commit()

    db.refresh(payment)

    # ========================================================
    # PAYMONGO CONFIG
    # ========================================================

    secret_key = PAYMONGO_SECRET_KEY

    if not secret_key:

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
    # PAYMONGO PAYMENT LINK
    #
    # IMPORTANT:
    #
    # DO NOT USE:
    #
    # {
    #     "data": {
    #         "attributes": {
    #             ...
    #         }
    #     }
    # }
    #
    # amount, currency and description are sent
    # directly in the request body.
    # ========================================================

    payload = {

        "amount":
            paymongo_amount,

        "currency":
            "PHP",

        "description":
            payment_description,

        "remarks":
            (
                f"Store purchase "
                f"#{payment.id}"
            ),

        "metadata": {

            "type":
                "store_purchase",

            "payment_id":
                str(payment.id),

            "store_item_id":
                str(item.id),

            "item_name":
                item.item_name,

            "category":
                category,

            "quantity":
                str(data.quantity),

            "size":
                selected_size or "",

            "customer_name":
                customer_name,

            "customer_contact":
                customer_contact,

            "customer_email":
                customer_email
        }
    }

    # ========================================================
    # SEND PAYMENT LINK TO PAYMONGO
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

                "Idempotency-Key":
                    (
                        f"store-payment-"
                        f"{payment.id}-"
                        f"{uuid.uuid4()}"
                    )
            },

            json=payload,

            timeout=30
        )

    except Exception as e:

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

        db.delete(payment)

        db.commit()

        raise HTTPException(

            status_code=502,

            detail={
                "message":
                    "PayMongo rejected "
                    "the payment.",

                "paymongo":
                    error_data
            }
        )

    # ========================================================
    # READ PAYMONGO RESPONSE
    # ========================================================

    try:

        result = response.json()

    except Exception as exc:

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
    # GET PAYMENT DATA
    # ========================================================

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

    # ========================================================
    # PAYMENT URL
    #
    # The URL can be returned directly.
    # ========================================================

    payment_url = (
        payment_data.get(
            "url"
        )
    )

    reference_number = (
        payment_data.get(
            "reference_number"
        )
    )

    # ========================================================
    # CHECK PAYMENT LINK ID
    # ========================================================

    if not payment_link_id:

        db.delete(payment)

        db.commit()

        raise HTTPException(

            status_code=502,

            detail=(
                "PayMongo did not return "
                "a payment link ID."
            )
        )

    # ========================================================
    # CHECK PAYMENT URL
    # ========================================================

    if not payment_url:

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
    # ========================================================

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

    payment.tshirt_size = (
        selected_size
    )

    db.commit()

    db.refresh(payment)

    # ========================================================
    # IMPORTANT
    #
    # DO NOT REDUCE INVENTORY HERE.
    #
    # Inventory is reduced ONLY after the
    # PayMongo webhook confirms successful payment.
    # ========================================================

    return {

        "success":
            True,

        "message":
            "Payment created successfully.",

        "payment_id":
            payment.id,

        "store_item_id":
            item.id,

        "item_name":
            item.item_name,

        "category":
            category,

        "quantity":
            data.quantity,

        "size":
            selected_size,

        "unit_price":
            float(item.price),

        "total_amount":
            float(total_php),

        "checkout_url":
            payment_url,

        "payment_status":
            "Pending"
    }
    


# ============================================================
# CHECK STORE PURCHASE PAYMENT STATUS
# ============================================================

@app.get("/store/purchase/status/{payment_id}")
def get_store_purchase_status(
    payment_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # FIND PAYMENT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # RETURN PAYMENT STATUS
    # --------------------------------------------------------

    status = (
        payment.status or "Pending"
    ).strip()

    return {

        "success": True,

        "payment_id":
            payment.id,

        "payment_type":
            payment.payment_type,

        "status":
            status,

        "payment_status":
            status,

        "customer_name":
            payment.customer_name,

        "customer_contact":
            payment.customer_contact,

        "customer_email":
            payment.customer_email,

        "description":
            payment.description,

        "checkout_url":
            payment.checkout_url,

        "paymongo_reference":
            payment.paymongo_reference,

        "size":
            payment.tshirt_size,

        "paid_at":
            payment.paid_at
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


    except smtplib.SMTPAuthenticationError:

        print(
            "CONTACT EMAIL ERROR: Gmail authentication failed."
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to send your message because "
                "the email service authentication failed."
            )
        )


    except smtplib.SMTPException as error:

        print(
            "CONTACT EMAIL SMTP ERROR:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to send your message. "
                "Please try again later."
            )
        )


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
        


# =========================================================
# STORE IMAGE UPLOAD
# =========================================================

STORE_UPLOAD_DIR = Path("uploads/store")

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
    
