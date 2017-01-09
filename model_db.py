from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, Integer, DATETIME, VARCHAR, BOOLEAN, TEXT
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

engine = create_engine('mysql+mysqlconnector://root:@localhost/blog', echo=True)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column('used_id', Integer, primary_key=True)
    username = Column('username', VARCHAR(20), unique=True, index=True)
    password = Column('password', VARCHAR(250))
    email = Column('email', VARCHAR(50), unique=True, index=True)
    registred_on = Column('registred_on', DATETIME)
    confirmed = Column('confirmed', BOOLEAN, nullable=False, default=False)
    confirmed_on = Column('confirmed_on', DATETIME, nullable=True)
    posts = relationship('Post', backref=backref('users'), lazy='dynamic')

    def __init__(self, username, password, email, confirmed, confirmed_on=None):
        self.username = username
        self.set_password(password)
        self.email = email
        self.registred_on = datetime.utcnow()
        self.confirmed = confirmed
        self.confirmed_on = confirmed_on

    def set_password(self, password):
            self.password = generate_password_hash(password)

    def check_password(self, password):
            return check_password_hash(self.password, password)

    def is_authenticated(self):
            return True

    def is_active(self):
            return False

    def get_id(self):
            return self.id

    def __repr__(self):
        return '<User %r' % self.username


class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True)
    title = Column(VARCHAR(25), nullable=False)
    body = Column(TEXT, nullable=False)
    file = Column(VARCHAR(250), nullable=False)
    created = Column(DATETIME)
    user_id = Column(Integer, ForeignKey('users.used_id'))

    def __init__(self, title, body, file, user_id):
        self.title = title
        self.body = body
        self.file = file
        self.created = datetime.utcnow()
        self.user_id = user_id

    def __repr__(self):
        return '<post %r>' % self.title

Base.metadata.create_all(engine)
