import hmac, time, hashlib, uuid
from base64 import urlsafe_b64encode

def gen_temp_token(session):
        _USERAPI = "https://api.p-c3-e.abema-tv.com/v1/users"
        def gen_key_secret(device_id_str: str) -> str:
            """
            デバイスIDと現在の時間(1時間単位)に基づいて認証トークンを生成する。
            """
            # 定数
            SECRET_KEY = (
                b"v+Gjs=25Aw5erR!J8ZuvRrCx*rGswhB&qdHd_SYerEWdU&a?3DzN9B"
                b"Rbp5KwY4hEmcj5#fykMjJ=AuWz5GSMY-d@H7DMEh3M@9n2G552Us$$"
                b"k9cD=3TxwWe86!x#Zyhe"
            )

            def compute_hmac(data: bytes) -> bytes:
                """HMAC-SHA256を計算してダイジェストを返すヘルパー"""
                return hmac.new(SECRET_KEY, data, hashlib.sha256).digest()

            def b64_strip(data: bytes) -> bytes:
                """URL safe Base64でエンコードし、末尾のパディング(=)を削除する"""
                return urlsafe_b64encode(data).rstrip(b"=")

            ts_1hour = (int(time.time()) + 3600) // 3600 * 3600
            time_struct = time.gmtime(ts_1hour)
            
            device_id_bytes = device_id_str.encode("utf-8")
            ts_bytes = str(ts_1hour).encode("utf-8")

            digest = compute_hmac(SECRET_KEY)

            for _ in range(time_struct.tm_mon):
                digest = compute_hmac(digest)

            digest = compute_hmac(b64_strip(digest) + device_id_bytes)

            for _ in range(time_struct.tm_mday % 5):
                digest = compute_hmac(digest)

            digest = compute_hmac(b64_strip(digest) + ts_bytes)

            for _ in range(time_struct.tm_hour % 5):
                digest = compute_hmac(digest)

            return b64_strip(digest).decode("utf-8")

        device_id = str(uuid.uuid4())
        json_data = {"deviceId": device_id, "applicationKeySecret": gen_key_secret(device_id)}

        res = session.post(_USERAPI, json=json_data).json()

        try:
            token = res['token']
            status = True
        except:
            status = False
            return status, None, None, None

        return status, token, device_id, res["profile"]["userId"]

def guest_web(session):
    status, token, device_id, member_id = gen_temp_token(session)
    if not status:
        return False, {"field_1": None, "field_2": None}
    session.headers.update({"Authorization": "Bearer " + token})
    return True, {"field_1": member_id, "field_2": device_id}