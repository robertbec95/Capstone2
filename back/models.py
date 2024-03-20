import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from werkzeug.security import generate_password_hash
from flask_sqlalchemy import SQLAlchemy

Base = declarative_base()
db = SQLAlchemy()
class User(Base):
    __tablename__ = 'users'
    ID = Column(Integer, primary_key=True)
    USERNAME = Column(String, unique=True, nullable=False)
    PASSWORD = Column(String, nullable=False)
    FUNDS = Column(Float, default=1000000)
    PORTFOLIO = relationship('Portfolio', back_populates='user')

class Portfolio(Base):
    __tablename__ = 'portfolio'
    ID = Column(Integer, primary_key=True)
    USER_ID = Column(Integer, ForeignKey('users.id'))
    STOCK = Column(String, nullable=False)
    QUANTITY = Column(Integer, nullable=False)
    USER = relationship('User', back_populates='portfolio')

def db_init(app):
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    Base.metadata.create_all(engine)
    app.config['db_session'] = sessionmaker(bind=engine)

def db_session_create(app):
    return app.config['db_session']()

def db_session_commit(session):
    """Commit the current transaction."""
    try:
        session.commit()
    except Exception as e:
        session.rollback()  # Roll back the transaction on error
        raise e

def db_session_rollback(session):
    """Roll back the current transaction."""
    session.rollback()

def db_session_close(session):
    """Close the current session."""
    session.close()

def db_transaction(func):
    """Decorator to handle session transactions."""
    def wrapper(session, *args, **kwargs):
        try:
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
    return wrapper

@db_transaction
def db_user_add_funds(session, username, amount):
    user = session.query(User).filter_by(username=username).first()
    if user:
        user.funds += amount
    else:
        raise ValueError("User not found")

@db_transaction
def db_user_remove_funds(session, username, amount):
    user = session.query(User).filter_by(username=username).first()
    if user and user.funds >= amount:
        user.funds -= amount
    else:
        raise ValueError("Insufficient funds or user not found")

@db_transaction
def db_user_add_stock(session, username, stock, quantity):
    user = session.query(User).filter_by(username=username).first()
    if user:
        portfolio = Portfolio(user=user, stock=stock, quantity=quantity)
        user.portfolio.append(portfolio)
    else:
        raise ValueError("User not found")

@db_transaction
def db_user_remove_stock(session, username, stock, quantity):
    user = session.query(User).filter_by(username=username).first()
    if user:
        for port in user.portfolio:
            if port.stock == stock and quantity <= port.quantity:
                port.quantity -= quantity
                return True
        raise ValueError("Stock not found in portfolio or insufficient quantity")
    else:
        raise ValueError("User not found")


def db_session_close(session):
    session.close()