from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    category = Column(String(100))
    cost_price = Column(Float, nullable=False)
    amazon_price = Column(Float)
    flipkart_price = Column(Float)
    amazon_listing_id = Column(String(50))
    flipkart_listing_id = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    inventory = relationship("Inventory", back_populates="product", uselist=False)
    orders = relationship("Order", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    competitors = relationship("Competitor", back_populates="product")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    stock_qty = Column(Integer, default=0)
    reorder_threshold = Column(Integer, default=10)
    last_updated = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="inventory")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    platform = Column(String(20), nullable=False)  # amazon / flipkart
    quantity = Column(Integer, default=1)
    sale_price = Column(Float, nullable=False)
    order_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="delivered")  # delivered, returned, cancelled
    customer_state = Column(String(50))

    product = relationship("Product", back_populates="orders")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    platform = Column(String(20))
    rating = Column(Integer)  # 1-5
    review_text = Column(Text)
    reviewer_name = Column(String(100))
    review_date = Column(DateTime)
    responded = Column(Boolean, default=False)
    response_text = Column(Text)

    product = relationship("Product", back_populates="reviews")


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    competitor_name = Column(String(100))
    platform = Column(String(20))
    price = Column(Float)
    snapshot_date = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="competitors")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    type = Column(String(50))  # low_stock, price_drop, negative_review
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    message = Column(Text)
    severity = Column(String(20))  # low, medium, high, urgent
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
