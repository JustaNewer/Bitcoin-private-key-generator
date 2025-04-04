from hashlib import sha256, pbkdf2_hmac
import secrets
import binascii
import datetime
import time
import hmac
import hashlib
import random
import socket
import uuid
import platform
import psutil
import os
import string
import threading
import queue
import ctypes
import multiprocessing

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

# 添加多线程竞争熵收集函数
def collect_thread_entropy(size=32):
    """
    通过多线程竞争和系统资源波动收集高质量熵
    
    Args:
        size: 要生成的熵字节数
    
    Returns:
        bytes: 熵数据
    """
    entropy_queue = queue.Queue()
    results = []
    
    # 创建一些CPU密集型操作
    def cpu_task(task_id, result_queue, iterations=10000):
        # 准备一些随机数据
        data = os.urandom(1024)
        start_time = time.time_ns()
        
        # 进行一些密集计算
        for i in range(iterations):
            # 混合多种操作以增加CPU工作负载随机性
            data = hashlib.sha256(data + str(i).encode()).digest()
            if i % 100 == 0:
                # 定期收集熵并放入队列
                timestamp = time.time_ns()
                entropy_part = hashlib.sha256(
                    data + 
                    str(timestamp).encode() + 
                    str(task_id).encode() +
                    str(i).encode()
                ).digest()
                result_queue.put((task_id, i, timestamp, entropy_part))
        
        # 计算总耗时
        end_time = time.time_ns()
        elapsed = end_time - start_time
        result_queue.put((task_id, "done", elapsed, data))
    
    # 创建随机内存访问任务
    def memory_task(result_queue):
        # 创建一个大数组
        size = random.randint(500000, 1000000)
        data = bytearray(os.urandom(size))
        
        # 随机访问数组位置
        for _ in range(10000):
            idx = random.randrange(0, size)
            # 读取并修改内存
            value = data[idx]
            data[idx] = (value + 1) % 256
            
            if _ % 1000 == 0:
                # 收集读写延迟作为熵
                timestamp = time.time_ns()
                entropy_part = hashlib.sha256(
                    bytes([value]) + 
                    str(timestamp).encode() + 
                    str(idx).encode()
                ).digest()
                result_queue.put(("memory", idx, timestamp, entropy_part))
    
    # 创建IO任务
    def io_task(result_queue):
        # 找一个临时文件写入随机数据
        temp_filename = f"temp_entropy_{time.time_ns()}.tmp"
        try:
            # 先收集一些系统指标
            cpu_percent = psutil.cpu_percent(interval=0.05)
            memory = psutil.virtual_memory()
            disk = psutil.disk_io_counters()
            network = psutil.net_io_counters()
            
            # 将这些指标转换为字节
            metrics = f"{cpu_percent},{memory.percent},{disk.read_bytes},{disk.write_bytes},{network.bytes_sent},{network.bytes_recv}"
            
            # 写入临时文件
            with open(temp_filename, 'wb') as f:
                f.write(os.urandom(8192))  # 写入8KB随机数据
                f.flush()
                os.fsync(f.fileno())  # 确保数据写入磁盘
            
            # 读取文件并混合IO延迟
            with open(temp_filename, 'rb') as f:
                read_start = time.time_ns()
                data = f.read()
                read_end = time.time_ns()
                
                # 收集IO延迟作为熵
                io_entropy = hashlib.sha256(
                    data + 
                    str(read_end - read_start).encode() + 
                    metrics.encode()
                ).digest()
                
                result_queue.put(("io", read_end - read_start, read_end, io_entropy))
                
        except Exception as e:
            # 如果IO操作失败，使用随机值代替
            result_queue.put(("io_error", str(e), time.time_ns(), os.urandom(32)))
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_filename):
                    os.unlink(temp_filename)
            except:
                pass
    
    # 启动多个线程
    threads = []
    num_threads = min(8, multiprocessing.cpu_count() * 2)  # 使用2倍CPU核心数的线程
    
    for i in range(num_threads):
        t = threading.Thread(target=cpu_task, args=(i, entropy_queue))
        threads.append(t)
        t.start()
    
    # 启动内存和IO线程
    mem_thread = threading.Thread(target=memory_task, args=(entropy_queue,))
    io_thread = threading.Thread(target=io_task, args=(entropy_queue,))
    
    threads.append(mem_thread)
    threads.append(io_thread)
    
    mem_thread.start()
    io_thread.start()
    
    # 收集结果直到获取足够的熵
    timeout = 0.5  # 最长等待0.5秒
    end_time = time.time() + timeout
    
    while time.time() < end_time and len(results) < 50:  # 收集50个样本点
        try:
            result = entropy_queue.get(timeout=timeout/10)
            results.append(result)
        except queue.Empty:
            # 队列为空，可能需要等待更长时间
            pass
    
    # 等待线程完成
    for t in threads:
        t.join(timeout=0.1)  # 最多等待0.1秒
    
    # 组合所有收集到的熵
    all_data = b''
    for result in results:
        # 将结果的所有字段转换为字节并连接
        task_id, iteration, timestamp, data = result
        
        # 转换非字节类型为字节
        task_id_bytes = str(task_id).encode() if not isinstance(task_id, bytes) else task_id
        iteration_bytes = str(iteration).encode() if not isinstance(iteration, bytes) else iteration
        timestamp_bytes = str(timestamp).encode() if not isinstance(timestamp, bytes) else timestamp
        
        # 连接所有字节
        all_data += task_id_bytes + iteration_bytes + timestamp_bytes + data
    
    # 如果收集的数据不足，添加一些随机数据
    if len(all_data) < size * 2:  # 确保有足够的数据进行哈希处理
        all_data += os.urandom(size * 2 - len(all_data))
    
    # 使用SHA-256哈希处理所有收集的数据
    final_entropy = hashlib.sha256(all_data).digest()[:size]
    return final_entropy

def generate_new_key(wordlist, verbose=True, word_count=12, mouse_entropy=None):
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
    
    # 生成熵 (16字节/128位 用于12个单词, 32字节/256位 用于24个单词)
    entropy_size = 32 if word_count == 24 else 16
    random_entropy = secrets.token_bytes(entropy_size)
    
    # 生成1000万个随机字符 (a-z, A-Z, 0-9)
    chars = string.ascii_letters + string.digits
    extra_random = ''.join(secrets.choice(chars) for _ in range(10000000))
    extra_entropy = sha256(extra_random.encode()).digest()[:8]  # 取前8字节
    
    # 1. 添加网络接口信息作为熵源
    try:
        # 获取主机名和IP地址
        hostname = socket.gethostname().encode()
        try:
            ip_address = socket.gethostbyname(hostname).encode()
        except:
            ip_address = b'127.0.0.1'
            
        # 获取MAC地址
        mac_address = uuid.getnode().to_bytes(6, 'big')
        
        # 混合网络信息
        network_entropy = sha256(hostname + ip_address + mac_address).digest()[:8]
    except:
        network_entropy = secrets.token_bytes(8)
    
    # 2. 添加系统信息作为熵源
    try:
        # 系统信息
        system_info = platform.platform().encode()
        python_build = ''.join(platform.python_build()).encode()
        
        # CPU和内存信息
        cpu_percent = str(psutil.cpu_percent()).encode()
        memory_info = str(psutil.virtual_memory()).encode()
        disk_info = str(psutil.disk_usage('/')).encode()
        
        # 混合系统信息
        system_entropy = sha256(system_info + python_build + cpu_percent + memory_info + disk_info).digest()[:8]
    except:
        system_entropy = secrets.token_bytes(8)
    
    # 3. 添加进程信息作为熵源
    try:
        process_id = os.getpid().to_bytes(4, 'big')
        process_entropy = sha256(process_id + str(time.process_time_ns()).encode()).digest()[:8]
    except:
        process_entropy = secrets.token_bytes(8)
    
    # 4. 添加环境变量作为熵源
    try:
        env_str = str(os.environ).encode()
        env_entropy = sha256(env_str).digest()[:8]
    except:
        env_entropy = secrets.token_bytes(8)
    
    # 5. 添加随机延迟作为熵源
    delay_entropy = b''
    for _ in range(8):
        # 随机微秒延迟
        delay = random.uniform(0.001, 0.01)
        time.sleep(delay)
        delay_ns = int(delay * 1_000_000_000)
        delay_entropy += (delay_ns & 0xFF).to_bytes(1, 'big')
    
    # 6. 使用新的线程竞争熵替代鼠标熵
    thread_entropy = collect_thread_entropy(8)  # 收集8字节的线程竞争熵
    
    # 7. 添加文件系统熵源
    try:
        # 获取临时目录和系统目录的文件统计信息
        file_entropy = b''
        dirs_to_scan = ['/tmp', '/var/log', '/etc'] if platform.system() != 'Windows' else ['C:\\Windows\\Temp', 'C:\\Windows\\System32\\config']
        
        # 选择一个存在的目录
        target_dir = None
        for d in dirs_to_scan:
            if os.path.exists(d) and os.path.isdir(d):
                target_dir = d
                break
        
        if target_dir:
            # 快速列出目录内容并获取文件大小、修改时间等元数据
            file_data = []
            for entry in os.scandir(target_dir):
                try:
                    stats = entry.stat()
                    # 收集文件大小、修改时间、inode号等
                    file_data.append(stats.st_size)
                    file_data.append(stats.st_mtime_ns)
                    file_data.append(stats.st_ino)
                    # 只收集最多50个文件的信息，保证速度
                    if len(file_data) > 150:
                        break
                except (PermissionError, FileNotFoundError):
                    pass
            
            # 将收集到的数据转换为字节
            file_info_str = ''.join(str(x) for x in file_data).encode()
            file_entropy = sha256(file_info_str).digest()[:8]
        else:
            # 如果找不到合适的目录，使用随机字节
            file_entropy = secrets.token_bytes(8)
    except:
        file_entropy = secrets.token_bytes(8)
    
    # 混合所有熵源
    if entropy_size == 16:
        # 修改现有的混合逻辑，添加线程竞争熵源替代鼠标熵源
        mixed_entropy = bytes([
            a ^ b ^ c ^ d ^ e ^ f ^ g ^ h ^ i ^ j ^ k ^ l ^ m
            for a, b, c, d, e, f, g, h, i, j, k, l, m in zip(
                time_bytes + time_bytes,
                perf_counter_bytes + perf_counter_bytes,
                process_time_bytes + process_time_bytes,
                sys_random_bytes + sys_random_bytes,
                random_entropy,
                extra_entropy + extra_entropy,
                network_entropy + network_entropy,
                system_entropy + system_entropy,
                process_entropy + process_entropy,
                env_entropy + env_entropy,
                delay_entropy + delay_entropy,
                thread_entropy + thread_entropy,  # 使用线程竞争熵替代鼠标熵
                file_entropy + file_entropy
            )
        ])
    else:  # 对于24个单词，需要更多的熵
        # 创建足够长的字节序列
        time_entropy = time_bytes * 4
        perf_entropy = perf_counter_bytes * 4
        proc_entropy = process_time_bytes * 4
        sys_entropy = sys_random_bytes * 4
        extra_entropy_extended = extra_entropy * 4
        network_entropy_extended = network_entropy * 4
        system_entropy_extended = system_entropy * 4
        process_entropy_extended = process_entropy * 4
        env_entropy_extended = env_entropy * 4
        delay_entropy_extended = delay_entropy * 4
        thread_entropy_extended = thread_entropy * 4  # 线程竞争熵
        file_entropy_extended = file_entropy * 4
        
        # 确保所有序列至少有32字节长
        mixed_entropy = bytes([
            a ^ b ^ c ^ d ^ e ^ f ^ g ^ h ^ i ^ j ^ k ^ l ^ m
            for a, b, c, d, e, f, g, h, i, j, k, l, m in zip(
                time_entropy[:32],
                perf_entropy[:32],
                proc_entropy[:32],
                sys_entropy[:32],
                random_entropy,
                extra_entropy_extended[:32],
                network_entropy_extended[:32],
                system_entropy_extended[:32],
                process_entropy_extended[:32],
                env_entropy_extended[:32],
                delay_entropy_extended[:32],
                thread_entropy_extended[:32],  # 使用线程竞争熵替代鼠标熵
                file_entropy_extended[:32]
            )
        ])
    
    # 额外的SHA256哈希来进一步混合熵
    entropy = sha256(mixed_entropy).digest()[:entropy_size]

    if verbose:
        print(f"\n使用时间生成: {current_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
        print(f"性能计数器: {time.perf_counter()}")
        print(f"进程时间: {time.process_time()}")
        print(f"额外随机字符长度: {len(extra_random)}")
        print("已添加线程竞争熵")  # 更新提示
        print("已添加文件系统熵")
        print(f"生成 {word_count} 个单词的助记词")

    # 计算校验和
    entropy_bits = bin(int.from_bytes(entropy, 'big'))[2:].zfill(entropy_size * 8)
    checksum_bits_count = entropy_size * 8 // 32  # 12个单词为4位，24个单词为8位
    checksum = bin(int(sha256(entropy).hexdigest(), 16))[2:].zfill(256)[:checksum_bits_count]

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

def validate_word(word, wordlist):
    """验证单词是否在BIP39词表中"""
    return word in wordlist

def generate_custom_mnemonic(wordlist, custom_words, positions):
    """
    生成包含自定义词的助记词
    
    Args:
        wordlist: BIP39词表
        custom_words: 自定义词列表
        positions: 自定义词要插入的位置列表 (从1开始)
    """
    # 验证输入
    if not all(1 <= p <= 12 for p in positions):
        raise ValueError("位置必须在1到12之间")
    if len(custom_words) != len(positions):
        raise ValueError("自定义词的数量必须与位置数量相同")
    if len(set(positions)) != len(positions):
        raise ValueError("位置不能重复")
    if not all(validate_word(word, wordlist) for word in custom_words):
        raise ValueError("所有自定义词必须在BIP39词表中")
    
    # 获取当前时间和基础熵
    current_time = datetime.datetime.now()
    max_attempts = 1000  # 设置最大尝试次数
    attempt = 0
    
    print("\n正在寻找符合条件的助记词...")
    while attempt < max_attempts:
        attempt += 1
        # 生成基础助记词，禁用详细输出
        mnemonic, _ = generate_new_key(wordlist, verbose=False)
        words = mnemonic.split()
        
        # 在指定位置插入自定义词
        for word, pos in zip(custom_words, positions):
            words[pos-1] = word
            
        # 验证新的助记词是否有效
        new_mnemonic = ' '.join(words)
        if verify_mnemonic(new_mnemonic, wordlist):
            return new_mnemonic, current_time
    
    raise ValueError("无法生成符合条件的助记词，请尝试使用不同的自定义词")

def verify_mnemonic(mnemonic, wordlist):
    """验证助记词是否符合BIP39标准"""
    words = mnemonic.split()
    word_count = len(words)
    
    if word_count not in [12, 24]:
        return False
    
    # 确定熵大小
    entropy_size = 32 if word_count == 24 else 16
    checksum_bits_count = entropy_size * 8 // 32  # 12个单词为4位，24个单词为8位
        
    # 将助记词转换回二进制
    word_indexes = [wordlist.index(word) for word in words]
    bits = ''.join(bin(index)[2:].zfill(11) for index in word_indexes)
    
    # 分离熵和校验和
    entropy_bits = bits[:entropy_size * 8]
    checksum_bits = bits[entropy_size * 8:]
    
    # 验证校验和
    entropy_bytes = int(entropy_bits, 2).to_bytes(entropy_size, 'big')
    checksum = bin(int(sha256(entropy_bytes).hexdigest(), 16))[2:].zfill(256)[:checksum_bits_count]
    
    return checksum_bits == checksum

def generate_from_entropy(wordlist, entropy_input, word_count=12):
    """
    从提供的熵生成助记词
    
    Args:
        wordlist: BIP39词表
        entropy_input: 输入熵（字节）
        word_count: 助记词单词数量 (12 或 24)
    """
    current_time = datetime.datetime.now()
    
    # 确定熵大小
    entropy_size = 32 if word_count == 24 else 16
    
    # 使用SHA256处理输入熵
    entropy = sha256(entropy_input).digest()[:entropy_size]
    
    # 计算校验和
    entropy_bits = bin(int.from_bytes(entropy, 'big'))[2:].zfill(entropy_size * 8)
    checksum_bits_count = entropy_size * 8 // 32  # 12个单词为4位，24个单词为8位
    checksum = bin(int(sha256(entropy).hexdigest(), 16))[2:].zfill(256)[:checksum_bits_count]
    
    # 组合熵和校验和
    combined_bits = entropy_bits + checksum
    
    # 将比特分成11位的组，并转换为助记词
    indexes = [int(combined_bits[i:i+11], 2) for i in range(0, len(combined_bits), 11)]
    mnemonic = ' '.join(wordlist[index] for index in indexes)
    
    return mnemonic, current_time

def main():
    wordlist = load_wordlist()
    
    print("\nBIP39助记词和私钥生成器")
    print("------------------------")
    
    choice = input("\n选择模式:\n1. 生成随机助记词\n2. 生成自定义助记词\n请输入(1或2): ")
    
    if choice == '1':
        mnemonic, current_time = generate_new_key(wordlist)
    elif choice == '2':
        try:
            num_custom = int(input("\n请输入要自定义的词数量: "))
            if not 1 <= num_custom <= 12:
                raise ValueError("自定义词数量必须在1到12之间")
            
            custom_words = []
            positions = []
            
            print("\n请输入自定义词和位置(位置为1-12):")
            for i in range(num_custom):
                word = input(f"第{i+1}个自定义词: ").strip()
                pos = int(input(f"第{i+1}个词的位置(1-12): "))
                custom_words.append(word)
                positions.append(pos)
            
            mnemonic, current_time = generate_custom_mnemonic(wordlist, custom_words, positions)
        except ValueError as e:
            print(f"\n错误: {str(e)}")
            return
    else:
        print("\n无效的选择")
        return
    
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