from __future__ import annotations

from typing import Sequence

from Crypto.Cipher import Blowfish


def _to_key_bytes(key: Sequence[int] | bytes | bytearray | str) -> bytes:
    if isinstance(key, str):
        return bytes(ord(ch) & 0xFF for ch in key)
    return bytes(int(value) & 0xFF for value in key)


def _to_data_bytes(data: Sequence[int] | bytes | bytearray) -> bytes:
    return bytes(int(value) & 0xFF for value in data)


def return_ir(e: Sequence[int] | bytes | bytearray, t: Sequence[int] | bytes | bytearray | str) -> list[float]:
    """
    js の `return_ir(e, t)` の Python 移植版。

    JavaScript 実装と一致する動作：
    - `t` は Blowfish の鍵として使用される。
    - `e` は ECB モードで復号される。
    - 8 バイトの完全なブロックのみが処理される。
    - 要求されたサンプル出力に合わせて、結果は浮動小数点数のリストとして返される。
    """
    data = _to_data_bytes(e)
    key = _to_key_bytes(t)

    block_len = (len(data) // Blowfish.block_size) * Blowfish.block_size
    if block_len == 0:
        return []

    cipher = Blowfish.new(key, Blowfish.MODE_ECB)
    decrypted = cipher.decrypt(data[:block_len])
    return [float(value) for value in decrypted]