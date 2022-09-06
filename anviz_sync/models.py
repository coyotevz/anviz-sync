# -*- coding=utf-8 -*-

from anviz_sync.saw import SQLAlchemy

db = SQLAlchemy()


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_record"

    id = db.Column(db.Integer, primary_key=True)
    user_code = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, unique=True)
    bkp_type = db.Column(db.Integer, nullable=False)
    type_code = db.Column(db.Integer, nullable=False)
    received = db.Column(db.DateTime)
    device = db.Column(db.String)


def configure_db(db_uri):
    db.configure(db_uri)
