import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext
from tkinter.ttk import Progressbar, Style, Combobox  # 导入Combobox
import logging


def resource_path(relative_path):
    """获取打包后资源文件的绝对路径"""
    try:
        # 如果是打包后的环境，使用临时目录
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境，直接使用当前路径
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 导入命令行工具中的核心逻辑函数
from docker_image_puller import pull_image_logic

# 配置日志记录器
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# 定义一个函数来运行命令行工具的逻辑
def run_pull(image, registry, arch, log_text, layer_progress_bar, overall_progress_bar):
    def log_callback(message):
        log_text.config(state="normal")
        log_text.insert(tk.END, message)
        log_text.config(state="disabled")
        log_text.see(tk.END)  # 自动滚动到底部

    def update_layer_progress(value):
        layer_progress_bar["value"] = value
        layer_progress_bar.update()

    def update_overall_progress(value):
        overall_progress_bar["value"] = value
        overall_progress_bar.update()

    try:
        log_callback(f"开始拉取镜像：{image}\n")
        pull_image_logic(
            image, 
            registry, 
            arch, 
            log_callback=log_callback, 
            layer_progress_callback=update_layer_progress, 
            overall_progress_callback=update_overall_progress
        )
        log_callback("镜像拉取完成！\n")
    except Exception as e:
        log_callback(f"发生错误：{e}\n")
        logger.error(f"程序运行过程中发生异常: {e}")
    finally:
        layer_progress_bar["value"] = 0  # 重置进度条
        overall_progress_bar["value"] = 0  # 重置进度条

# 定义 GUI 类
class DockerPullerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Docker 镜像拉取打包工具 v1.0.7")
        self.root.geometry("600x650")  # 调整窗口高度以容纳两条进度条
        self.root.configure(bg="#f0f0f0")  # 设置背景颜色

        # 使用 resource_path 函数动态获取图标文件路径
        favicon_path = resource_path("logo.ico")  # 动态路径
        if os.path.exists(favicon_path):
            self.root.iconbitmap(favicon_path)  # 设置窗口左上角图标
        else:
            logger.warning("logo.ico 文件未找到！")

        # 设置样式
        style = Style()
        style.theme_use("default")
        style.configure("TLabel", font=("SimSun", 12), background="#f0f0f0")
        style.configure("TEntry", font=("SimSun", 12))
        style.configure("TButton", font=("SimSun", 12), background="#4CAF50", foreground="white")
        style.configure("TProgressbar", thickness=20)
        style.configure("TCombobox", font=("SimSun", 12))  # 设置Combobox样式

        # 设置网格权重，使布局响应式
        self.root.grid_columnconfigure(0, weight=0)  # 左侧列权重为0
        self.root.grid_columnconfigure(1, weight=1)  # 右侧列权重为1，进度条所在列
        self.root.grid_rowconfigure(4, weight=1)  # 日志区域占更多空间

        # 创建输入框和标签
        tk.Label(root, text="Docker 镜像名称：", bg="#f0f0f0", font=("SimSun", 12)).grid(row=0, column=0, padx=(20, 5), pady=10, sticky="e")
        self.image_entry = tk.Entry(root, font=("SimSun", 12), width=30)
        self.image_entry.grid(row=0, column=1, padx=(5, 20), pady=10, sticky="w")

        tk.Label(root, text="Docker 仓库地址：", bg="#f0f0f0", font=("SimSun", 12)).grid(row=1, column=0, padx=(20, 5), pady=10, sticky="e")
        self.registry_entry = tk.Entry(root, font=("SimSun", 12), width=30)
        self.registry_entry.grid(row=1, column=1, padx=(5, 20), pady=10, sticky="w")
        self.registry_entry.insert(0, "registry.hub.docker.com")  # 默认值

        tk.Label(root, text="架构：", bg="#f0f0f0", font=("SimSun", 12)).grid(row=2, column=0, padx=(20, 5), pady=10, sticky="e")
        self.arch_var = tk.StringVar(root)
        self.arch_var.set("amd64")  # 默认值
        self.arch_menu = Combobox(root, textvariable=self.arch_var, values=["amd64", "arm64", "arm", "i386"], state="readonly", font=("SimSun", 12))
        self.arch_menu.grid(row=2, column=1, padx=(5, 20), pady=10, sticky="w")

        # 创建按钮
        self.pull_button = tk.Button(root, text="拉取镜像", command=self.pull_image, bg="#4CAF50", fg="black", font=("SimSun", 18, "bold"), width=20)
        self.pull_button.grid(row=3, column=0, columnspan=2, pady=20, padx=20, sticky="nsew")

        # 创建复位按钮
        self.reset_button = tk.Button(root, text="复位", command=self.reset_fields, bg="#0bbcc9", fg="black", font=("SimSun", 18, "bold"), width=20)
        self.reset_button.grid(row=7, column=0, columnspan=2, pady=20, padx=20, sticky="nsew")

        # 创建日志显示区域
        self.log_text = scrolledtext.ScrolledText(root, height=10, state="disabled", bg="#ffffff", font=("SimSun", 13))
        self.log_text.grid(row=4, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")

        # 创建进度条和标签
        tk.Label(root, text="当前层进度：", bg="#f0f0f0", font=("SimSun", 12)).grid(row=5, column=0, padx=(20, 5), pady=5, sticky="e")
        self.layer_progress_bar = Progressbar(root, orient="horizontal", length=400, mode="determinate", style="TProgressbar")
        self.layer_progress_bar.grid(row=5, column=1, padx=(5, 20), pady=5, sticky="ew")  # 水平居中

        tk.Label(root, text="总体进度：", bg="#f0f0f0", font=("SimSun", 12)).grid(row=6, column=0, padx=(20, 5), pady=5, sticky="e")
        self.overall_progress_bar = Progressbar(root, orient="horizontal", length=400, mode="determinate", style="TProgressbar")
        self.overall_progress_bar.grid(row=6, column=1, padx=(5, 20), pady=5, sticky="ew")  # 水平居中

    def pull_image(self):
        """拉取镜像的逻辑"""
        image = self.image_entry.get().strip()
        registry = self.registry_entry.get().strip()
        arch = self.arch_var.get().strip()

        if not image:
            messagebox.showerror("错误", "镜像名称不能为空！")
            return

        # 清空日志区域
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        # 使用线程运行拉取逻辑，避免阻塞 GUI
        threading.Thread(
            target=run_pull, 
            args=(image, registry, arch, self.log_text, self.layer_progress_bar, self.overall_progress_bar)
        ).start()

    def reset_fields(self):
        """复位按钮的逻辑"""
        # 清空输入框
        self.image_entry.delete(0, tk.END)
        self.registry_entry.delete(0, tk.END)
        self.registry_entry.insert(0, "registry.hub.docker.com")  # 恢复默认仓库地址
        self.arch_var.set("amd64")  # 恢复默认架构

        # 清空日志区域
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")

        # 重置进度条
        self.layer_progress_bar["value"] = 0
        self.overall_progress_bar["value"] = 0


if __name__ == "__main__":
    root = tk.Tk()
    app = DockerPullerGUI(root)
    root.mainloop()