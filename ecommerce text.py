from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, String, Column, Float, DateTime, Integer, select
from typing import List
from datetime import datetime, timezone
from marshmallow import ValidationError, fields


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:%40Soccer90@localhost/ecommerce_api'

#Create  Base Class
class Base(DeclarativeBase):
    pass

#Initialize extensions
db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

#The association table between Users and Orders
order_product = Table(
	"order_product",
	Base.metadata,	
	Column("order_id", ForeignKey("orders.id")),
    Column("product_id", ForeignKey("product.id")),
)
user_order = Table(
	"user_order",
	Base.metadata,	
	Column("order_id", ForeignKey("orders.id")),
    Column("user_id", ForeignKey("user.id")),
)
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    users: Mapped[List["User"]] = relationship(secondary=user_order, back_populates="orders")
    order_products: Mapped[List["Product"]] = relationship(secondary=order_product, back_populates="product_orders")

class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_name: Mapped[str] = mapped_column(String(200))
    price: Mapped[Float] = mapped_column(Float, nullable=False)
    product_orders : Mapped[List["Order"]] = relationship(secondary=order_product, back_populates="order_products")

class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200))
    

#One-to-Many relationship from this User to a List of Orders
    orders: Mapped[List["Order"]] = relationship(secondary=user_order, back_populates="users")

#=====Schemas======

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
    user_id = fields.Integer()
class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

user_schema = UserSchema()
users_schema = UserSchema(many=True)
order_schema = OrderSchema()
orders_schema = OrderSchema(many=True)
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)

#=======Routes=========

#Create a User
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

#Read users

@app.route('/users', methods=['GET'])
def get_users():
    query = select(User)
    users = db.session.execute(query).scalars().all()

    return users_schema.jsonify(users), 200

#Read an individual user

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = db.session.get(User, id)
    return user_schema.jsonify(user), 200

#Update a user

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    try:
        user_data = user_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    user.name = user_data['name']
    user.email = user_data['email']
    user.address = user_data['address']

    db.session.commit()
    return user_schema.jsonify(user), 200

#Delete a user

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = db.session.get(User, id)

    if not user:
        return jsonify({"message": "Invalid user id"}), 400
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"succefully deleted user {id}"}), 200

#Create a product

@app.route('/products', methods=['POST'])
def create_product():
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_product = Product(product_name=product_data['product_name'], price=product_data['price'])
    db.session.add(new_product)
    db.session.commit()

    return user_schema.jsonify(new_product), 201

#Read products
@app.route('/products', methods=['GET'])
def get_products():
    query = select(Product)
    products = db.session.execute(query).scalars().all()

    return products_schema.jsonify(products), 200

#Read a product
@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = db.session.get(Product, id)
    return product_schema.jsonify(product), 200

#Update a product

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    try:
        product_data = product_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    product.product_name = product_data['product_name']
    product.price = product_data['price']

    db.session.commit()
    return product_schema.jsonify(product), 200


#Delete a product

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = db.session.get(Product, id)

    if not product:
        return jsonify({"message": "Invalid product id"}), 400
    
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": f"succefully deleted product {id}"}), 200

#Create order

@app.route('/orders', methods=['POST'])
def create_order():
    try:
        order_data = order_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_order = Order(user_id=order_data['user_id'])
    db.session.add(new_order)
    db.session.commit()

    return order_schema.jsonify(new_order), 201

#Add a product to an order

@app.route('/orders/<int:order_id>/add_product/<int:product_id>', methods=['POST'])
def create_product_to_order(order_id, product_id):
    order = db.session.get(Order, order_id)
    product = db.session.get(Product, product_id)

    if product in order.order_products:
        return jsonify({"message": f"Product.id{product_id} already exists"}), 400
    order.order_products.append(product)
    db.session.commit()
    return jsonify({"message": f"Product.id{product_id} has been added to order.id {order_id}!"}), 200

#remove a product from an order

@app.route('/orders/<int:order_id>/delete_product/<int:product_id>', methods=['DELETE'])
def remove_product_from_order(order_id, product_id):
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"message": "Invalid order id"}), 400

    product = db.session.get(Product, product_id)
    if not product:
        return jsonify({"message": "Invalid product id"}), 400

    if product not in order.order_products:
        return jsonify({"message": "Product not in order"}), 400

    order.order_products.remove(product)
    db.session.commit()
    return jsonify({"message": f"Product{product_id} has successfully been removed from order {order_id}!"}), 200

#Read an order for a user

@app.route('/orders/<int:order_id>/user/<int:user_id>', methods=['GET'])
def get_orders(order_id, user_id):
    query = select(Order, order_id, User, user_id)
    orders = db.session.execute(query).scalars().all()

    return orders_schema.jsonify(orders), 200

#Read products for an order

@app.route('/orders/<int:order_id>/products', methods=['GET'])
def get_products_from_orders(order_id):
    query = select(Order, id, order_id)
    order = db.session.execute(query).scalars().all()

    return products_schema.jsonify(order.order_products), 200


if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)    