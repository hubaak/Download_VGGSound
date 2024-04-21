import os
# Set proxy if you want
# os.environ["http_proxy"] = "127.0.0.1:port"
# os.environ["https_proxy"] = "127.0.0.1:port"
num_threads = 8

import yt_dlp
import subprocess
import pandas as pd
from tqdm import tqdm
import re
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import contextlib
from contextlib import redirect_stdout, redirect_stderr


def ffmpeg_extract_segment(input_file, output_file, start_time, end_time):
    # Command to extract segment using ffmpeg
    cmd = ['ffmpeg', '-loglevel', 'quiet', '-i', input_file, '-ss', str(start_time), '-to', str(end_time), output_file]
    
    # Execute the command
    subprocess.run(cmd)
    
def meta_data_clean_df_exist_file(data_dir, df):
    exist_video = []
    for (root,dirs,files) in os.walk(data_dir, topdown=True):
        pattern = r'(\d+)_(\d+)_out.mkv'
        for filename in files:
            if filename.find('.mkv') != -1 and filename[0] == 'v':
                match = re.match(pattern, filename[13:])
                if match:
                    start_time = match.group(1)
                    exist_video.append((filename[1:12], int(start_time)))
    filtered_df = df[~df.apply(lambda row: (row['video_id'], row['start_time']) in exist_video, axis=1)]
    return filtered_df

def download_and_process(data_dir, df_row):
    split_dir = os.path.join(data_dir, df_row['split'])
    category_name = df_row['category']
    category_name = category_name.replace('\"', '').replace(',', '').replace(' ', '_').replace('.', '')
    category_dir = os.path.join(split_dir, category_name)
    if not os.path.exists(split_dir):
        os.mkdir(split_dir)
    if not os.path.exists(category_dir):
        os.mkdir(category_dir)

    video_id = df_row['video_id']
    start_time = df_row['start_time']
    end_time = start_time + 10
    download_file_name = "v{}_{}_{}".format(video_id, start_time, end_time)
    video_url = "https://www.youtube.com/watch?v={}".format(video_id)
    options = {
        'format': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        'merge_output_format': 'mkv',
        'outtmpl': f'tmp/{download_file_name}.%(ext)s',
        'quiet': True
    }
    with contextlib.redirect_stdout(open(os.devnull, 'w')):
        ydl = yt_dlp.YoutubeDL(options)
        # Download the video
        with ydl:
            result = ydl.extract_info(video_url, download=True)
            downloaded_file = ydl.prepare_filename(result)
    inputfile = downloaded_file
    output_file_name = "v{}_{}_{}_out.mkv".format(video_id, start_time, end_time)
    ffmpeg_extract_segment(inputfile, os.path.join(category_dir, output_file_name), start_time, end_time)
    os.remove(inputfile)


csv_path = 'vggsound.csv'
data_dir = 'VGGSound'
if not os.path.exists(data_dir):
    os.mkdir(data_dir)
if not os.path.exists('tmp'):
    os.mkdir('tmp')
    
column_names = ['video_id', 'start_time', 'category', 'split']
df = pd.read_csv(csv_path, names=column_names)
total_num = len(df)
print("All {} videos in VGGSound".format(total_num))    # filter exist files
df = meta_data_clean_df_exist_file(data_dir, df)
print("{} videos have been downloaded, {} to be downloaded".format(total_num - len(df), len(df)))
    
    
print("Start runing!")
with tqdm(total=len(df)) as pbar:
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(download_and_process, data_dir, df_row) for _, df_row in df.iterrows()]
            
        for future in concurrent.futures.as_completed(futures):
            pbar.update(1)
            
    
    
    