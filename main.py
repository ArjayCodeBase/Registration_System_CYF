from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Date,
    DateTime
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


# ======================================================
# APP CONFIGURATION
# ======================================================

app = FastAPI(
    title="Event Registration System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    # ======================================================
    # PARTICIPANT INFORMATION
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


    
Base.metadata.create_all(bind=engine)
































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

    event_id:int

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


class ParticipantUpdateSchema(BaseModel):

    event_id:int

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
# EVENT RULES SCHEMA
# ======================================================

class EventRulesAgreementSchema(BaseModel):

    participant_id: int

    agreed: bool




















    

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
# STARTUP
# ======================================================

@app.on_event("startup")
def startup_event():

    Base.metadata.create_all(bind=engine)

    create_default_admin()

    print("=" * 50)
    print("Event Registration System")
    print("SQLite Database Ready")
    print("Default Admin Ready")
    print("=" * 50)
    
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
    # CHECK REGISTRATION PERIOD
    # ======================================================

    today = datetime.date.today()

    if today < event.registration_start:

        raise HTTPException(

            status_code=400,

            detail="Event registration has not started yet."

        )

    # Optional:
    # Prevent registration after the event has started.
    # Walk-in participants can still register after
    # registration_end but before kickoff_date.

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

    db.add(participant)

    db.commit()

    db.refresh(participant)

    return {

        "message": "Participant registered successfully.",

        "participant": {

            "participant_id": participant.id,

            "registration_number": participant.registration_number,

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

    keyword = keyword.lower()

    for participant in participants:

        fullname = f"{participant.fname} {participant.mname} {participant.lname}".lower()

        if (

            keyword in fullname

            or keyword in participant.registration_number.lower()

            or keyword in participant.email.lower()

            or keyword in participant.contact_number.lower()

        ):

            evaluation = db.query(ParticipantEvaluation).filter(

                ParticipantEvaluation.participant_id == participant.id

            ).first()

            result.append({

                "participant_id": participant.id,

                "registration_number": participant.registration_number,

                "fullname": f"{participant.fname} {participant.mname} {participant.lname}",

                "event_name": participant.event_name,

                "registration_phase": participant.registration_phase,

                "registration_status": participant.registration_status,

                "participant_tier": evaluation.participant_tier if evaluation else None

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
    # DUPLICATE VALIDATION
    # ======================================================

    duplicate = db.query(Participant).filter(

        Participant.event_id == participant.event_id,

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

    participant.updated_at = datetime.datetime.now()

    db.commit()

    db.refresh(participant)

    return {

        "message": "Participant updated successfully.",

        "participant": {

            "participant_id": participant.id,

            "registration_number": participant.registration_number,

            "registration_age": participant.registration_age,

            "registration_status": participant.registration_status

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
# Complete Registration Validation
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

        "message": "Registration completed successfully.",

        "participant": {

            "participant_id": participant.id,

            "registration_number": participant.registration_number,

            "fullname": f"{participant.fname} {participant.mname} {participant.lname}".replace("  ", " ").strip(),

            "registration_age": participant.registration_age,

            "registration_date": participant.registration_date,

            "registration_phase": participant.registration_phase,

            "registration_status": participant.registration_status

        },

        "event": {

            "event_id": event.id,

            "event_name": event.event_name,

            "registration_start": event.registration_start,

            "registration_end": event.registration_end,

            "kickoff_date": event.kickoff_date,

            "wrapup_date": event.wrapup_date

        },

        "evaluation": {

            "influence_score": evaluation.influence_score,

            "spiritual_score": evaluation.spiritual_score,

            "creative_status": evaluation.creative_status,

            "participant_tier": evaluation.participant_tier

        },

        "completed_at": participant.updated_at

    }
    
    
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
