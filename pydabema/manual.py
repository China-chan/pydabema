import re
import base64
import requests
import xml.etree.ElementTree as ET
from rich.console import Console


from utils.gen_token import guest_web
import utils.decryption.decryptor as decryption_logic

print("init s/d")
console = Console()
print(" + GoodBye Fucking Abema DRM")




web_session = requests.Session()
status, message = guest_web(web_session)
if not status:
    print("ERROR USE GUEST: {}".format(message))

member_id = message["field_1"]
print("Using Account ID: {}".format(member_id))

# TARGET CONTENT: サイレント・ウィッチ_第1話_同期が来たりて無茶を言う
#target_cid = "189-11_s1_p12"
#target_kid = "BAa3jqMUStCICZrH9yhpEA"

def get_default_KID(mpd_content):
    root = ET.fromstring(mpd_content)

    namespaces = {
        '': 'urn:mpeg:dash:schema:mpd:2011',
        'cenc': 'urn:mpeg:cenc:2013'
    }

    for elem in root.iterfind('.//{urn:mpeg:dash:schema:mpd:2011}Period//{urn:mpeg:dash:schema:mpd:2011}AdaptationSet//{urn:mpeg:dash:schema:mpd:2011}ContentProtection', namespaces):
        default_KID = elem.get('{urn:mpeg:cenc:2013}default_KID')
        if default_KID:
            return default_KID
    return None
def get_content_info(url):
    # only support url 
    # : https://abema.tv/video/episode/26-248_s1_p1
    match = re.search(r'/([^/]+)$', url)
    if match:
        episode_id = match.group(1)
        
        mpd_response = web_session.get(f"https://ds-vod-abematv.akamaized.net/program/{episode_id}/manifest.mpd").text
        sex_kid = get_default_KID(mpd_response)

        print("Get normal KID: {}".format(sex_kid))
        target_kid = base64.b64encode(bytes.fromhex(sex_kid.replace("-", "").upper())).decode('utf-8').replace("==", "").replace("+", "-").replace("/", "_")
        print("Gen encode KID: {}".format(target_kid))
        return episode_id, target_kid 
    else:
        print("Bad url. please die")
        exit(1)
def get_dash_info():
    _KEYPARAMS = { ## ANDROID TV版を使うと、対応してないタイプの暗号化(8,e)が帰ってきます。 なうさぽーと4,5
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
        "ct": "program"
    }
    _PAYLOAD = {
        "kids":[target_kid],
        "type":"temporary"
    }
    dash_return = web_session.post("https://license.p-c3-e.abema-tv.com/abematv-dash", params=_KEYPARAMS, json=_PAYLOAD)
    data = dash_return.json()
    try:
        if data["error"] == "playback not allowed":
            print("Require PREMIUM")
            exit(1)
    except:
        pass
    gl = data["keys"][0]

    kid = gl['kid']
    k   = gl['k']
    kty = gl['kty']
    
    print("GET KID: {}".format(kid))
    print("GET K:   {}".format(k))
    print("GET KTY: {}".format(kty))
    
    k_value = k
    hash = k_value.split(".")[-1]
    k_slice = k_value.split(".")[0]
    y_slice = k_value.split(".")[1]

    return data, k_slice, y_slice, hash, kid

try:
    url_input = input("URL (e.x. abema.tv/video/episode/26-248_s1_p1) >> ")
    target_cid, target_kid = get_content_info(url_input)

    enc_json, enc_k, enc_y, enc_hash, enc_kid = get_dash_info()
    decrypt_json = decryption_logic.decrypt_key(enc_json, enc_k, enc_y, enc_hash, enc_kid, member_id)

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
    
    print("Decrypt Key!")
    print(f"{result_kid}:{result_key}")
except:
    console.print_exception(show_locals=True)