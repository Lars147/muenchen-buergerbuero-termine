import datetime
import os

from constants import Office, Services
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class WebPushSubscription(Base):
    __tablename__ = "webpush_subscriptions"
    id = Column(Integer, primary_key=True)
    endpoint = Column(Text, unique=True, nullable=False, index=True)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    services = Column(String, nullable=False)  # Comma-separated service IDs
    offices = Column(String, nullable=False)  # Comma-separated office IDs
    datetimes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(
        DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now
    )


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    location = Column(
        String(100), nullable=False
    )  # Keep location as string (Office name)
    office_id = Column(Integer, nullable=False)  # Office ID
    service_id = Column(Integer, nullable=False)  # Service ID
    date = Column(DateTime, nullable=False)
    fetched_at = Column(DateTime, default=datetime.datetime.now)

    __table_args__ = (
        UniqueConstraint(
            "location", "office_id", "service_id", "date", name="uix_appointment"
        ),
    )

    def get_service_name(self) -> str:
        return Services(self.service_id).name

    def get_office_name(self) -> str | None:
        for office in Office:
            if office.value[1] == self.office_id:
                return office.name


base_dir = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = f"sqlite:///{os.path.join(base_dir, 'database.db')}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
