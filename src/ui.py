# ui.py
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
import sys

class ImageNormalizationUI:
    def __init__(self, master):
        self.master = master
        self.master.title("图像归一化处理")

        # 输入图像1
        self.label_image1 = tk.Label(master, text="选择输入图像1")
        self.label_image1.pack()
        self.button_image1 = tk.Button(master, text="浏览", command=self.select_image1)
        self.button_image1.pack()
        self.entry_image1 = tk.Entry(master)
        self.entry_image1.pack()

        # 输入图像2
        self.label_image2 = tk.Label(master, text="选择输入图像2")
        self.label_image2.pack()
        self.button_image2 = tk.Button(master, text="浏览", command=self.select_image2)
        self.button_image2.pack()
        self.entry_image2 = tk.Entry(master)
        self.entry_image2.pack()


        # ===== 分位数设置 =====
        # 标题
        self.label_section_norm = tk.Label(master, text="归一化分位数设置", font=("Arial", 10, "bold"))
        self.label_section_norm.pack()

        # 归一化分位数
        self.label_q_low = tk.Label(master, text="归一化 - 低分位数")
        self.label_q_low.pack()
        self.entry_q_low = tk.Entry(master)
        self.entry_q_low.insert(0, "1")  # 默认值为1
        self.entry_q_low.pack()

        self.label_q_high = tk.Label(master, text="归一化 - 高分位数")
        self.label_q_high.pack()
        self.entry_q_high = tk.Entry(master)
        self.entry_q_high.insert(0, "99")  # 默认值为99
        self.entry_q_high.pack()

        # 标题
        self.label_section_color = tk.Label(master, text="色彩校正分位数设置", font=("Arial", 10, "bold"))
        self.label_section_color.pack()

        # 色彩校正分位数
        self.label_q_low_color = tk.Label(master, text="色彩校正 - 低分位数")
        self.label_q_low_color.pack()
        self.entry_q_low_color = tk.Entry(master)
        self.entry_q_low_color.insert(0, "2")  # 默认值为2
        self.entry_q_low_color.pack()

        self.label_q_high_color = tk.Label(master, text="色彩校正 - 高分位数")
        self.label_q_high_color.pack()
        self.entry_q_high_color = tk.Entry(master)
        self.entry_q_high_color.insert(0, "98")  # 默认值为98
        self.entry_q_high_color.pack()

        # 输出路径
        self.label_output = tk.Label(master, text="选择输出路径")
        self.label_output.pack()
        self.button_output = tk.Button(master, text="浏览", command=self.select_output)
        self.button_output.pack()
        self.entry_output = tk.Entry(master)
        self.entry_output.pack()

        # 提交按钮
        self.button_submit = tk.Button(self.master, text="提交", command=self.submit)
        self.button_submit.pack()

        # 进度条
        self.progress = ttk.Progressbar(self.master, orient="horizontal", length=300, mode="determinate")
        # mode="determinate" 是确定进度的那种（我们可以控制它的值）
        self.progress.pack(pady=5)  # pack(pady=5) 是加了一点上下间距

        # 日志输出区
        self.log_text = tk.Text(self.master, height=10, width=70)
        self.log_text.pack()

        # 重定向 print 输出。print() 内容（sys.stdout），全部重定向到了 self.log_text 控件里；
        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)



    def select_image1(self):
        file_path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tif")])
        self.entry_image1.delete(0, tk.END)
        self.entry_image1.insert(0, file_path)

    def select_image2(self):
        file_path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tif")])
        self.entry_image2.delete(0, tk.END)
        self.entry_image2.insert(0, file_path)

    def select_output(self):
        output_path = filedialog.askdirectory()
        self.entry_output.delete(0, tk.END)
        self.entry_output.insert(0, output_path)

    def submit(self):
        # 获取用户输入
        try:
            # 获取用户输入的路径和分位数
            image1_path = self.entry_image1.get()
            image2_path = self.entry_image2.get()
            output_path = self.entry_output.get()
            q_low = self.entry_q_low.get()
            q_high = self.entry_q_high.get()
            q_low_color = self.entry_q_low_color.get()
            q_high_color = self.entry_q_high_color.get()

            # 校验路径是否有效
            if not image1_path or not image2_path or not output_path:
                messagebox.showerror("错误", "请输入所有必要的信息！")
                return

            if q_low >= q_high:
                messagebox.showerror("错误", "低分位数应小于高分位数！")
                return

            if q_low_color >= q_high_color:
                messagebox.showerror("错误", "低分位数应小于高分位数！")
                return

            # 如果一切正常，返回路径和分位数
            self.master.quit()  # 关闭界面
            return image1_path, image2_path, output_path, q_low, q_high, q_low_color, q_high_color

        except ValueError:
            messagebox.showerror("错误", "请输入有效的分位数！")
            return

    def set_progress(self, value):
        # 设置进度条
        self.progress["value"] = value
        self.progress.update()


class TextRedirector(object):
    def __init__(self, text_widget):
        self.text_widget = text_widget  # 后面写入的内容都会加到这个控件里。

    # 这个方法就是 print() 真正会调用的：
    def write(self, str):
        self.text_widget.insert(tk.END, str)
        self.text_widget.see(tk.END)  # 自动滚动到底部
        self.text_widget.update()

    # 这个是为了兼容print(..., flush=True)这样的调用。
    def flush(self):
        pass  # 兼容 print()

