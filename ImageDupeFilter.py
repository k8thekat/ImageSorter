# ImageDupeFilter
import hashlib
import os
import shutil
from pathlib import Path
import json

def FileHashCompare(pathin):
    comparelist = os.listdir(pathin)
    hashlist = []
    for entry in comparelist:
        filehash = hashlib.sha256(open(pathin + entry,'rb').read()).hexdigest() # file hash comparison => open(file), "rb" = read binary , read file and digest = hash results

        if filehash not in hashlist:
            hashlist.append(filehash)
            hashlist.sort()
        else:
            os.remove(pathin + entry)
    return


def LoadSettings(filewd,setfile):
    if os.path.isfile(filewd + setfile) != True:
        newfile = open(filewd + setfile, 'x')
        lastdir = ''
    else:
        jsonfile = open(filewd + setfile)
        lastdir = json.load(jsonfile) 
        #print("settings loaded")
    return lastdir

def SaveSettings(path,filewd,setfile):
    newfile = open(filewd + setfile, 'w')
    #print("settings saved")
    json.dump(path,newfile)
    newfile.close()
    return path

def Pinput(filewd,setfile,reply):
    #prompts for userinput
    u_input = input(reply) # user input is a string!!!
    if len(u_input) == 0: # if length of input is 0 then set path to defaultpath.
        u_input = LoadSettings(filewd,setfile)

    if u_input[-1] not in ['\\', '/']: 
        u_input += '/' 
    
    return u_input #what the function replies with

def main():
    wd = Path(__file__).parent.absolute()
    filewd = str(wd)
    setfile = "\imagefilter.json"   
    pathin = Pinput(filewd,setfile,'enter directory (lastdir: ' + LoadSettings(filewd,setfile) + '):')
    FileHashCompare(pathin)
    SaveSettings(pathin,filewd,setfile)
    return 
    
if __name__ == "__main__":
    print("Main Loaded")
    main()

