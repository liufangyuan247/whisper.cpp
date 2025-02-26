import srt
import glob
import shutil
import sys
from datetime import timedelta
import os

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
    print(len(subs))

    text = srt.compose(subs)
    print(len(text))

    with open(srt_path, 'w') as f:
        f.write(srt.compose(subs))

def merge_srt(subs_folder, audio_seg_length = 1200):
    base_name = os.path.basename(subs_folder)

    files = glob.glob(os.path.join(subs_folder, '*.srt'))
    files.sort()
    print(files)

    subs = []
    index = 1
    for f in files:
        sub = load_subs(f)
        if not subs:
            subs = sub
        else:
            last_entry = subs[-1]
            time = max(last_entry.end.total_seconds(), audio_seg_length * index)
            subs += offset_subs(sub, time, last_entry.index)
        index += 1

    save_srt(subs, subs_folder + '.srt')


if __name__ == "__main__":
    merge_srt(sys.argv[1])