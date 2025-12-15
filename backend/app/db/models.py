from sqlalchemy import Column, Integer, String, Float, Text, JSON
from app.db.database import Base

# SQLAlchemy ORM model for Product
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    price = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    features = Column(JSON, nullable=True)   # JSON array of features
    image_url = Column(String, nullable=True)
    category = Column(String(100), nullable=True)
    source_url = Column(String, nullable=True)