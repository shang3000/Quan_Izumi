from pytube import YouTube, exceptions
import os
import time
import random
from tkinter import Tk, Entry, Button, Label, PhotoImage
from tkinter.filedialog import askdirectory
from tkinter.messagebox import showinfo, showerror
from threading import Thread
from queue import Queue
import tkinter as tk
import socket

socket.setdefaulttimeout(30)  # 设置网络请求超时

file_size = 0
progress_queue = Queue()


def progress(stream=None, chunk=None, remaining=None):
    file_downloaded = file_size - remaining
    per = round((file_downloaded / file_size) * 100, 1)
    progress_queue.put(per)


def update_progress():
    try:
        per = progress_queue.get_nowait()
        dBtn.config(text=f"{per}% downloaded")
    except:
        pass
    main.after(100, update_progress)


def startDownload():
    global file_size
    try:
        URL = urlField.get()
        if not URL:
            showerror("Error", "Please enter a valid URL")
            return
        dBtn.config(text="Please wait...", state=tk.DISABLED)
        path_save = askdirectory()
        if path_save is None:
            dBtn.config(state=tk.NORMAL, text="Start Download")
            return
        for attempt in range(3):  # 最多重试 3 次
            try:
                ob = YouTube(URL, on_progress_callback=progress)
                strm = ob.streams.filter(progressive=True, file_extension='mp4').first()
                if not strm:
                    raise Exception("No suitable stream found")
                file_size = strm.filesize
                dfile_size = round(file_size / 1000000, 2)
                label.config(text=f"Size: {dfile_size} MB")
                label.pack(side=tk.TOP, pady=10)
                desc.config(
                    text=f"{ob.title}\n\nLabel: {ob.author}\n\nlength: {round(ob.length / 60, 1)} mins\n\nViews: {round(ob.views / 1000000, 2)}M"
                )
                desc.pack(side=tk.TOP, pady=10)
                strm.download(path_save, ob.title)
                break  # 成功下载后退出循环
            except exceptions.VideoUnavailable as e:
                raise Exception(f"Video unavailable: {str(e)}")
            except exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    wait_time = random.uniform(5, 15)  # 随机等待 5-15 秒
                    print(f"Too many requests. Waiting {wait_time:.1f} seconds before retrying...")
                    time.sleep(wait_time)
                else:
                    raise  # 其他 HTTP 错误直接抛出
        else:
            raise Exception("Failed after multiple attempts due to rate limiting")
        dBtn.config(state=tk.NORMAL, text="Start Download")
        showinfo("Download Finished", "Downloaded Successfully")
        urlField.delete(0, tk.END)
        label.pack_forget()
        desc.pack_forget()
    except Exception as e:
        showerror("Error", f"Download failed: {str(e)}")
        dBtn.config(state=tk.NORMAL, text="Start Download")


def startDownloadthread():
    thread = Thread(target=startDownload)
    thread.start()


# 主窗口
main = Tk()
main.title("My YouTube Downloader")
main.config(bg="#3498DB")
main.geometry("500x600")

try:
    main.iconbitmap("youtube-ios-app.ico")
    file = PhotoImage(file="photo.png")
    headingIcon = Label(main, image=file)
    headingIcon.pack(side=tk.TOP)
except Exception as e:
    print(f"Failed to load image/icon: {e}")

urlField = Entry(main, font=("Times New Roman", 18), justify=tk.CENTER)
urlField.pack(side=tk.TOP, fill=tk.X, padx=10, pady=15)

dBtn = Button(
    main,
    text="Start Download",
    font=("Times New Roman", 18),
    relief="ridge",
    activeforeground="red",
    command=startDownloadthread,
)
dBtn.pack(side=tk.TOP)
label = Label(main, text="")
desc = Label(main, text="")
author = Label(main, text="@G.S.", font=("Courier", 44))
author.pack(side=tk.BOTTOM)

main.after(100, update_progress)  # 启动进度更新检查
main.mainloop()
