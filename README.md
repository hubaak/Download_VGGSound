# Download_VGGSound
A very simple code to download [VGGSound](https://www.robots.ox.ac.uk/~vgg/data/vggsound/) dataset.

---

## Install Python Packages
```bash
pip install yt_dlp pandas tqdm
```

## How to use
If you want to use proxy or set the number of thread to download the dataset in parallel, simply the code at very begining of `download_vggsound.py`.

Run 
```bash
python download_vggsound.py
```
and a directory named `VGGSound` should be create automatically, and data set will be downloaded in `VGGSound`.

By the way, you can continue you downloading after interrupting with this code :).

