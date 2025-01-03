from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, String, Column, Float, DateTime, Integer
from typing import List
from datetime import datetime, timezone
from marshmallow import ValidationError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:%40Soccer90@localhost/ecommerce_api'

#Create  Base Class
class Base(DeclarativeBase):
    pass

#Initialize extensions
db = SQLAlchemy(model_class=Base)
db.init_app
ma = Marshmallow(app)

#The association table between Users and Orders
order_product = Table(
	"order_product",
	Base.metadata,	
	Column("order_id", ForeignKey("order.id")),
    Column("product_id", ForeignKey("product.id")),
)
user_order = Table(
	"user_order",
	Base.metadata,	
	Column("order_id", ForeignKey("order.id")),
    Column("user_id", ForeignKey("user.id")),
)
class Order(Base):
    __tablename__ = "order"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    users: Mapped[List["User"]] = relationship(secondary=user_order, back_populates="order")
    products: Mapped[List["Product"]] = relationship(secondary=order_product, back_populates="order")

class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200))
    price: Mapped[Float] = mapped_column(Float, nullable=False)
    orders : Mapped[List["Order"]] = relationship(secondary=order_product, back_populates="product")

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))

#One-to-Many relationship from this User to a List of Orders
    orders: Mapped[List["Order"]] = relationship(secondary=user_order, back_populates="user")

#=====Schemas======

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

user_schema = UserSchema()
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

#=======Routes=========

@app.route('/users', methods=['POST'])
def create_user():
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_user = User(name=user_data['name'], address=user_data['address'], email=user_data['email'])
    db.session.add(new_user)
    db.session.commit()

    return user_schema.jsonify(new_user), 201

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)    