import os
# Set proxy if you want
# os.environ["http_proxy"] = "127.0.0.1:port"
# os.environ["https_proxy"] = "127.0.0.1:port"
num_threads = 16

import yt_dlp
import subprocess
import pandas as pd
from tqdm import tqdm
import re
import sys
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
import contextlib
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

import logging

# Define a custom logger that suppresses output
class NullLogger(logging.Logger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addHandler(logging.NullHandler())

# Create a custom logger instance
null_logger = NullLogger('null_logger')
yt_dlp.YoutubeDL.logger = null_logger

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
    return filtered_df, len(df) - len(filtered_df)

def meta_data_clean_df_error_videos(err_df, df):
    filtered_df = df[~df['video_id'].isin(err_df['video_id'])]
    return filtered_df, len(df) - len(filtered_df)

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
    stderr_redirect = StringIO()
    try:
        with contextlib.redirect_stderr(stderr_redirect):
            ydl = yt_dlp.YoutubeDL(options)
            # Download the video
            with ydl:
                result = ydl.extract_info(video_url, download=True)
                downloaded_file = ydl.prepare_filename(result)
    except Exception as e:
        return stderr_redirect.getvalue(), df_row['video_id']  # Return the error message
    
    inputfile = downloaded_file
    output_file_name = "v{}_{}_{}_out.mkv".format(video_id, start_time, end_time)
    ffmpeg_extract_segment(inputfile, os.path.join(category_dir, output_file_name), start_time, end_time)
    os.remove(inputfile)
    return None, df_row['video_id']


csv_path = 'vggsound.csv'
err_csv_path = 'error.csv'
data_dir = 'VGGSound'
if not os.path.exists(data_dir):
    os.mkdir(data_dir)
if not os.path.exists('tmp'):
    os.mkdir('tmp')
if os.path.exists(err_csv_path):
    err_column_names = ['video_id', 'err_reason']
    err_df = pd.read_csv(err_csv_path, names=err_column_names)
else:
    err_column_names = ['video_id', 'err_reason']
    err_df = pd.DataFrame(columns=err_column_names)
    err_df.to_csv(err_csv_path, index=False, header=False)
    
column_names = ['video_id', 'start_time', 'category', 'split']
df = pd.read_csv(csv_path, names=column_names)
total_num = len(df)
print("All {} videos in VGGSound".format(total_num))    # filter exist files
df, num_exist = meta_data_clean_df_exist_file(data_dir, df)
df, num_error = meta_data_clean_df_error_videos(err_df, df)
print("{} videos have been downloaded, {} videos failed to be download, {} to be downloaded".format(num_exist, num_error, len(df)))
    
origin_sysout = sys.stdout
print("Start runing!")
with tqdm(total=len(df)) as pbar:
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(download_and_process, data_dir, df_row) for _, df_row in df.iterrows()]
            
        for future in concurrent.futures.as_completed(futures):
            error_message, video_id = future.result()
            if error_message:
                with contextlib.redirect_stdout(origin_sysout):
                    print(error_message)
                    if 'ERROR' in error_message:
                        video_id_str = "[youtube] {}: ".format(video_id)
                        Error_reason = error_message[error_message.find(video_id_str) + len(video_id_str):].strip()
                        if Error_reason.find("\n") != -1:
                            Error_reason = Error_reason[:Error_reason.find("\n")]
                        if not any(error in Error_reason for error in ['Too Many Requests', 'Internal Server Error', 'Read timed out']):
                            with open(err_csv_path, "a") as file:
                                file.write("{},\"{}\"\n".format(video_id, Error_reason.replace('\"', '')))

            pbar.update(1)
            
    
    
    