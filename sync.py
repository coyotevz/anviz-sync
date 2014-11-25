"""
    anviz-sync
    ~~~~~~~~~~

    Software that read Anviz A300 device and sync data with db.
"""
from saw import SQLAlchemy
from anviz import Device
from configparser import ConfigParser

db = SQLAlchemy()

class UserRecord(db.Model):
    __tablename__ = 'user_record'

    id = db.Column(db.Integer, primary_key=True)
    user_code = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, unique=True)
    bkp_type = db.Column(db.Integer, nullable=False)
    type_code = db.Column(db.Integer, nullable=False)


def sync(progress=False):
    config = ConfigParser()
    config.read('anviz-sync.ini')

    # config device
    dev_id = config.getint('anviz', 'device_id')
    ip_addr = config.get('anviz', 'ip_addr')
    ip_port = config.getint('anviz', 'ip_port')
    clock = Device(dev_id, ip_addr, ip_port)

    # config db
    db_uri = config.get('sqlalchemy', 'uri')
    db.configure(db_uri)
    db.create_all()

    # Check stored db
    count = UserRecord.query.count()
    if count == 0:
        only_new = False
    else:
        only_new = True

    for record in clock.download_records(only_new):
        user_record = UserRecord(
                user_code=record.code,
                datetime=record.datetime,
                bkp_type=record.bkp,
                type_code=record.type
        )

        # check that record don't exist in db
        count = UserRecord.query.filter(UserRecord.user_code==record.code)\
                                .filter(UserRecord.datetime==record.datetime)\
                                .count()
        if count == 0:
            # store
            db.add(user_record)
        else:
            # discard
            pass

    db.commit()

if __name__ == '__main__':
    sync(progress=True)
