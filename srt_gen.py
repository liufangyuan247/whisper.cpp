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
    ret = subprocess.call(cmds, stderr=subprocess.DEVNULL)
    # ret = subprocess.call(cmds)
    if ret != 0:
        raise Exception("wisper failed")

def convert_to_wav(audio_file_path, wav_file_path, start_time, end_time):
    cmds = [
        "ffmpeg",
        "-i", audio_file_path,
        "-ss", str(start_time),
        "-t", str(end_time - start_time),
        "-ar", "16000",
        "-acodec", "pcm_s16le",
        wav_file_path,
        "-y"
    ]
    print(f"try call {' '.join(cmds)}", flush=True)
    ret = subprocess.call(cmds, stderr=subprocess.DEVNULL)
    if ret != 0:
        raise Exception("convert_to_wav failed")


def gen_srt(audio_file, model = 'ggml-large-v2.bin', lang = 'zh', audio_seg_length = 1200, audio_offset = 0):
    dir = os.path.dirname(audio_file)
    base_name = os.path.basename(audio_file).split('.')[0]
    project_folder = os.path.join(dir, base_name)
    if not os.path.exists(project_folder):
        os.mkdir(project_folder)

    # first get audio file length
    audio_length = get_audio_length(audio_file)

    model_path = f"models/{model}"

    subs = []
    for i in range(0, int((audio_length - audio_offset) / audio_seg_length) + 1):
        time_point = datetime.now()
        start_time = i * audio_seg_length + audio_offset
        end_time = min(start_time + audio_seg_length, audio_length)
        wav_file = os.path.join(project_folder, f"{i:05d}.wav")
        srt_file = os.path.join(project_folder, f"{i:05d}.srt")
        convert_to_wav(audio_file, wav_file, start_time, end_time)
        run_wisper(wav_file, os.path.splitext(srt_file)[0], model_path, lang)
        sub = load_subs(srt_file)
        if not subs:
            subs = sub
        else:
            last_entry = subs[-1]
            subs += offset_subs(sub, start_time, last_entry.index)
        save_srt(subs, os.path.join(dir, base_name + ".srt"))
        time_consumed = datetime.now() - time_point
        print(f"audio length: {end_time - start_time}s, process time: {time_consumed.total_seconds()}s, process ratio: {(end_time - start_time) / time_consumed.total_seconds()}")

    # shutil.rmtree(project_folder)

if __name__ == "__main__":
    # sub0 = load_subs('output.wav.srt')
    # sub1 = load_subs('output.wav.srt')
    # print(offset_subs(sub1, 300, sub0[-1].index))

    # save_srt(sub0 + sub1, "output.wav1.srt")
    # print(get_audio_length("./镕亦看世界 - 苏东坡新传1.opus"))

    gen_srt(sys.argv[1], audio_offset=26 * 1200)