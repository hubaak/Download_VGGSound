# Download_VGGSound
A very simple code to download [VGGSound](https://www.robots.ox.ac.uk/~vgg/data/vggsound/) dataset.

---

## Install Python Packages
The code requires some python packages:
```bash
pip install yt_dlp pandas tqdm ffmpeg-python
```

Install `FFmpeg` in `Linux`:
```bash
sudo apt-get install ffmpeg
```

Install `FFmpeg` in `windows`:
Go to [the official website](https://ffmpeg.org/download.html) of `FFmpeg` to install it. Remember to add `FFmpeg` to system environment.

## How to use
If you want to use proxy or set the number of thread to download the dataset in parallel, simply the code at very begining of `download_vggsound.py`.

Run 
```bash
python download_vggsound.py
```
and a directory named `VGGSound` should be create automatically, and data set will be downloaded in `VGGSound`.

By the way, you can continue your downloading after interrupting with this code :).
As some video on `YouTube` is private or cannot be accessed anymore, it's natural that some video in `vggsound.csv` cannot be downloaded.

