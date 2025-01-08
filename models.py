from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import validates

from app import db

class Bikes(db.Model):
    __tablename__ = "bikes"
    bike = Column("bike", String, primary_key=True, autoincrement=True)
    km_stand = Column("km_stand", Integer)
    rel_fahrten = relationship('Fahrten', back_populates='rel_bikes')
    rel_wartung = relationship('Wartung', back_populates='rel_bikes')
    def __init__(self, bike, km_stand, rel_fahrten, rel_wartung):
        self.bike = bike
        self.km_stand = km_stand
        self.rel_fahrten = rel_fahrten
        self.rel_wartung = rel_fahrten
    def __repr__(self):
        return f"({self.bike} {self.km_stand} {self.rel_fahrten}{self.rel_wartung})"

class Fahrten(db.Model):
    __tablename__ = "fahrten"
    fahrt_id = Column("fahrt_id", Integer, primary_key=True,  autoincrement=True)
    bike = Column("bike", String, ForeignKey(Bikes.bike))
    datum = Column("datum", DATETIME)
    strecke = Column("strecke", Integer)
    wetter = Column("wetter", String)
    strava_id = Column("strava_id", String)
    rel_bikes = relationship('Bikes', back_populates='rel_fahrten')
    def __init__(self, bike, datum, strecke, wetter, strava_id, rel_bikes):
        self.bike = bike
        self.datum = datum
        self.strecke = strecke
        self.wetter = wetter
        self.strava_id = strava_id
        self.rel_bikes = rel_bikes 
    def __repr__(self):
        return f"( {self.bike} {self.datum} {self.strecke} {self.wetter} {self.strava_id}{self.rel_bikes})" 


class Wartung(db.Model):
    __tablename__="wartung"
    wartung_id = Column("wartung_id", Integer, primary_key=True ,autoincrement=True)
    datum = Column("datum", DATETIME)
    bike = Column("bike", String, ForeignKey(Bikes.bike))
    service = Column("service", String)
    notes = Column("notes", String)
    rel_bikes = relationship('Bikes', back_populates='rel_wartung')
    def __init__(self, datum, bike, service, notes, rel_bikes):
        self.datum = datum
        self.bike = bike
        self.service = service
        self.notes = notes
        self.rel_bikes = rel_bikes
    def __repr__(self):
        return f"( {self.datum} {self.bike} {self.service} {self.notes}{self.rel_bikes})"
        

class Wetter(db.Model):
    __tablename__="wetter"
    bedingung = Column("bedingung", String, primary_key=True)
    faktor = Column("faktor", Integer)
    def __init__(self, bedingung, faktor):
        self.bedingung
        self.faktor
    def __repr__(self):
        return f"({self.bedingung} {self.faktor})"