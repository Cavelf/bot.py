import sqlalchemy as sq
import psycopg2
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from config import login, password
#from config import login, password, host

login = os.getenv('login')
kod = os.getenv('kod')
engine = sq.create_engine(f'postgresql+psycopg2://postgres: 7811@localhost:5432/vkinder')
#engine = sq.create_engine(f'postgresql+psycopg2://{login}:{password}@{host}/vkinder', client_encoding='utf8')

Session = sessionmaker(bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = 'User'

    dating_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    age_from = sq.Column(sq.Integer)
    age_to = sq.Column(sq.Integer)
    city = sq.Column(sq.String)
    partners_sex = sq.Column(sq.Integer)
    matchingusers = relationship('MatchingUser', backref='User')
    blacklistedusers = relationship('BlacklistedUser', backref='User')


class MatchingUser(Base):
    __tablename__ = 'MatchingUser'

    matching_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    id_dater = sq.Column(sq.Integer, sq.ForeignKey('User.dating_id'))
    photos = relationship('Photos', backref='MatchingUser')
    sex = sq.Column(sq.Integer)


class Photos(Base):
    __tablename__ = 'Photos'

    photo_id = sq.Column(sq.Integer, primary_key=True)
    id_matcher = sq.Column(sq.Integer, sq.ForeignKey('MatchingUser.matching_id'))
    photo_link = sq.Column(sq.String)
    likes_count = sq.Column(sq.Integer)


class BlacklistedUser(Base):
    __tablename__ = 'BlacklistedUser'

    blacklisted_id = sq.Column(sq.Integer, primary_key=True)
    first_name = sq.Column(sq.String)
    last_name = sq.Column(sq.String)
    id_dater = sq.Column(sq.Integer, sq.ForeignKey('User.dating_id'))


Base.metadata.create_all(engine)
