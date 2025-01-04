from hashlib import sha256, pbkdf2_hmac
import secrets
import binascii
import datetime
import time
import hmac
import hashlib
import random

# Base58 字符集
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def b58encode(v):
    # Base58 编码实现
    nPad = len(v)
    v = v.lstrip(b'\0')
    nPad -= len(v)

    p, acc = 1, 0
    for c in reversed(v):
        acc += p * c
        p = p << 8

    result = ''
    while acc:
        acc, idx = divmod(acc, 58)
        result = ALPHABET[idx] + result

    return '1' * nPad + result

def load_wordlist():
    with open('english.txt', 'r') as f:
        return [w.strip() for w in f.readlines()]

def generate_new_key(wordlist):
    # 获取当前时间信息
    current_time = datetime.datetime.now()
    timestamp = int(time.time() * 1000)
    time_bytes = timestamp.to_bytes(8, 'big')

    # 系统性能计数器（如CPU周期）作为额外熵源
    perf_counter_bytes = int(time.perf_counter() * 10**9).to_bytes(8, 'big')
    
    # 进程性能计数器
    process_time_bytes = int(time.process_time() * 10**9).to_bytes(8, 'big')
    
    # 获取系统随机数
    system_random = random.SystemRandom()
    sys_random_bytes = system_random.getrandbits(64).to_bytes(8, 'big')
    
    # 生成16字节(128位)的随机熵
    random_entropy = secrets.token_bytes(16)
    
    # 生成10000个随机数并拼接
    extra_random = ''.join(str(secrets.randbelow(10)) for _ in range(10000))
    extra_entropy = sha256(extra_random.encode()).digest()[:8]  # 取前8字节
    
    # 混合所有熵源
    mixed_entropy = bytes([
        a ^ b ^ c ^ d ^ e ^ f
        for a, b, c, d, e, f in zip(
            time_bytes + time_bytes,
            perf_counter_bytes + perf_counter_bytes,
            process_time_bytes + process_time_bytes,
            sys_random_bytes + sys_random_bytes,
            random_entropy,
            extra_entropy + extra_entropy  # 新增的熵源
        )
    ])
    
    # 额外的SHA256哈希来进一步混合熵
    entropy = sha256(mixed_entropy).digest()[:16]

    print(f"\n使用时间生成: {current_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print(f"性能计数器: {time.perf_counter()}")
    print(f"进程时间: {time.process_time()}")
    print(f"额外随机数长度: {len(extra_random)}")

    # 计算校验和
    entropy_bits = bin(int.from_bytes(entropy, 'big'))[2:].zfill(128)
    checksum = bin(int(sha256(entropy).hexdigest(), 16))[2:].zfill(256)[:4]

    # 组合熵和校验和
    combined_bits = entropy_bits + checksum

    # 将比特分成11位的组，并转换为助记词
    indexes = [int(combined_bits[i:i+11], 2) for i in range(0, len(combined_bits), 11)]
    mnemonic = ' '.join(wordlist[index] for index in indexes)
    
    return mnemonic, current_time

def mnemonic_to_private_key(mnemonic, timestamp):
    salt = 'mnemonic' + timestamp.strftime('%Y%m%d%H%M%S')
    seed = pbkdf2_hmac('sha512', mnemonic.encode(), salt.encode(), 2048)
    
    # 从种子派生主私钥 (使用 BIP32)
    master_key = hmac.new(b'Bitcoin seed', seed, hashlib.sha512).digest()
    master_private_key = master_key[:32]
    master_chain_code = master_key[32:]
    
    return seed, master_private_key

def to_wif(private_key, compressed=True, testnet=False):
    version = b'\xef' if testnet else b'\x80'
    extended_key = version + private_key
    
    if compressed:
        extended_key += b'\x01'
    
    double_sha256 = hashlib.sha256(hashlib.sha256(extended_key).digest()).digest()
    extended_key += double_sha256[:4]
    
    return b58encode(extended_key)

def main():
    wordlist = load_wordlist()
    
    print("\nBIP39助记词和私钥生成器")
    print("------------------------")
    
    mnemonic, current_time = generate_new_key(wordlist)
    seed, master_private_key = mnemonic_to_private_key(mnemonic, current_time)
    
    print("\n生成的助记词:")
    print(mnemonic)
    print("\n生成的种子 (hex):")
    print(binascii.hexlify(seed).decode())
    print("\n主私钥 (hex):")
    print(binascii.hexlify(master_private_key).decode())
    print("\nWIF格式私钥 (压缩格式):")
    print(to_wif(master_private_key))

if __name__ == "__main__":
    main()