# pydabema/decrypt.py

import base64
import requests
from .utils.gen_token import guest_web

from .utils.decryption.decryptor import decrypt_key

def get_dash_info(web_session, target_cid, target_ct, target_kid):
    _KEYPARAMS = { ## Only Support Web base os
        "osName": "pc",
        "osVersion": "1.0.0",
        "osLand": "ja",
        "osTimezone": "Asia/Tokyo",
        "appVersion": "v25.1009.2"
    }
    restoken = web_session.get("https://api.p-c3-e.abema-tv.com/v1/media/token", params=_KEYPARAMS).json()
    mediatoken = restoken['token']     

    _KEYPARAMS = {
        "t": mediatoken,
        "cid": target_cid,
        "ct": target_ct
    }
    _PAYLOAD = {
        "kids":[target_kid],
        "type":"temporary"
    }
    dash_return = web_session.post("https://license.p-c3-e.abema-tv.com/abematv-dash", params=_KEYPARAMS, json=_PAYLOAD)
    data = dash_return.json()
    try:
        if data["error"] == "playback not allowed":
            return {"status": False, "message": "require_premium", "return": None}
    except:
        pass
    gl = data["keys"][0]

    kid = gl['kid']
    k   = gl['k']
    kty = gl['kty']
    
    k_value = k
    hash = k_value.split(".")[-1]
    k_slice = k_value.split(".")[0]
    y_slice = k_value.split(".")[1]

    return {"status": True, "message": None, "return": [data, k_slice, y_slice, hash, kid]}

def decrypt(content_type: str = "program", content_id: str = None, kid: str = None, session: requests.Session = None, member_id: str = None):
    if session == None:
        session = requests.Session()
        status, message = guest_web(session)
        if not status:
            return {"status": False, "message": "guest_login_failed"}
        member_id = message["field_1"]
    
    result_json = get_dash_info(session, content_id, content_type, kid)
    if result_json["status"]:
        encrypt_data, k_slice, y_slice, all_hash, kid = result_json["return"]
        pass
    else:
        return {"status": False, "message": result_json["message"]}
    
    decrypt_json = decrypt_key(encrypt_data, k_slice, y_slice, all_hash, kid, member_id)

    
    ## decode data to string
    temp_d = decrypt_json['keys'][0]['k']
    temp_f = decrypt_json['keys'][0]['kid']
    
    temp_d = temp_d.replace('_', '/').replace('-', '+')
    temp_f = temp_f.replace('_', '/').replace('-', '+')
    
    while len(temp_d) % 4 != 0:
        temp_d += '='
    while len(temp_f) % 4 != 0:
        temp_f += '='
    
    raw1 = base64.b64decode(temp_d)
    raw2 = base64.b64decode(temp_f)
    
    result_key = ''.join(format(c, '02x') for c in raw1)
    result_kid = ''.join(format(c, '02x') for c in raw2)
    
    return {
        "status": True,
        "message": None,
        "result": {
            "kid": result_kid,
            "key": result_key,
            "block": result_kid+":"+ result_key 
        },
        "debug": {
            "member_id": member_id,
            "kid": kid,
            "encrypt_data": k_slice,
        }
    }