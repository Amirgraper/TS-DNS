import os
import subprocess
import re
import threading
import queue
import customtkinter as ctk
from ping3 import ping
import ctypes
import sys

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

class HoverButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        self.default_fg_color = kwargs.pop('fg_color', '#444444')
        self.default_text_color = kwargs.pop('text_color', '#FFFFFF')
        self.hover_fg_color = kwargs.pop('hover_color', '#FF0000')
        self.hover_text_color = kwargs.pop('hover_text_color', '#000000')
        self.is_active = kwargs.pop('is_active', True)
        super().__init__(*args, fg_color=self.default_fg_color, text_color=self.default_text_color, **kwargs)
        if self.is_active:
            self.bind('<Enter>', self.on_enter)
            self.bind('<Leave>', self.on_leave)

    def on_enter(self, event):
        if self.is_active:
            self.configure(fg_color=self.hover_fg_color, text_color=self.hover_text_color)

    def on_leave(self, event):
        if self.is_active:
            self.configure(fg_color=self.default_fg_color, text_color=self.default_text_color)

class DNSChangerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry('650x400')
        self.title('TS-DNS')
        self.configure(bg='#333333')
        self.resizable(False, False)

        self.icon_path = os.path.join(os.path.dirname(__file__), 'Assets', 'icon.ico')
        self.set_icon()

        self.libraries_path = os.path.join(os.path.dirname(__file__), 'libraries')
        self.scripts = [file for file in os.listdir(self.libraries_path) if file.endswith('.ps1')]
        self.current_page = 0
        self.queue = queue.Queue()

        self.create_widgets()
        self.update_buttons()
        self.start_dns_update_thread()

    def set_icon(self):
        if os.path.exists(self.icon_path):
            self.iconbitmap(self.icon_path)
        else:
            print(f'Icon file not found at {self.icon_path}')

    def create_widgets(self):
        self.create_nav_frame()
        self.create_title_frame()
        self.create_ts_dns_container()

    def create_nav_frame(self):
        self.nav_frame = ctk.CTkFrame(self, fg_color='#333333')
        self.nav_frame.pack(side='top', fill='x', padx=20, pady=(20, 0))
        self.prev_button = HoverButton(self.nav_frame, text='←', command=lambda: self.change_page(-1),
                                       hover_color='#FF0000', hover_text_color='#000000', corner_radius=10, 
                                       width=40, height=40)
        self.prev_button.pack(side='left', padx=5, pady=5)
        self.dns_label = ctk.CTkLabel(self.nav_frame, text='DNS1: N/A | DNS2: N/A', font=('Comic Sans MS', 18 , 'bold'), text_color='#999999')
        self.dns_label.pack(side='left', padx=5, expand=True)
        self.next_button = HoverButton(self.nav_frame, text='→', command=lambda: self.change_page(1),
                                       hover_color='#FF0000', hover_text_color='#000000', corner_radius=10, 
                                       width=40, height=40)
        self.next_button.pack(side='right', padx=5, pady=5)

    def create_title_frame(self):
        self.title_frame = ctk.CTkFrame(self, fg_color=self.cget('bg'))
        self.title_frame.pack(side='top', fill='x', padx=20, pady=(10, 20))
        self.title_frame_inner = ctk.CTkFrame(self.title_frame, fg_color=self.cget('bg'))
        self.title_frame_inner.pack()
        self.title_label_ts = ctk.CTkLabel(self.title_frame_inner, text='TS', font=('Comic Sans MS', 70, 'bold'), text_color='#FF0000')
        self.title_label_ts.pack(side='left')
        self.title_label_dns = ctk.CTkLabel(self.title_frame_inner, text='-DNS', font=('Comic Sans MS', 50, 'bold'), text_color='#FFFFFF')
        self.title_label_dns.pack(side='left')

    def create_ts_dns_container(self):
        self.ts_dns_container = ctk.CTkFrame(self, fg_color='#333333')
        self.ts_dns_container.pack(side='bottom', fill='x', padx=20, pady=(0, 20))
        self.ts_dns_container.grid_rowconfigure(list(range(2)), weight=1)
        self.ts_dns_container.grid_columnconfigure(list(range(3)), weight=1)

    def extract_dns_from_ps1(self, file_path):
        try:
            with open(file_path, 'r') as file:
                matches = re.findall(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', file.read())
                return matches if matches else ['N/A']
        except Exception as e:
            print(f'Error reading {file_path}: {e}')
            return ['N/A']

    def ping_host(self, host):
        try:
            response_time = ping(host)
            return f'{round(response_time * 1000)}ms' if response_time else 'Error'
        except Exception as e:
            print(f'Error pinging host {host}: {e}')
            return 'Error'

    def get_active_dns(self):
        try:
            result = subprocess.run('ipconfig /all', capture_output=True, text=True, shell=True)
            matches = re.findall(r'DNS Servers[^\r\n]*:\s*(\d{1,3}(?:\.\d{1,3}){3})(?:[^\r\n]*\s+(\d{1,3}(?:\.\d{1,3}){3}))?', result.stdout)
            return matches[0] if matches else ('N/A', 'N/A')
        except Exception as e:
            print(f'Error retrieving DNS servers: {e}')
            return ('N/A', 'N/A')

    def update_buttons(self):
        for button in self.ts_dns_container.winfo_children():
            button.grid_forget()
        start_index = self.current_page * 6
        for i, file_name in enumerate(self.scripts[start_index:start_index+6]):
            display_name = file_name[:-4]
            file_path = os.path.join(self.libraries_path, file_name)
            dns_list = self.extract_dns_from_ps1(file_path)
            target = dns_list[0] if dns_list else 'N/A'
            ping_time = self.ping_host(target)
            button_text = f'{display_name} : {ping_time}'
            ts_dns_button = HoverButton(self.ts_dns_container, text=button_text, command=lambda f=file_name: self.run_script(f),
                                       hover_color='#FF0000', hover_text_color='#000000', corner_radius=10, 
                                       font=('Comic Sans MS', 14, 'bold'), is_active=True)
            ts_dns_button.grid(row=i // 3, column=i % 3, pady=10, padx=10, sticky='nsew')
        self.update_navigation_buttons()

    def start_dns_update_thread(self):
        threading.Thread(target=self.update_dns_loop, daemon=True).start()
        self.process_queue()

    def update_dns_loop(self):
        while True:
            dns1, dns2 = self.get_active_dns()
            self.queue.put(('dns', dns1, dns2))
            self.update_buttons_color(dns1, dns2)
            threading.Event().wait(0.01)  # Reducing wait time for more frequent updates

    def update_buttons_color(self, dns1, dns2):
        for button in self.ts_dns_container.winfo_children():
            file_name = button.cget('text').split()[0] + '.ps1'
            file_path = os.path.join(self.libraries_path, file_name)
            dns_list = self.extract_dns_from_ps1(file_path)
            target = dns_list[0] if dns_list else 'N/A'
            button_color = '#004d00' if target in (dns1, dns2) else '#444444'
            ping_time = self.ping_host(target)
            button_text = f'{file_name[:-4]} : {ping_time}'
            self.queue.put(('button', button, button_color, button_text))

    def process_queue(self):
        while not self.queue.empty():
            item = self.queue.get()
            if item[0] == 'dns':
                self.dns_label.configure(text=f'DNS1: {item[1]} | DNS2: {item[2]}')
            elif item[0] == 'button':
                item[1].configure(fg_color=item[2], text=item[3])
        self.after(1, self.process_queue)  # Reduced interval for more frequent UI updates

    def run_script(self, script_name):
        script_path = os.path.join(self.libraries_path, script_name)
        try:
            subprocess.run(['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', script_path], shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f'Error running script {script_name}: {e}')

    def change_page(self, direction):
        new_page = self.current_page + direction
        if 0 <= new_page < (len(self.scripts) + 5) // 6:
            self.current_page = new_page
            self.update_buttons()

    def update_navigation_buttons(self):
        self.prev_button.configure(state='normal' if self.current_page > 0 else 'disabled')
        self.next_button.configure(state='normal' if (self.current_page + 1) * 6 < len(self.scripts) else 'disabled')

if __name__ == '__main__':
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("Requesting admin privileges...")
        script_path = os.path.realpath(__file__)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 1)
    else:
        app = DNSChangerApp()
        app.mainloop()