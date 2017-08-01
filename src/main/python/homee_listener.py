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
osram_nodes = ['Fensterlampe', 'TerrasseWand']


def get_token():
    password = hashlib.sha512(homee_pass).hexdigest()
    url = "http://" + homee_ip + ":7681/access_token"
    form_data = {'device_name': 'homebridge', 'device_hardware_id': 'homebridge','device_os': 5,'device_type': 3,'device_app': 1}
    headers={"Content-Type" : "application/x-www-form-urlencoded"}

    r = requests.post(url, data=form_data, headers= headers, auth=HTTPBasicAuth(homee_user, password))
    token = r.text.split('&')[0].split('=')[1]
    expires = '123'
    return {'token': token, 'expires': expires}

def getConnection(token):
    connection = "ws://192.168.2.26:7681/connection?access_token="+token
    return connection

def make_dashing_call(value, name):
    curl_data = '{ "auth_token": "YOUR_AUTH_TOKEN", "value": "%s" }' % (value)
    curl_url = 'http://localhost:3030/widgets/%s' % (urllib.unquote(name))
    call(['curl', '-d', curl_data, curl_url])

def checkNode(name, raw_value):
    value = None
    if name in smoke_nodes:
        value = get_fibaro_smoke_temp(raw_value)
    if name in motion_nodes:
        value = get_fibaro_motion_temp(raw_value)
    if name in door_nodes:
        value = get_fibaro_door_state(raw_value)
    if name in osram_nodes:
        value = get_osram_light_status(raw_value)
    if value:
        make_dashing_call(value, name)

def get_fibaro_smoke_temp(value_raw):
    return str(value_raw) + " Celsius"

def get_fibaro_motion_temp(value_raw):
    return str(value_raw) + " Celsius"

def get_fibaro_door_state(value_raw):
    if value_raw == 0.0:
        value = "Geschlossen"
    else:
        value = "Offen"
    return value

def get_osram_light_status(value_raw):
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
            checkNode(action_name, action_value)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
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
