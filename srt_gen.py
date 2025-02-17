import subprocess
import os
import time
import srt
from datetime import timedelta, datetime
import re
import glob
import shutil
import sys

nvcc_path = "/usr/local/cuda/bin"
cuda_lib_path = "/usr/local/cuda-11.4/targets/x86_64-linux/lib/"

if nvcc_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + nvcc_path

if cuda_lib_path not in os.environ.get("LD_LIBRARY_PATH", ""):
    os.environ["LD_LIBRARY_PATH"] = os.environ.get("LD_LIBRARY_PATH", "") + os.pathsep + cuda_lib_path

def offset_subs(subs, time_offset, index_offset):
    # time_offset in seconds
    time_delta = timedelta(seconds=time_offset)
    for sub in subs:
        sub.start += time_delta
        sub.end += time_delta
        sub.index += index_offset
    return subs

def load_subs(srt_path):
    with open(srt_path, 'r') as f:
        return list(srt.parse(f.read()))

def save_srt(subs, srt_path):
    with open(srt_path, 'w') as f:
        f.write(srt.compose(subs))

def get_audio_length(audio_file_path):
    ret = subprocess.check_output(['ffprobe', '-i', audio_file_path, '-show_entries', 'format=duration', '-v', 'error'], stderr=subprocess.DEVNULL)
    str = re.search(r"duration=\d+(\.\d+)?", ret.decode()).group()
    return float(str.split('=')[1])

def run_wisper(wav_file_path, srt_file_path, model_path, lang = 'zh'):
    cmds = [
        "./main",
        "-m", model_path,
        "-f", wav_file_path,
        "-l", lang,
        "-osrt",
        "-of", srt_file_path,
    ]

    print(f"try call {' '.join(cmds)}", flush=True)
    ret = subprocess.call(cmds, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    # ret = subprocess.call(cmds)
    if ret != 0:
        raise Exception("wisper failed")

def split_audio(audio_file_path, segment_len):
    dir = os.path.dirname(audio_file_path)
    base_name = os.path.basename(audio_file_path).split('.')[0]
    project_folder = os.path.join(dir, base_name)

    cmds = [
        "ffmpeg",
        "-i", audio_file_path,
        "-f", "segment",
        "-segment_time", str(segment_len),
        "-c", "copy",
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        os.path.join(project_folder, "%05d.wav"),
    ]
    print(f"try call {' '.join(cmds)}", flush=True)

    time_point = datetime.now()
    ret = subprocess.call(cmds, stderr=subprocess.DEVNULL)
    if ret != 0:
        raise Exception("split audio failed")
    time_consumed = datetime.now() - time_point
    print(f"split audio {audio_file_path} cost {time_consumed}s")



def gen_srt(audio_file, model = 'ggml-large-v2.bin', lang = 'zh', audio_seg_length = 1200):
    dir = os.path.dirname(audio_file)
    base_name = os.path.basename(audio_file).split('.')[0]
    project_folder = os.path.join(dir, base_name)
    if not os.path.exists(project_folder):
        os.mkdir(project_folder)
    split_audio(audio_file, audio_seg_length)

    model_path = f"models/{model}"

    audio_files = glob.glob(f"{project_folder}/*.wav")
    audio_files.sort()

    subs = []
    for i in range(len(audio_files)):
        time_point = datetime.now()
        start_time = i * audio_seg_length
        wav_file = audio_files[i]
        srt_file = os.path.join(project_folder, f"{i:05d}.srt")
        run_wisper(wav_file, os.path.splitext(srt_file)[0], model_path, lang)
        sub = load_subs(srt_file)
        if not subs:
            subs = sub
        else:
            last_entry = subs[-1]
            subs += offset_subs(sub, start_time, last_entry.index)
        save_srt(subs, os.path.join(dir, base_name + ".srt"))
        time_consumed = datetime.now() - time_point
        audio_length = get_audio_length(wav_file)
        print(f"audio length: {audio_length}s, process time: {time_consumed.total_seconds()}s, process ratio: {audio_length / time_consumed.total_seconds()}")

    # shutil.rmtree(project_folder)

if __name__ == "__main__":
    files = [
        # '镕亦看世界 - 苏东坡新传1.opus',
        '镕亦看世界 - 苏东坡新传2.opus',
        '镕亦看世界 - 苏东坡新传3.opus',
        '镕亦看世界 - 全球通史1.opus',
        '镕亦看世界 - 全球通史2.m4a',
        '镕亦看世界 - 万历十五年.opus',
    ]

    for f in files:
        print(f"begin processing: {f}")
        gen_srt(f)