#!/usr/bin/env python
import os
import sys
import json
import subprocess
import time

values = {
    "name": "WindowsXP",
    "p": 102011604035381881,     # 0x16A6B036D7F2A79
    "x": {
        "0": 0,
        "1": 9433814980383617,   # 0x21840136C85381
        "2": 19168316694801104,  # 0x44197B83892AD0
        "3": 90078616228674308,  # 0x1400606322B3B04
        "4": 90078616228674308,  # 0x1400606322B3B04
        "5": 1,
    },
    "pub": 65537,                # 0x10001
}

def tee(*output, file=None, **kwargs):
    # Get the current timestamp
    timestamp = time.strftime("[%H:%M:%S]", time.localtime())
    
    print(timestamp, *output, file=sys.stdout, **kwargs)
    
    if file is not None:
        print(timestamp, *output, file=file, **kwargs)

# Start measuring the execution time
start_time = time.time()

skip = 0

if len(sys.argv) > 1:
    if sys.argv[1] == "-h":
        print(f"Usage: {sys.argv[0]} [options]")
        print("  -h : Display this help")
        print("  -s : Skip the longest part to solve and use precomputed orders mod small primes")
        exit(0)
    elif sys.argv[1] == "-s":
        skip = 1

os.makedirs(values["name"], exist_ok=True)

ell_todo = [5, 11, 13, 17, 19]
curve = list(values["x"].values())  # Excluding p and pub from the curve

logFile = open(f"{values['name']}/log.txt", "a")

if skip == 0:
    ell = []
    s1p = []
    s2p = []

    # Check if the JSON file already exists with the required values
    json_file = f"{values['name']}/input_ell_state.json"
    if os.path.exists(json_file):
        with open(json_file, "r") as f:
            data = json.load(f)
            if (
                "ell" in data
                and "s1p" in data
                and "s2p" in data
                and len(data["ell"]) == len(data["s1p"]) == len(data["s2p"])
            ):
                ell = data["ell"]
                s1p = data["s1p"]
                s2p = data["s2p"]
            else:
                tee(f"JSON value lengths don't match! starting from scratch", file=logFile)

    for i in range(len(ell_todo)):
        ell_i = ell_todo[i]
        
        if i < len(ell):
            tee(f"\n---------- Skipping order mod {ell_i} ----------", file=logFile)
            continue

        tee(f"\n---------- Solving order mod {ell_i} ----------", file=logFile)
        input_filename = f"{values['name']}/input_ell_{ell_i}.txt"

        with open(input_filename, "w") as f:
            f.write(str(values["p"]) + "\n")
            f.write(str(curve) + "\n")
            f.write(str(ell_i) + "\n")

        output_filename = f"{values['name']}/input_ell_{ell_i}_output.txt"
        
        # open a subprocess
        process = subprocess.Popen(["./main", "-o", output_filename], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
        with open(input_filename, "r") as f:
            process.stdin.write(f.read())
        process.stdin.close()
        
        # read and display the output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                tee(output.strip(), file=logFile)
                
        process.wait()

        with open(output_filename, "r") as f:
            res = f.read()

        ell_res = res.split(" ")
        ell.append(ell_i)
        s1p.append(int(ell_res[1]))
        s2p.append(int(ell_res[2]))

        # Write ell, s1p, and s2p values to JSON file
        with open(json_file, "w") as f:
            json.dump({"ell": ell, "s1p": s1p, "s2p": s2p}, f)

else:
    tee("\n---------- Skipping solving of orders mod small primes ----------", file=logFile)
    tee("Setting precomputed values:", file=logFile)

    ell = [5, 11, 13, 17, 19, 23]
    s1p = [4, 1, 5, 16, 15, 8]
    s2p = [0, 2, 10, 16, 2, 7]

crt_arr_ell = ",".join(map(str, ell))
crt_arr_s1p = ",".join(map(str, s1p))
crt_arr_s2p = ",".join(map(str, s2p))

tee("\n---------- Calculating bigger modular information using CRT ----------", file=logFile)
filename = f"{values['name']}/input_crt.txt"

with open(filename, "w") as f:
    f.write(crt_arr_ell + "\n")
    f.write(crt_arr_s1p + "\n")
    f.write(crt_arr_s2p + "\n")

process = subprocess.Popen(["./CRT", "-q"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
with open(filename, "r") as f:
    process.stdin.write(f.read())
process.stdin.close()

crt_output = ""
# read and display the output in real-time
while True:
    output = process.stdout.readline()
    if output == '' and process.poll() is not None:
        break
    if output:
        crt_output = output.strip()
        tee(output.strip(), file=logFile)
        
process.wait()

crt_res = crt_output.split(" ")
crt_mod = int(crt_res[2])
crt_s1p = int(crt_res[0])
crt_s2p = int(crt_res[1])

tee("CRT mod =", crt_mod, file=logFile)
tee("CRT s1p =", crt_s1p, file=logFile)
tee("CRT s2p =", crt_s2p, file=logFile)

tee("\n---------- Solving order from CRT results ----------", file=logFile)
filename = f"{values['name']}/input_lmpmct.txt"

with open(filename, "w") as f:
    f.write(str(values["p"]) + "\n")
    
    for value in list(values["x"].values())[:-1]:
        f.write(str(value) + "\n")
        
    f.write(str(crt_mod) + "\n")
    f.write(str(crt_s1p) + "\n")
    f.write(str(crt_s2p) + "\n")

process = subprocess.Popen(["./LMPMCT", "-o", f"{values['name']}/output_lmpmct.txt"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)
with open(filename, "r") as f:
    process.stdin.write(f.read())
process.stdin.close()

# read and display the output in real-time
while True:
    output = process.stdout.readline()
    if output == '' and process.poll() is not None:
        break
    if output:
        tee(output.strip(), file=logFile)
        
process.wait()

with open(f"{values['name']}/output_lmpmct.txt", "r") as f:
    order = f.read()

tee("\n---------- Calculating private key from order ----------", file=logFile)
process = subprocess.Popen(["./InvMod", str(values['pub']), order], stdout=subprocess.PIPE, universal_newlines=True)
priv = process.stdout.read()

process.wait()

tee("\nPrivate key:", priv, file=logFile)
tee("\nDecimal:", int(priv, 16).str(), file=logFile)

# Stop measuring the execution time
end_time = time.time()

# Calculate the elapsed time
elapsed_time = end_time - start_time

# Print the execution time
tee("Execution time:", elapsed_time, "seconds", file=logFile)
