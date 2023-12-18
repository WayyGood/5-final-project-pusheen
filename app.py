from flask import Flask, render_template, request, redirect, url_for,jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
#API settings
API_URL = 'https://api.calorieninjas.com/v1/nutrition?query='
API_KEY = 'Mg32i8it134/WHBsJ/BNMw==VzPRDn8ISb0n1GPZ'
# db conncetion 
client = MongoClient("mongodb://localhost:27017/")
db = client['fitness_app']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Hashing the password
        hashed_password = generate_password_hash(request.form.get('password'))

        user_info = {
            "username": request.form.get('username'),
            "password": hashed_password,
            "gender": request.form.get('gender'),
            "dob": request.form.get('dob'),
            "height": request.form.get('height'),
            "current_weight": request.form.get('current_weight')
        }
        db.users.insert_one(user_info)
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # finding user by user name 
        user = db.users.find_one({"username": username})

        if user and check_password_hash(user['password'], password):
            # auth successf
            return redirect(url_for('index'))  # Redirect to a different page after login
        else:
            # Authentication failed
            return "Invalid credentials", 401

    return render_template('signin.html')

@app.route('/nutrition-diary', methods=['GET', 'POST'])
def nutrition_diary():
    # Initialize an empty list for entries
    entries = []

    if request.method == 'POST':
        # Get the food item from the form
        food_item = request.form.get("food-item")
        
        # Make the API call
        response = requests.get(
            f"{API_URL}?query={food_item}",
            headers={'X-Api-Key': API_KEY}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Assuming the first item in the response is what we want
            if data['items']:
                item_data = data['items'][0]
                calories = item_data['calories']
                
                # Create an entry to insert into the database
                entry = {
                    "user_id": session['user_id'],
                    "food_item": food_item,
                    "calories": calories,
                    "date": request.form.get("date")
                    # Add more fields from item_data if necessary
                }
                db.nutrition.insert_one(entry)
            else:
                pass
        else:
            # Handle error from API
            print(f"Error: {response.status_code}, {response.text}")
    # historical data from MongoDB
    entries = db.nutrition.find().sort("date", -1)  # Sort by date descending
    return render_template('nutrition-diary.html', entries=entries)

@app.route('/get-nutrition', methods=['POST'])
def get_nutrition():
    data = request.get_json()
    food_item = data['food_item']
    
    # Make the API call
    response = requests.get(
        'https://api.calorieninjas.com/v1/nutrition',
        headers={'X-Api-Key': API_KEY},
        params={'query': food_item}
    )
    
    if response.status_code == 200:
        # Pass the API response as JSON back to the front-end
        return jsonify(response.json())
    else:
        # Handle any error that occurred during the API call
        return jsonify({'error': 'Could not retrieve nutrition data'}), response.status_code


if __name__ == '__main__':
    app.run(debug=True)
