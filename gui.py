import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import generator
import os
import time
import hashlib

class MnemonicGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("BIP39助记词生成器")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # 确保english.txt文件存在
        if not os.path.exists('english.txt'):
            messagebox.showerror("错误", "找不到english.txt文件，请确保它与程序在同一目录下。")
            root.destroy()
            return
            
        # 加载词表
        self.wordlist = generator.load_wordlist()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_label = ttk.Label(self.main_frame, text="BIP39助记词和私钥生成器", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 随机生成框架
        self.random_frame = ttk.Frame(self.main_frame)
        self.random_frame.pack(fill=tk.BOTH, expand=True)
        
        # 设置随机生成界面
        self.setup_random_ui()
        
        # 结果显示区域
        self.result_frame = ttk.LabelFrame(self.main_frame, text="生成结果", padding="10")
        self.result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 助记词结果
        ttk.Label(self.result_frame, text="助记词:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.mnemonic_text = scrolledtext.ScrolledText(self.result_frame, height=3, width=70, wrap=tk.WORD)
        self.mnemonic_text.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        # 种子结果
        ttk.Label(self.result_frame, text="种子 (hex):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.seed_text = scrolledtext.ScrolledText(self.result_frame, height=2, width=70, wrap=tk.WORD)
        self.seed_text.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # 私钥结果
        ttk.Label(self.result_frame, text="主私钥 (hex):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.private_key_text = scrolledtext.ScrolledText(self.result_frame, height=2, width=70, wrap=tk.WORD)
        self.private_key_text.grid(row=2, column=1, sticky=tk.EW, pady=5)
        
        # WIF格式私钥
        ttk.Label(self.result_frame, text="WIF格式私钥:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.wif_text = scrolledtext.ScrolledText(self.result_frame, height=2, width=70, wrap=tk.WORD)
        self.wif_text.grid(row=3, column=1, sticky=tk.EW, pady=5)
        
        # 设置列权重
        self.result_frame.columnconfigure(1, weight=1)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # 设置所有文本框为只读
        for text_widget in [self.mnemonic_text, self.seed_text, self.private_key_text, self.wif_text]:
            text_widget.config(state=tk.DISABLED)
    
    def setup_random_ui(self):
        # 随机生成界面内容
        frame = ttk.Frame(self.random_frame, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        info_label = ttk.Label(frame, text="选择助记词长度并点击按钮生成随机助记词", font=("Arial", 10))
        info_label.pack(pady=(0, 20))
        
        # 助记词长度选择
        length_frame = ttk.Frame(frame)
        length_frame.pack(pady=10)
        
        self.mnemonic_length = tk.IntVar(value=12)
        ttk.Radiobutton(length_frame, text="12个单词", variable=self.mnemonic_length, value=12).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(length_frame, text="24个单词", variable=self.mnemonic_length, value=24).pack(side=tk.LEFT, padx=10)
        
        # 进度条
        progress_frame = ttk.Frame(frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(progress_frame, text="生成进度:").pack(side=tk.LEFT, padx=(0, 10))
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 生成按钮
        generate_button = ttk.Button(frame, text="生成随机助记词", command=self.generate_random)
        generate_button.pack(pady=20)
    
    def generate_random(self):
        self.status_var.set("正在生成随机助记词...")
        self.progress_var.set(0)
        self.root.update()
        
        # 在单独的线程中运行生成过程
        word_count = self.mnemonic_length.get()
        threading.Thread(target=self._generate_random, args=(word_count,), daemon=True).start()
    
    def _generate_random(self, word_count):
        try:
            # 模拟进度
            for i in range(1, 101):
                time.sleep(0.02)  # 模拟生成过程
                self.root.after(0, lambda i=i: self.progress_var.set(i))
                if i == 25:
                    self.root.after(0, lambda: self.status_var.set("正在收集系统熵..."))
                elif i == 50:
                    self.root.after(0, lambda: self.status_var.set("正在生成随机字符..."))
                elif i == 75:
                    self.root.after(0, lambda: self.status_var.set("正在计算助记词..."))
            
            # 实际生成助记词，不再传递鼠标熵数据
            mnemonic, current_time = generator.generate_new_key(self.wordlist, word_count=word_count)
            seed, master_private_key = generator.mnemonic_to_private_key(mnemonic, current_time)
            wif = generator.to_wif(master_private_key)
            
            # 更新UI（必须在主线程中进行）
            self.root.after(0, lambda: self.update_results(mnemonic, seed, master_private_key, wif))
            self.root.after(0, lambda: self.status_var.set("随机助记词生成完成"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"生成过程中出错: {str(e)}"))
            self.root.after(0, lambda: self.status_var.set("生成失败"))
    
    def update_results(self, mnemonic, seed, master_private_key, wif):
        # 更新结果文本框
        for text_widget, content in [
            (self.mnemonic_text, mnemonic),
            (self.seed_text, generator.binascii.hexlify(seed).decode()),
            (self.private_key_text, generator.binascii.hexlify(master_private_key).decode()),
            (self.wif_text, wif)
        ]:
            text_widget.config(state=tk.NORMAL)
            text_widget.delete(1.0, tk.END)
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = MnemonicGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 