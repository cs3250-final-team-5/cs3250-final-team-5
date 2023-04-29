from flask import Flask, request, render_template, session, redirect, url_for
from flask_socketio import SocketIO
from flask_socketio import join_room, leave_room, send
import os


# Create app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'key1234'
socketio = SocketIO(app)


### Cafe

# Menu items
menu = {
    "croissant": {"price": 2.49, "description": "Flaky pastry with buttery flavor"},
    "bagel": {"price": 1.99, "description": "Soft and chewy, great with cream cheese or jam"},
    "muffin": {"price": 2.99, "description": "Freshly baked, great for breakfast or snack"}
}

drinks = {
    "coffee": {"price": 2.99, "description": "Freshly brewed coffee"},
    "latte": {"price": 3.99, "description": "Espresso with steamed milk and a layer of foam"},
    "cappuccino": {"price": 3.49, "description": "Espresso with steamed milk and more foam than a latte"} 
}


# Welcome page
@app.route('/')
def welcome():
    return render_template('welcome.html', menu=menu, drinks=drinks)


# Order page
@app.route('/order', methods=['GET', 'POST'])
def order():
    message = ''
    if request.method == 'POST':
        items = request.form.getlist('items')
        total_price = sum([menu[item]['price'] for item in items])
        message = f'Thank you for you order, {request.form["name"]} ({request.form["student_id"]})! Your order has been placed. Your total is ${total_price:.2f}.'
    return render_template('order.html', menu=menu, drinks=drinks, message=message)


### Chat

# List to store rooms
rooms = {}

# Chat login page
@app.route("/index", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        join = request.form.get("join", False)
            
        if join != False:
            room = 1234
            rooms[room] = {"members": 0, "messages": []}
            session["room"] = room
            session["name"] = name
        return redirect(url_for("room"))

    return render_template("index.html")

# Chat page
@app.route("/chat")
def room():
    room = session.get("room")

    return render_template("chat.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "(has entered the room)"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
    
    send({"name": name, "message": "(has left the room)"}, to=room)
    print(f"{name} has left the room {room}")


# Run app
if __name__ == '__main__':
    socketio.run(app, debug=True)

