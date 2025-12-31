from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class BackCheck(Base):
    __tablename__ = 'back_checks'
    id = Column(Integer, primary_key=True)
    checker_name = Column(String)
    fenced = Column(String)
    # Guava
    guava_beds = Column(Integer)
    guava_length = Column(Float)
    guava_sockets = Column(Integer)
    # Lemon
    lemon_beds = Column(Integer)
    lemon_length = Column(Float)
    lemon_sockets = Column(Integer)
    # Gesho
    gesho_beds = Column(Integer)
    gesho_length = Column(Float)
    gesho_sockets = Column(Integer)
    # Grevillea
    grevillea_beds = Column(Integer)
    grevillea_length = Column(Float)
    grevillea_sockets = Column(Integer)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
