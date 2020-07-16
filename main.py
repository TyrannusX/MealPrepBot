from flask import Flask, redirect, url_for, request
import requests
import json
import recipes
app = Flask(__name__)


@app.route('/')
def landing_page():
    return 'Welcome To MealPrepBot'

@app.route('/KrogerSignIn')
def take_user_to_kroger_signin():
    http_client = http.client.HTTPConnection('api.kroger.com')
    http_client.request('GET', 'https://api.kroger.com/v1/connect/oauth2/authorize?scope=cart.basic:write&client_id={clientIdGoesHere}&redirect_uri=http://localhost:5000/OrderStuffPlease&response_type=code')
    response = http_client.getresponse()
    return response.read()


@app.route('/OrderStuffPlease', methods=['GET'])
def get_oauth_token_and_order_stuff():
    kroger_customer_token = request.args.get('code')

    form_data = {'grant_type': 'authorization_code', 'code': kroger_customer_token, 'redirect_uri': 'http://localhost:5000/OrderStuffPlease'}
    response = requests.post('https://api.kroger.com/v1/connect/oauth2/token', data=form_data, auth=({clientIdGoesHere}, {secretGoesHere}))
    response_json = json.loads(response.text)
    access_token = response_json['access_token']

    cart_data = {'items': []}
    for key in recipes.common_foods:
        cart_data['items'].append({'upc': recipes.common_foods[key], 'quantity': 1})

    cart_data_json = json.dumps(cart_data)
    response = requests.put('https://api.kroger.com/v1/cart/add', data=cart_data_json, headers={'Authorization': f'Bearer {access_token}'})
    return str(response.status_code)


if __name__ == '__main__':
    app.run()