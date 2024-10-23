from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:champ%40mysql@localhost:3306/champ1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define a model for tracking orders
class Tracking(db.Model):
    __tablename__ = 'tracking'
    track_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Tracking(track_id={self.track_id}, order_id={self.order_id}, status={self.status}, updated_at={self.updated_at})"

# Define a model for food orders
class FoodOrder(db.Model):
    __tablename__ = 'food_order'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    items = db.Column(db.String(255), nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"FoodOrder(id={self.id}, items={self.items}, total_price={self.total_price})"

@app.route('/')
def index():
    return "Welcome to the Tracking API"

# Webhook endpoint to handle intents from Dialogflow
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(force=True)
    query_result = req.get('queryResult', {})

    intent_name = query_result.get('intent', {}).get('displayName')

    if intent_name == 'track.order':
        return handle_track_order(query_result)
    elif intent_name == 'order.add':
        return handle_add_order(query_result)
    else:
        return jsonify({'fulfillmentText': 'Intent not recognized'})

def handle_track_order(query_result):
    # Extract parameters from Dialogflow request
    parameters = query_result.get('parameters', {})
    track_id = parameters.get('track_id')

    if track_id is None:
        fulfillment_text = "Please provide a valid track ID."
    else:
        try:
            # Query the database for tracking information
            tracking_info = Tracking.query.filter_by(track_id=track_id).first()

            if tracking_info:
                status = tracking_info.status
                fulfillment_text = f"The status of order {track_id} is {status}."
            else:
                fulfillment_text = f"Order with track ID {track_id} not found."

        except Exception as e:
            fulfillment_text = f"Error occurred: {str(e)}"

    # Prepare JSON response to send back to Dialogflow
    response = {
        'fulfillmentText': fulfillment_text
    }

    return jsonify(response)

def handle_add_order(query_result):
    parameters = query_result.get('parameters', {})
    food_items = parameters.get('food', [])
    quantities = parameters.get('number', [])

    if not food_items or not quantities or len(food_items) != len(quantities):
        fulfillment_text = "Please provide both food items and their respective quantities."
    else:
        try:
            # Menu with prices
            menu = {
                'paneer': 150,
                'butter chicken': 200,
                'veg biryani': 180,
                'chole bhature': 160,
                'masala dosa': 120,
                'pizza': 299,
                'paratha': 20,
                'biriyani': 180
            }

            total_price = 0
            items_list = []

            # Calculate total price and build items string
            for food_item, quantity in zip(food_items, quantities):
                price = menu.get(food_item.lower())
                if price is None:
                    fulfillment_text = f"{food_item} is not on the menu."
                    return jsonify({'fulfillmentText': fulfillment_text})
                
                item_total = price * quantity
                total_price += item_total
                items_list.append(f"{quantity} {food_item}(s)")

            items_str = ", ".join(items_list)

            # Create a new food order record
            new_order = FoodOrder(items=items_str, total_price=total_price)
            db.session.add(new_order)
            db.session.commit()

            # Create a new tracking record
            new_tracking = Tracking(order_id=new_order.id, status="Order placed", updated_at=datetime.utcnow())
            db.session.add(new_tracking)
            db.session.commit()

            fulfillment_text = f"Added {items_str} to your order. Total price: ₹{total_price}. Your tracking ID is {new_tracking.track_id}."

        except Exception as e:
            db.session.rollback()
            fulfillment_text = f"Error occurred: {str(e)}"

    # Prepare JSON response to send back to Dialogflow
    response = {
        'fulfillmentText': fulfillment_text
    }

    return jsonify(response)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
