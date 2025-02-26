import srt
from pylrc.classes import Lyrics, LyricLine
import os
import sys
from datetime import datetime

def srt2lrc(srt_file):
  subs = srt.parse(open(srt_file).read())
  subs = list(subs)
  print(len(subs))

  lyrics = []
  for sub in subs:
      total_seconds = sub.start.total_seconds()
      min = int(total_seconds / 60)
      seconds = int(total_seconds) % 60
      ms = int(total_seconds * 100) % 100

      lyrics.append(f"[{min}:{seconds:02d}.{ms:02d}]{sub.content}")

  lrc_file = srt_file.replace(".srt", ".lrc")
  with open(lrc_file, "w") as f:
     f.write("\n".join(lyrics))


if __name__=="__main__":
  srt2lrc(sys.argv[1])
