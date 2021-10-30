import os.path

import peewee as pw

db = pw.SqliteDatabase(
    os.path.join(os.path.dirname(__file__), 'msg.db')
)


class Msg(pw.Model):
    id = pw.IntegerField()
    message = pw.TextField()
    qgroup = pw.IntegerField(default=0)  # 0 for none and 1 for all
    qid = pw.IntegerField(default=0)
    create_time = pw.TimestampField()

    class Meta:
        database = db
        primary_key = pw.CompositeKey('id')


def init():
    if not os.path.exists(os.path.join(os.path.dirname(__file__), 'msg.db')):
        db.connect()
        db.create_tables([Msg])
        db.close()


init()
