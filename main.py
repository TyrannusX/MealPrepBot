# flask/web framework imports
from flask import Flask, redirect, url_for, request, Response
import pymongo
from flask_cors import CORS
from bson.json_util import loads, dumps
from bson.objectid import ObjectId

# imports
import requests
import json
import recipes
import configs

# flask app instance with database
app = Flask(__name__)
CORS(app)
app.config['MONGO_URI'] = configs.MONGO_CONNECTION_STRING
client = pymongo.MongoClient(configs.MONGO_CONNECTION_STRING)
mongo_db = client['MealPrepBot']


@app.route('/')
def landing_page():
    return 'Welcome To MealPrepBot API'


@app.route('/Search/<criteria>', methods=['GET'])
def search_kroger(criteria):
    # obtain oauth token with search level access
    form_data = {'grant_type': 'client_credentials', 'scope': 'product.compact'}
    response = requests.post('https://api.kroger.com/v1/connect/oauth2/token', data=form_data, auth=(configs.KROGER_APP_ID, configs.KROGER_APP_SECRET))
    response_json = json.loads(response.text)
    access_token = response_json['access_token']

    # search for and return products
    response = requests.get(f'https://api.kroger.com/v1/products?filter.term={criteria}&filter.locationId={configs.KROGER_LOCATION_ID}', headers={'Authorization': f'Bearer {access_token}'})
    return response.text


@app.route('/Products', methods=['GET'])
def get_all_products():
    # Return all ingredients
    ingredients_from_db = mongo_db['ingredients'].find()
    response = []
    for ingredient in ingredients_from_db:
        ingredient['_id'] = str(ingredient['_id'])
        response.append(ingredient)
    return json.dumps(response)


@app.route('/AddProductToDb', methods=['POST'])
def add_product_to_db():
    # Insert record to db
    ingredient = json.loads(request.data)
    mongo_db['ingredients'].insert_one(ingredient)
    return Response("", status=201)


@app.route('/AddRecipeToDb', methods=['POST'])
def add_recipe_to_db():
    # Insert record to db
    recipe = json.loads(request.data)
    mongo_db['recipes'].insert_one(recipe)
    return Response("", status=201)


@app.route('/Recipes', methods=['GET'])
def get_all_recipes():
    # Return all ingredients
    recipes_from_db = mongo_db['recipes'].find()
    response = []
    for recipe in recipes_from_db:
        recipe['_id'] = str(recipe['_id'])
        response.append(recipe)
    return json.dumps(response)



@app.route('/OrderStuffPlease/<krogerCode>/<recipeId>', methods=['POST'])
def get_oauth_token_and_order_stuff(krogerCode, recipeId):
    # build up order request for kroger
    recipe_from_db = mongo_db['recipes'].find_one({'_id': ObjectId(recipeId)})
    recipe_json_str = dumps(recipe_from_db)
    recipe_json = loads(recipe_json_str)
    cart_data = {'items': []}
    counter = 0
    for ingredient in recipe_json['ingredients']:
        cart_data['items'].append({'upc': ingredient['upc'], 'quantity': int(recipe_json['quantities'][counter]['quantity'])})
        counter += 1

    # get oauth token with customer level access
    form_data = {'grant_type': 'authorization_code', 'code': krogerCode, 'redirect_uri': 'http://localhost:4200/ChooseYourRecipe'}
    response = requests.post('https://api.kroger.com/v1/connect/oauth2/token', data=form_data, auth=(configs.KROGER_APP_ID, configs.KROGER_APP_SECRET))
    response_json = json.loads(response.text)
    access_token = response_json['access_token']

    print(cart_data)
    cart_data_json = json.dumps(cart_data)
    response = requests.put('https://api.kroger.com/v1/cart/add', data=cart_data_json, headers={'Authorization': f'Bearer {access_token}'})
    return str(response.status_code)


if __name__ == '__main__':
    app.run(debug=True)