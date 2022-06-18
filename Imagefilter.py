# Image Filter
# By k8thekat - 4/10/2021
import os
from os import path
import sys
from PIL import Image
import hashlib
import shutil


# User path input function loop
def Uinput(loc):
    defaultpath = "d:/picture/anime"
    while(1):
        path = input(loc + " File Path (default: " + defaultpath + "): ") # user input with default path displayed
        if len(path) == 0: # if length of input is 0 then set path to defaultpath.
            path = defaultpath
            break

        if os.path.exists(path):
            break

        print("Please re-enter " + loc + " file path~")

    print(loc + " Path set to " + path)
    
    # if last character of path not containing array values [ ] then append "/" to end of path
    if path[-1] not in ["\\", "/"]: 
        path += "/" 
    return path

# Deletion confirmation loop
def Confirm(pathin, entry, fileoutname):
    defans = "n"
    while(1):
        ans = input("Delete duplicate file? " + pathin + entry + "(y/N)?")
        ans = ans.lower()
        if len(ans) == 0:
            #print('Default ans set to ' + defans)
            ans = defans

        if ans == "y":
            os.remove(pathin + entry)
            print("FileExistsError: Duplicate file found at " + fileoutname + " --> Deleting file..." + pathin + entry)
            break

        elif ans == "n":
            print("Skipping deletion..." + pathin + entry)
            break
    return ans


# User path prompt
pathin = Uinput("Source")
pathout = Uinput("Destination")

# IMGRES Dictionary
IMGRES = [{"name": "Low Res", "dimensions": (1440,900)}, 
           {"name": "Mid Res", "dimensions":  (1920, 1440)},
           {"name": "High Res", "dimensions":  (2560, 1600)},
           {"name": "UHD Res", "dimensions":  (3840, 2160)},
           {"name": "Phone Res", "dimensions":  (1080, 2400)},
           {"name": "UHDP Res", "dimensions":(0,0)}]

# Resolution folder creation
for entry in IMGRES:
    if not os.path.exists(pathout + entry["name"]):
        os.makedirs(pathout + entry["name"])
        print(entry["name"] + " folder created!")
    else:
        print("Found " + entry["name"] + " directory; skipping creation")
input()

# create list of path directory
alist = os.listdir(pathin)

# image filtering
for entry in alist:

    # directory check 
    if os.path.isdir(pathin + entry):
        print("Found " + entry + " directory; skipping~")
        continue
        
    # ignore .ini files (picasa file sorter/similar)
    if entry.lower().endswith(".ini"):
        print("Found .ini file; skipping~")
        continue
    
    # image sorting via dictionary dimensions comparison" > = GREATER THAN | < = LESS THAN "
    Found = False
    try:
        im = Image.open(pathin + entry)
        for move in range(0, len(IMGRES) - 1): # range function starts at X value and ends at Y-1 (range(X,Y-1)) count = interation value
            IMW,IMH = IMGRES[move]["dimensions"] # value 1, value 2 = IMGRES[int][dictionary key]
            if (IMW >= im.width) and (IMH >= im.height):
                Found = True
                break

        im.close()
        
    except:
        pass

    
    # if image doesn't fit any dictionary values place in UHDP folder
    if(not Found):
        move = len(IMGRES) - 1

    # file moving to new location via os.rename(source, new) function
    # if duplicate file exists; compare via hashlib.sha256 in binary format
    fileoutname = pathout + IMGRES[move]["name"] + "/" + entry
    try:
        #os.rename(pathin + entry, fileoutname)
        shutil.move(pathin + entry, fileoutname)

    except FileExistsError:
        file1hash = hashlib.sha256(open(pathin + entry,"rb").read()).hexdigest() # file hash comparison => open(file), "rb" = read binary , read file and digest = hash results
        file2hash = hashlib.sha256(open(fileoutname,"rb").read()).hexdigest()

        # compare file1hash to file2hash
        # if files are same; delete file in source folder
        if file1hash == file2hash:
            print(pathin + entry)
            print(file1hash + "\n" + file2hash)

            # Prompt confirmation for deletion
            Confirm(pathin, entry, fileoutname)
         
        else:
            # duplicate file name check and renaming
            dotloc = fileoutname.rfind(".")
            filenum = 2

            while(os.path.exists(fileoutname[0:dotloc] + str(filenum) + fileoutname[dotloc:])):
                filenum += 1   

            print("Duplicate file name found at " + fileoutname + " --> Renaming file..." + fileoutname[0:dotloc] + str(filenum) + fileoutname[dotloc:])
            #os.rename(pathin + entry, fileoutname[0:dotloc] + str(filenum) + fileoutname[dotloc:])
            shutil.move(pathin + entry, fileoutname[0:dotloc] + str(filenum) + fileoutname[dotloc:])

    print( im.width, "X", im.height, "|", entry, ">> " + IMGRES[move]["name"] + " >>", fileoutname)
print("Finished Sorting, press enter key to exit")
input()
