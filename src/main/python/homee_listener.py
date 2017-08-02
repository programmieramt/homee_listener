import websocket
import thread
import time
import hashlib
import base64
import requests
from requests.auth import HTTPBasicAuth
import json
import urllib
from subprocess import call

homee_pass = 'somepass'
homee_user = 'someuser'
homee_ip = '192.168.2.26'
token_expires = 0
homee_dict = {}

smoke_nodes = []
motion_nodes = ['Lichtsensor', 'Motion_Flur', 'Motion_oben']
door_nodes = ['Terrassentuer', 'Eingangstuer']
light_nodes = ['Fensterlampe', 'TerrasseWand']


def get_token():
    password = hashlib.sha512(homee_pass).hexdigest()
    url = "http://" + homee_ip + ":7681/access_token"
    form_data = {'device_name': 'homebridge', 'device_hardware_id': 'homebridge','device_os': 5,'device_type': 3,'device_app': 1}
    headers={"Content-Type" : "application/x-www-form-urlencoded"}

    print('requesting token')
    r = requests.post(url, data=form_data, headers= headers, auth=HTTPBasicAuth(homee_user, password))
    token = r.text.split('&')[0].split('=')[1]
    expires = '123'
    print('recieved token')
    return {'token': token, 'expires': expires}

def getConnection(token):
    connection = "ws://%s:7681/connection?access_token=%s" % (homee_ip, token)
    return connection

def make_dashing_call(value, name):
    curl_data = '{ "auth_token": "YOUR_AUTH_TOKEN", "value": "%s" }' % (value)
    curl_url = 'http://localhost:3030/widgets/%s' % (urllib.unquote(name))
    call(['curl', '-d', curl_data, curl_url])

def checkNode(name, raw_value, unit):
    value = None
    if name in smoke_nodes:
        value = get_fibaro_smoke_temp(raw_value, unit)
    if name in motion_nodes:
        value = get_fibaro_motion_temp(raw_value, unit)
    if name in door_nodes:
        value = get_fibaro_door_state(raw_value, unit)
    if name in light_nodes:
        value = get_light_status(raw_value, unit)

    if value:
        make_dashing_call(value, name)


def get_fibaro_smoke_temp(value_raw, unit):
    if unit != "Lux":
        return str(value_raw) + " Celsius"
    return None	

def get_fibaro_motion_temp(value_raw, unit):
    if unit != "Lux":
        return str(value_raw) + " Celsius"
    return None	

def get_fibaro_door_state(value_raw, unit):
    value = None
    if unit != '%C2%B0C':
        if value_raw == 0.0:
            value = "Geschlossen"
        else:
            value = "Offen"
    return value

def get_light_status(value_raw, unit):
    if value_raw == 0.0:
        value = "Aus"
    else:
        value = "An"
    return value

def on_message(ws, raw_message):
    message = json.loads(raw_message)
    if 'nodes' in message:
        homee_nodes = message['nodes']
        for node in homee_nodes:
            name = node['name']
            id = node['id']
        homee_dict[id] = name

    if 'attribute' in message and 'nodes' not in message:
        if message['attribute']['current_value'] == message['attribute']['target_value']:
            action_name = homee_dict[message['attribute']['node_id']]
            action_value = message['attribute']['current_value']
	    action_unit = message['attribute']['unit']
	    print(action_name, action_value)
            checkNode(action_name, action_value, action_unit)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print('Connection created')
    ws.send('GET:nodes')

if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(getConnection(get_token()['token']),
                  subprotocols=['v2'],
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
