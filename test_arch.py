import subprocess
import re
import os
import time

nvcc_path = "/usr/local/cuda/bin"
cuda_lib_path = "/usr/local/cuda-11.4/targets/x86_64-linux/lib/"

if nvcc_path not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + nvcc_path

if cuda_lib_path not in os.environ.get("LD_LIBRARY_PATH", ""):
    os.environ["LD_LIBRARY_PATH"] = os.environ.get("LD_LIBRARY_PATH", "") + os.pathsep + cuda_lib_path

makefile_path = "Makefile"

def get_arch_list():
    res = subprocess.check_output(["nvcc", "--list-gpu-arch"])
    return res.decode("utf-8").split()

def replace_arch_for_makefile(arch):
    pat='''	else
		CUDA_ARCH_FLAG=.+?
	endif
'''
    text = open(makefile_path, "r").read()
    match = re.search(pat, text)

    if match:
        text = text.replace(match.group(0), f'''\telse
\t\tCUDA_ARCH_FLAG={arch}
\tendif
''')
        open(makefile_path, "w").write(text)


def make():
    subprocess.call(["make", "clean"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.call(["make", "WHISPER_CUBLAS=1"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def test_run():
    start_time = time.time()
    ret = subprocess.call("./main -m models/ggml-large-v2.bin -f ./output.wav -l zh".split(), stderr=subprocess.DEVNULL)
    end_time = time.time()
    if ret != 0:
        return -1
    return (end_time - start_time) * 1000

if __name__ == "__main__":
    arch_list = get_arch_list()
    print(arch_list)
    make()

    # for arch in arch_list[::-1]:
    #     replace_arch_for_makefile(arch)
    #     make()
    #     elasped = test_run()
    #     if elasped < 0:
    #         print(f"arch: {arch} not support")
    #     else:
    #         print(f"arch: {arch} time: {elasped}ms")
