from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Create the base class
Base = declarative_base()

class Customer(Base):
    """Customers table model"""
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)

    # Relationships - ADD cascade="all, delete-orphan"
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")

class Item(Base):
    """Items table model"""
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    cost_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)

    # Relationships - ADD cascade="all, delete-orphan"
    order_items = relationship("OrderItem", back_populates="item", cascade="all, delete-orphan")

class Order(Base):
    """Orders table model"""
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default="Pending")

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    """Order items table model"""
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)  # Actual selling price at time of order

    # Relationships
    order = relationship("Order", back_populates="order_items")
    item = relationship("Item", back_populates="order_items")

class Transaction(Base):
    """Transactions table model"""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bill_no = Column(String(50), unique=True, nullable=False) # This is a String
    date = Column(DateTime, default=datetime.utcnow)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    party_name = Column(String(100), nullable=False)
    address = Column(Text, nullable=False)
    mode = Column(String(20), nullable=False)  # e.g., 'Cash', 'Credit', 'Cheque'
    cheque_no = Column(String(50))
    dsr_no = Column(String(50))
    issue_amount = Column(Float, nullable=False)
    received = Column(Float, nullable=False)
    balance = Column(Float, nullable=False)

    # Relationships
    customer = relationship("Customer", back_populates="transactions")

class User(Base):
    """Users table model for authentication"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False) # Store hashed passwords

# Database connection and session management
class Database:
    def __init__(self, db_url='sqlite:///inventory.db'):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(self.engine)
        print("All tables created successfully!")

    def get_session(self):
        """Return a new database session"""
        return self.Session()

# Example usage (this part is for testing database.py standalone, not part of Streamlit app)
if __name__ == "__main__":
    db = Database()
    db.create_tables()

    # Test connection
    session = db.get_session()
    print("Database connection successful!")
    session.close()