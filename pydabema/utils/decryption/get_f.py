import hmac
import hashlib

def get_f_data(variant, key, message):
    """
    JavaScriptの get_f_data と同等の処理を行う関数
    :param variant: ハッシュアルゴリズムの指定 (1, 224, 256, 384, 512)
    :param key: 秘密鍵 (文字列またはバイト列)
    :param message: メッセージ (文字列またはバイト列)
    :return: バイナリ文字列（JSのString.fromCharCodeの結果に相当）
    """
    
    # アルゴリズムのマッピング
    hash_map = {
        1: hashlib.sha1,
        224: hashlib.sha224,
        256: hashlib.sha256,
        384: hashlib.sha384,
        512: hashlib.sha512
    }
    
    if variant not in hash_map:
        raise ValueError(f"Unsupported variant: {variant}")
    
    if isinstance(key, str):
        key = key.encode('latin1')
    if isinstance(message, str):
        message = message.encode('latin1')
        
    # HMACオブジェクトの作成と計算
    algorithm = hash_map[variant]
    h = hmac.new(key, message, algorithm)
    digest = h.digest()

    return digest.decode('latin1')