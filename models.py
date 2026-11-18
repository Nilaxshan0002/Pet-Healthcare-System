from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='owner')  # owner / vet / admin
    pets = db.relationship('Pet', backref='owner_user', lazy=True)


class Vet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    specialty = db.Column(db.String(80))
    phone = db.Column(db.String(20))
    available = db.Column(db.Boolean, default=True)


class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    species = db.Column(db.String(30))
    breed = db.Column(db.String(50))
    age = db.Column(db.Integer)
    owner = db.Column(db.String(80))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    appointments = db.relationship('Appointment', backref='pet', lazy=True,
                                   cascade='all, delete-orphan')
    records = db.relationship('MedicalRecord', backref='pet', lazy=True,
                              cascade='all, delete-orphan')


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    vet_id = db.Column(db.Integer, db.ForeignKey('vet.id'))
    date = db.Column(db.String(20))
    time = db.Column(db.String(10))
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default='Pending')  # Pending / Confirmed / Done / Cancelled
    vet = db.relationship('Vet')


class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    date = db.Column(db.String(20))
    diagnosis = db.Column(db.String(200))
    treatment = db.Column(db.Text)
    vet_name = db.Column(db.String(80))