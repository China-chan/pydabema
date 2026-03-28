import base58
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

from .get_ir import return_ir
from .get_yr import return_yr
from .get_f import get_f_data

def decode_hex(hex_str):
    """ 16進文字列をバイト列に変換 """
    return binascii.unhexlify(hex_str)

def aes_decrypt(original_json, iv_hex, key_list, ciphertext_raw):
    """ AES-CBCモードで復号しJSONを更新する """
    iv = decode_hex(iv_hex)
    key = bytes(key_list)
    
    if isinstance(ciphertext_raw, memoryview):
        ciphertext_raw = ciphertext_raw.tobytes()
    ciphertext = bytes(ciphertext_raw)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_raw = cipher.decrypt(ciphertext)

    try:
        decrypted_bytes = unpad(decrypted_raw, AES.block_size)
        decrypted_text = decrypted_bytes.decode('utf-8')
    except ValueError:
        decrypted_text = "[Padding error: Raw data not decodable]"

    # JSONの特定の値を書き換え
    original_json["keys"][0]["k"] = decrypted_text
    original_json["keys"][0]["alg"] = "A128KW"
    
    return original_json

def get_y_key(kid, user_id, y_slice):
    """
    複雑なロジックを用いてAESの鍵(y)を生成する。
    """
    # 秘密の変換テーブル
    SECRET_TABLES = [
        [200, 196, 157, 49, 219, 232, 69, 76, 83, 241, 90, 229, 150, 242, 92, 15, 84, 148, 229, 112, 54, 1, 119, 2, 169, 57, 211, 105, 136, 202, 103, 168],
        [234, 169, 154, 104, 251, 227, 123, 14, 69, 153, 122, 248, 216, 214, 90, 81, 11, 135, 195, 113, 29, 23, 116, 2, 161, 38, 253, 115, 142, 200, 42, 189],
        [200, 165, 201, 110, 242, 224, 40, 65, 59, 242, 81, 195, 162, 188, 101, 3, 79, 254, 234, 10, 16, 95, 72, 35, 164, 67, 164, 71, 240, 227, 121, 199],
        [245, 130, 172, 48, 216, 131, 115, 127, 66, 236, 28, 185, 136, 252, 90, 79, 119, 243, 179, 12, 72, 39, 98, 61, 137, 71, 249, 115, 214, 177, 21, 172],
        [89, 223, 151, 248, 170, 122, 131, 80, 144, 118, 56, 163, 241, 252, 134, 140, 142, 29, 185, 213, 230, 84, 127, 54, 179, 36, 10, 155, 207, 175, 138, 50],
        [14, 100, 3, 93, 159, 22, 163, 57, 95, 210, 206, 203, 142, 255, 17, 137, 104]
    ]
    RC4_SEED_KEY = [44, 128, 188, 10, 35, 20]

    def rc4_crypt(key_data, input_data):
        """RC4アルゴリズムによる共通鍵暗号処理"""
        s_box = list(range(256))
        j = 0
        for i in range(256):
            j = (j + s_box[i] + key_data[i % len(key_data)]) % 256
            s_box[i], s_box[j] = s_box[j], s_box[i]
        
        i = 0
        j = 0
        res = []
        for byte in input_data:
            i = (i + 1) % 256
            j = (j + s_box[i]) % 256
            s_box[i], s_box[j] = s_box[j], s_box[i]
            res.append(byte ^ s_box[(s_box[i] + s_box[j]) % 256])
        return res

    def get_const_str(index):
        """テーブルから復号された文字列を取得"""
        decrypted = rc4_crypt(RC4_SEED_KEY, SECRET_TABLES[index])
        return ''.join(chr(c) for c in decrypted)

    def get_const_list(index):
        """テーブルから復号されたリストを取得"""
        return rc4_crypt(RC4_SEED_KEY, SECRET_TABLES[index])

    def to_codes(s):
        """文字列を文字コードのリストに変換"""
        return [ord(c) for c in s]

    # --- ロジック開始 ---
    version_flag = y_slice[-1]
    MOD = 256

    if version_flag == "5":
        # バージョン5の処理 (ロジック順序を固定)
        salt_base = get_const_str(4)
        seed_c = get_f_data(MOD, salt_base, kid + user_id)
        seed_f = get_f_data(MOD, seed_c, user_id)
        seed_d = get_f_data(MOD, seed_c, kid)
        
        # 鍵生成
        key_l = rc4_crypt(get_const_list(5), to_codes(seed_f))
        key_w = rc4_crypt(get_const_list(5), to_codes(seed_d))
        
        # データの復号
        payload_v = list(base58.b58decode(y_slice[:-1]))
        decrypted_v = rc4_crypt(key_w, payload_v)
        
        return return_ir(decrypted_v, key_l)

    elif version_flag == "4":
        # バージョン4の処理
        # t = F(256, Dr(3), Dr(2) + kid)
        seed_t = get_f_data(MOD, get_const_str(3), get_const_str(2) + kid)
        # i = F(256, t, user_id + kid)
        seed_i = get_f_data(MOD, seed_t, user_id + kid)
        # o = F(256, t, Dr(2) + user_id)
        seed_o = get_f_data(MOD, seed_t, get_const_str(2) + user_id)
        
        payload_u = list(base58.b58decode(y_slice))
        
        # s = return_yr(codes(o), u)
        # return return_ir(s, codes(i))
        # ※この順序が重要
        temp_s = return_yr(to_codes(seed_o), payload_u)
        return return_ir(temp_s, to_codes(seed_i))

    else:
        # デフォルトの処理
        # t = F(256, Dr(1), kid + Dr(0))
        seed_t = get_f_data(MOD, get_const_str(1), kid + get_const_str(0))
        # i = F(256, t, kid + user_id)
        seed_i = get_f_data(MOD, seed_t, kid + user_id)
        # o = F(256, t, user_id + Dr(0))
        seed_o = get_f_data(MOD, seed_t, user_id + get_const_str(0))
        
        payload_u = list(base58.b58decode(y_slice))
        
        # s = return_ir(u, codes(i))
        # return return_yr(codes(o), s)
        # g==4の時と return_ir と return_yr の入れ子構造が逆になっている
        temp_s = return_ir(payload_u, to_codes(seed_i))
        return return_yr(to_codes(seed_o), temp_s)

def decrypt_key(original_json, k_slice, y_slice, o_slice, kid, user_id):
    """ メインの復号エントリーポイント """
    iv_hex = o_slice
    
    # 動的な鍵生成
    derived_y = get_y_key(kid=kid, user_id=user_id, y_slice=y_slice)
    key_list = [int(val) for val in derived_y]
    
    # Base58暗号文のデコード
    ciphertext = list(base58.b58decode(k_slice))
    
    # AES復号
    return aes_decrypt(original_json, iv_hex, key_list, ciphertext)