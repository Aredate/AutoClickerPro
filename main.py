import customtkinter as ctk
import pyautogui
import time
import threading
import random
from tkinter import messagebox

# 设置外观模式 (System, Dark, Light)
ctk.set_appearance_mode("Dark") 
ctk.set_default_color_theme("blue") 

class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- 窗口基础设置 ---
        self.title("AutoClicker Pro - 自动化点击助手")
        self.geometry("700x550")
        self.resizable(False, False)

        # --- 数据变量 ---
        self.targets = [] # 存储坐标元组 [(x1, y1), (x2, y2), ...]
        self.is_running = False
        self.thread = None

        # --- 布局配置 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= 左侧：参数设置区 =================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="参数配置", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # 参数输入辅助函数
        def create_param_entry(label_text, row, default_val):
            label = ctk.CTkLabel(self.sidebar_frame, text=label_text, anchor="w")
            label.grid(row=row, column=0, padx=20, pady=(10, 0), sticky="w")
            entry = ctk.CTkEntry(self.sidebar_frame, placeholder_text=str(default_val))
            entry.insert(0, str(default_val))
            entry.grid(row=row+1, column=0, padx=20, pady=(0, 5), sticky="ew")
            return entry

        self.entry_move_base = create_param_entry("移动基准时间 (秒)", 1, 0.5)
        self.entry_move_rand = create_param_entry("移动随机偏差 (+/-秒)", 3, 0.1)
        self.entry_interval_base = create_param_entry("点击后等待基准 (秒)", 5, 0.5)
        self.entry_interval_rand = create_param_entry("点击后等待随机 (+/-秒)", 7, 0.2)
        self.entry_jitter = create_param_entry("坐标随机偏移 (像素)", 9, 5)

        # 循环设置
        self.loop_var = ctk.BooleanVar(value=True)
        self.loop_switch = ctk.CTkSwitch(self.sidebar_frame, text="无限循环执行", variable=self.loop_var)
        self.loop_switch.grid(row=11, column=0, padx=20, pady=20, sticky="ns")

        # ================= 右侧：主操作区 =================
        
        # --- 1. 状态显示 ---
        self.status_label = ctk.CTkLabel(self, text="就绪 - 请添加目标点", font=ctk.CTkFont(size=16))
        self.status_label.grid(row=0, column=1, padx=20, pady=(20, 0), sticky="w")

        # --- 2. 坐标列表 (Scrollable Frame) ---
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="点击目标序列")
        self.list_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        self.list_frame.grid_columnconfigure(0, weight=1)

        # --- 3. 按钮操作区 ---
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.grid(row=2, column=1, padx=20, pady=20, sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)

        self.btn_add = ctk.CTkButton(self.button_frame, text="+ 获取新坐标 (F2)", command=self.start_pick_coordinate, fg_color="#2CC985", hover_color="#229A65")
        self.btn_add.grid(row=0, column=0, padx=5, sticky="ew")

        self.btn_clear = ctk.CTkButton(self.button_frame, text="清空列表", command=self.clear_targets, fg_color="#D63D3D", hover_color="#A82A2A")
        self.btn_clear.grid(row=0, column=1, padx=5, sticky="ew")

        self.btn_start = ctk.CTkButton(self.button_frame, text="▶ 开始运行", command=self.toggle_automation, height=40, font=ctk.CTkFont(size=15, weight="bold"))
        self.btn_start.grid(row=0, column=2, padx=5, sticky="ew")

        # 绑定快捷键用于快速取点 (这里为了简化，使用延时取点逻辑，快捷键监听需要额外库，暂用按钮触发)
        
    def start_pick_coordinate(self):
        """倒计时3秒后获取当前鼠标位置"""
        self.btn_add.configure(state="disabled", text="3秒后记录...")
        self.status_label.configure(text="⏳ 请将鼠标移动到目标位置，3秒后自动记录...", text_color="orange")
        self.update()
        
        # 使用线程倒计时，避免界面卡死
        threading.Thread(target=self._pick_logic, daemon=True).start()

    def _pick_logic(self):
        for i in range(3, 0, -1):
            self.btn_add.configure(text=f"{i} 秒后记录...")
            time.sleep(1)
        
        x, y = pyautogui.position()
        self.targets.append((x, y))
        
        # 回到主线程更新UI
        self.after(0, self._refresh_list)
        self.after(0, lambda: self.btn_add.configure(state="normal", text="+ 获取新坐标 (F2)"))
        self.after(0, lambda: self.status_label.configure(text=f"✅ 已添加坐标: ({x}, {y})", text_color="white"))

    def _refresh_list(self):
        """刷新右侧的坐标列表显示"""
        # 清空当前列表组件
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        for idx, (x, y) in enumerate(self.targets):
            row_frame = ctk.CTkFrame(self.list_frame)
            row_frame.pack(fill="x", pady=2)
            
            lbl = ctk.CTkLabel(row_frame, text=f"步骤 {idx+1}:  X={x}, Y={y}", anchor="w")
            lbl.pack(side="left", padx=10)
            
            # 删除单个按钮
            del_btn = ctk.CTkButton(row_frame, text="×", width=30, fg_color="#555", hover_color="#333",
                                    command=lambda i=idx: self.delete_item(i))
            del_btn.pack(side="right", padx=5, pady=5)

    def delete_item(self, index):
        if 0 <= index < len(self.targets):
            del self.targets[index]
            self._refresh_list()

    def clear_targets(self):
        self.targets = []
        self._refresh_list()
        self.status_label.configure(text="列表已清空")

    def toggle_automation(self):
        """开始/停止 切换逻辑"""
        if self.is_running:
            # 停止逻辑
            self.is_running = False
            self.btn_start.configure(text="▶ 开始运行", fg_color="#3B8ED0") # 恢复蓝色
            self.status_label.configure(text="⏹ 已停止", text_color="white")
            self.unlock_inputs()
        else:
            # 开始逻辑
            if not self.targets:
                messagebox.showwarning("提示", "请先添加至少一个坐标点！")
                return
            
            self.is_running = True
            self.btn_start.configure(text="■ 停止运行", fg_color="#D63D3D") # 变红
            self.lock_inputs()
            
            # 开启新线程运行自动化脚本
            self.thread = threading.Thread(target=self.run_automation_logic, daemon=True)
            self.thread.start()

    def lock_inputs(self):
        """运行时锁定输入框防止修改"""
        self.btn_add.configure(state="disabled")
        self.btn_clear.configure(state="disabled")
        # 也可以锁定输入框...

    def unlock_inputs(self):
        self.btn_add.configure(state="normal")
        self.btn_clear.configure(state="normal")

    def get_float_val(self, entry_widget):
        try:
            return float(entry_widget.get())
        except ValueError:
            return 0.0

    def get_int_val(self, entry_widget):
        try:
            return int(entry_widget.get())
        except ValueError:
            return 0

    # ================= 核心自动化逻辑 (线程中运行) =================
    # --- 新增：智能等待函数 (放在类里面) ---
    def smart_sleep(self, seconds):
        """
        替代 time.sleep。
        将长时间的等待切分成 0.1 秒的小段。
        每隔 0.1 秒检查一次 self.is_running 状态。
        一旦检测到停止信号，立即结束等待。
        """
        end_time = time.time() + seconds
        while time.time() < end_time:
            if not self.is_running: 
                return False # 返回 False 表示被强制中断
            
            # 计算剩余时间，如果小于0.1就睡剩余时间，否则睡0.1
            remaining = end_time - time.time()
            time.sleep(min(0.1, max(0, remaining)))
        
        return True # 返回 True 表示正常睡完了全程

    # --- 修改：运行逻辑 ---
    def run_automation_logic(self):
        # 获取参数
        move_base = self.get_float_val(self.entry_move_base)
        move_rand = self.get_float_val(self.entry_move_rand)
        int_base = self.get_float_val(self.entry_interval_base)
        int_rand = self.get_float_val(self.entry_interval_rand)
        jitter = self.get_int_val(self.entry_jitter)
        
        self.after(0, lambda: self.status_label.configure(text="🚀 脚本运行中... (按 '停止' 结束)", text_color="#2CC985"))
        
        try:
            while self.is_running:
                # 遍历所有目标点
                for i, (tx, ty) in enumerate(self.targets):
                    # 1. 每次大动作前都检查是否停止
                    if not self.is_running: break

                    self.after(0, lambda idx=i: self.status_label.configure(text=f"正在前往步骤 {idx+1}..."))

                    # --- 计算随机参数 ---
                    x = tx + random.randint(-jitter, jitter)
                    y = ty + random.randint(-jitter, jitter)
                    dur = max(0.05, move_base + random.uniform(-move_rand, move_rand))
                    wait = max(0.01, int_base + random.uniform(-int_rand, int_rand))

                    # --- 执行移动 ---
                    # 注意：pyautogui.moveTo 本身是阻塞的，如果移动时间(dur)设得特别长，
                    # 这里依然会卡住直到移动结束。通常 dur 很短(0.x秒)，所以影响不大。
                    pyautogui.moveTo(x, y, duration=dur)
                    
                    # 2. 移动完立刻检查
                    if not self.is_running: break
                    
                    # --- 执行点击 ---
                    pyautogui.click()
                    print(f"Clicked at ({x}, {y})")

                    # 3. 智能等待 (这里是关键修改)
                    # 如果你在等待期间点了停止，smart_sleep 会返回 False，我们就直接 break
                    if not self.smart_sleep(wait):
                        break

                # 检查是否循环
                if not self.loop_var.get():
                    break
                
                # 轮次间隔 (同样使用智能等待)
                if self.is_running:
                    loop_wait = random.uniform(0.5, 1.5)
                    if not self.smart_sleep(loop_wait):
                        break

        except pyautogui.FailSafeException:
            self.after(0, lambda: messagebox.showerror("错误", "触发鼠标安全保护 (鼠标移动到角落)！"))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # 无论如何退出的，最后都要重置界面状态
            self.is_running = False
            # 使用 after 确保在主线程更新 UI
            self.after(0, lambda: self._reset_ui_state())

    def _reset_ui_state(self):
        """重置按钮样式的辅助函数"""
        self.btn_start.configure(text="▶ 开始运行", fg_color="#3B8ED0")
        self.status_label.configure(text="⏹ 已停止", text_color="white")
        self.unlock_inputs()

if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()