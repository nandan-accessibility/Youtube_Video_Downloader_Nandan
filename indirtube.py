# -*- coding: utf-8 -*-
# Youtube Video Downloader Nandan v1.0
# Developed by Nandan Kumar Singh

import os
import threading
import subprocess
import gui
import wx
import ui
import api
import globalPluginHandler
import scriptHandler
import addonHandler
import re

addonHandler.initTranslation()

BRAND = "Youtube Video Downloader Nandan"
SIGN = "Developed by Nandan Kumar Singh"


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    scriptCategory = BRAND

    def __init__(self):
        super().__init__()
        self.currentPercent = 0
        self.isDownloading = False
        self.progressDialog = None
        self.lastTitle = None

    # =========================
    # Paths
    # =========================
    def get_paths(self):
        root = os.path.dirname(os.path.dirname(__file__))
        lib = os.path.join(root, "lib")
        ytdlp = os.path.join(lib, "yt-dlp.exe")
        return ytdlp, lib

    # =========================
    # Get Title
    # =========================
    def get_title(self, url):
        ytdlp, _ = self.get_paths()
        try:
            return subprocess.check_output(
                [ytdlp, "--get-title",
                 "--extractor-args", "youtube:player_client=android",
                 url]
            ).decode().strip()
        except:
            return "Video"

    # =========================
    # Progress Dialog
    # =========================
    def create_progress_dialog(self, title):
        self.progressDialog = wx.ProgressDialog(
            "Downloading",
            f"Downloading: {title}",
            maximum=100,
            parent=gui.mainFrame,
            style=wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME
        )

    # =========================
    # Update Progress
    # =========================
    def update_progress(self, line):

        match = re.search(r'(\d{1,3}\.\d+)%', line)

        if match:

            percent = int(float(match.group(1)))

            if percent != self.currentPercent:

                self.currentPercent = percent

                if self.progressDialog:
                    wx.CallAfter(self.progressDialog.Update, percent)

                if percent % 5 == 0:
                    ui.message(f"{percent} percent downloaded")

    # =========================
    # Insert+T Progress
    # =========================
    @scriptHandler.script(
        description="Reports current download progress",
        category=BRAND
    )
    def script_reportProgress(self, gesture):

        if self.isDownloading:
            ui.message(f"{self.currentPercent} percent downloaded")
        else:
            ui.message("No active download.")

    # =========================
    # Run Download
    # =========================
    def run_download(self, url, mode):

        ytdlp, lib = self.get_paths()

        if not os.path.exists(ytdlp):
            ui.message("yt-dlp.exe not found.")
            return

        download_path = os.path.join(
            os.path.expandvars("%USERPROFILE%"),
            "Downloads"
        )

        output_template = os.path.join(
            download_path,
            "%(title)s.%(ext)s"
        )

        cmd = [
            ytdlp,
            "-o", output_template,
            "--newline",
            "--restrict-filenames",
            "--extractor-args", "youtube:player_client=android",
            "--ffmpeg-location", lib
        ]

        if mode == "mp3":
            cmd += [
                "--extract-audio",
                "--audio-format", "mp3"
            ]
        else:
            cmd += [
                "-f", "bestvideo+bestaudio/best",
                "--merge-output-format", "mp4"
            ]

        cmd.append(url)

        try:

            self.isDownloading = True
            self.currentPercent = 0
            self.lastTitle = self.get_title(url)

            ui.message(f"Download started: {self.lastTitle}")

            wx.CallAfter(self.create_progress_dialog, self.lastTitle)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            for line in process.stdout:
                self.update_progress(line)

            process.wait()

            self.isDownloading = False

            if self.progressDialog:
                wx.CallAfter(self.progressDialog.Destroy)

            if process.returncode == 0:
                ui.message(
                    f"{self.lastTitle} downloaded successfully. {SIGN}"
                )
            else:
                ui.message("Download failed.")

        except Exception:
            ui.message("System error occurred.")

    # =========================
    # Main Script
    # =========================
    @scriptHandler.script(
        description="Download YouTube video or audio",
        category=BRAND
    )
    def script_start(self, gesture):

        try:
            url = api.getClipData().strip()
        except:
            ui.message("Clipboard not accessible.")
            return

        if not url.startswith(("http://", "https://")):
            ui.message("No valid URL. Please copy a valid YouTube link.")
            return

        if "youtu" not in url.lower():
            ui.message("No valid YouTube URL found in clipboard.")
            return

        def show_main():

            choices = [
                "Download MP3 (Audio)",
                "Download MP4 (Video)",
                "About Developer"
            ]

            dlg = wx.SingleChoiceDialog(
                gui.mainFrame,
                "Select option",
                BRAND,
                choices
            )

            if dlg.ShowModal() == wx.ID_OK:

                sel = dlg.GetSelection()

                if sel == 0:
                    threading.Thread(
                        target=self.run_download,
                        args=(url, "mp3"),
                        daemon=True
                    ).start()

                elif sel == 1:
                    threading.Thread(
                        target=self.run_download,
                        args=(url, "mp4"),
                        daemon=True
                    ).start()

                elif sel == 2:
                    ui.message(
                        "Youtube Video Downloader Nandan. Developed by Nandan Kumar Singh. NVDA and JAWS Certified Expert."
                    )

            dlg.Destroy()

        wx.CallAfter(show_main)