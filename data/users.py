import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    recording_time = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    recording_date = sqlalchemy.Column(sqlalchemy.String, nullable=True)
