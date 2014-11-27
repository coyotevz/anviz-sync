"""
    anviz-sync
    ~~~~~~~~~~

    Software that read Anviz A300 device and sync data with db.

    :copyright: (c) 2014 by Augusto Roccasalva.
    :license: BSD, see LICENSE for more details.
"""
from configparser import ConfigParser

from anviz_sync.saw import SQLAlchemy
from anviz_sync.anviz import Device
from anviz_sync.progress import ProgressBar, ProgressDummy

db = SQLAlchemy()

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_record'

    id = db.Column(db.Integer, primary_key=True)
    user_code = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, unique=True)
    bkp_type = db.Column(db.Integer, nullable=False)
    type_code = db.Column(db.Integer, nullable=False)


def sync(progress=False, force_all=False):
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
    count = AttendanceRecord.query.count()
    if count == 0 or force_all:
        only_new = False
    else:
        only_new = True

    if progress:
        total = getattr(clock.get_record_info(),
                        'new_records' if only_new else 'all_records')
        pbar = ProgressBar("sync [{}]".format(ip_addr), total)
    else:
        pbar = ProgressDummy()

    act_name = ('new' if only_new else 'all') + ' records'
    act_col = 'green' if only_new else 'red'

    pbar.set_activity(act_name, act_col)
    pbar.step(0)

    for record in clock.download_records(only_new):
        user_record = AttendanceRecord(
                user_code=record.code,
                datetime=record.datetime,
                bkp_type=record.bkp,
                type_code=record.type
        )

        # check that record don't exist in db
        count = AttendanceRecord.query.filter(AttendanceRecord.user_code==record.code)\
                                .filter(AttendanceRecord.datetime==record.datetime)\
                                .count()
        if count == 0:
            # store
            db.add(user_record)
        else:
            # discard
            pass
        pbar.step()

    db.commit()
    pbar.finish('synced')


def main():
    import sys
    progress = '--no-progress' not in sys.argv
    force_all = '--all' in sys.argv
    sync(progress=progress, force_all=force_all)


if __name__ == '__main__':
    main()
