# Image Filter
# By k8thekat - 4/10/2021

import os
from PIL import Image
import hashlib
import shutil
import json
from pathlib import Path

# Default Settings 
def DefaultSettings():
    # Directory Settings
    source = destination = hashdir = str(Path(__file__).parent.absolute())
    #Default Settings for Directories List
    directories = [{'Source' : source},
                {'Output' : destination},
                {'lastHash' : hashdir}]
    return directories

# Script Load Settings
def LoadSettings(filewd,setfile):
    try:    
        if os.path.isfile(filewd + setfile) != True:
            newfile = open(filewd + setfile, 'x')
            lastdir = DefaultSettings()
            newfile.close()
            return lastdir
        else:
            jsonfile = open(filewd + setfile)
            lastdir = json.load(jsonfile) 
            print("settings loaded")
            return lastdir
    except json.decoder.JSONDecodeError:
        lastdir = DefaultSettings()
    return lastdir

# Script Save Settings 
def SaveSettings(pathin,pathout,filewd,setfile,hashdir): 
    #list of dictionaries for settings
    directories = [{'Source' : pathin},
                {'Output' : pathout},
                {'lastHash' : hashdir}]
    newfile = open(filewd + setfile, 'w')
    print("settings saved")
    json.dump(directories,newfile)
    newfile.close()
    return directories

# Hash List Load
def HashDatabaseLoad(hashfile,filewd):
    try:    
        if os.path.isfile(filewd + hashfile) != True:
            newfile = open(filewd + hashfile, 'x')
            hashlist = {}
            newfile.close()
        else:
            jsonfile = open(filewd + hashfile)
            hashlist = json.load(jsonfile) 
            print("hashlist loaded")  
    except json.decoder.JSONDecodeError:
        hashlist = {}
    return hashlist

# Hash List Save
def HashDatabaseSave(filewd,hashfile,hashlist):
    newfile = open(filewd + hashfile, 'w') # w = overwrite
    #saves my hash list to a new file with each entry spaced out by a new line.
    json.dump(hashlist,newfile,indent="\n")
    newfile.close()
    print("hashlist saved")
    return

# Prompt for User Input of working directory
def UserDirectory(setlastdir,location,reply):
    path = input(reply)
    path = path.lower()

    # if length of input is 0 then set path to defaultpath.
    if len(path) == 0 and location == 'source': 
        path = setlastdir[0]['Source']
        return path
      
    if len(path) == 0 and location == 'output':
        path = setlastdir[1]['Output']
        return path

    if len(path) == 0 and location == 'hash':
        path = setlastdir[2]['lastHash']
        return path
    
    while os.path.exists(path) != True:
        print("Directory does not exist; please re-enter.")
        path = input(reply)
    
    if location == 'hash':
        return path

    # appends "/" to end of path if not there.
    if path[-1] not in ['\\', '/']: 
        path += '/' 
    return path

# Delete Confirmation Request
def DeleteFile(pathin, entry,use,reply):
    default_answer = "n"
    confirm = input(reply)
    confirm = confirm.lower()
    if len(confirm) == 0:
        confirm = default_answer
    
    if use == 'hash' and confirm == 'y':
        os.remove(entry)
        print("Duplicate hash entry found, deleting file :" + entry)
        return

    if confirm == "y":
        os.remove(pathin + entry)
        print("FileExistsError: Duplicate file found, deleting file :" + pathin + entry)
        return 

    else:
        print("Skipping deletion...")

    return

#Bulk delete function for any provided list
def BulkDelete(list,reply):
    default_answer = 'n'
    confirm = input(reply)
    confirm = confirm.lower()

    #if length of confirm is 0 set to 'n'
    if len(confirm) == 0:
        confirm = default_answer

    if confirm == 'y':
        for entry in list:
            os.remove(entry)
    else:
       print("Skipping deletion...")

    return

# Folder Directory Creation
def ImageDirCreation(pathout):
    #global search_folders
    ImageResolutions = [{"name": "Low Res", "dimensions": (1440, 900)}, 
                        {"name": "Mid Res", "dimensions":  (1920, 1440)},
                        {"name": "High Res", "dimensions":  (2560, 1600)},
                        {"name": "UHD Res", "dimensions":  (3840, 2160)},
                        {"name": "Phone Res", "dimensions":  (1080, 2400)},
                        {"name": "UHDP Res", "dimensions": (7680, 4320)}] 

    # Resolution folder creation
    #search_folders = []
    for entry in ImageResolutions:
        if not os.path.exists(pathout + entry["name"]):
            #search_folders.append(entry['name'])
            os.makedirs(pathout + entry["name"])
            print(entry["name"] + " folder created!")
        else:
            print("Found " + entry["name"] + " directory; skipping creation")
    return ImageResolutions

# Create Hash List and Compare/ Delete duplicate on prompt.
def FileHashCompare(pathin,hashlist):
    comparelist = []
    hashduplicatelist = []
    #hashlist = []
    # walks files, directories and  subdirectories; then appends them to a list
    for path, subdirs, files in os.walk(pathin):
        for name in files:
            entry = os.path.join(path, name)
            if os.path.isfile(entry):
                comparelist.append(entry)  

    #how many entries for hash compare it finds.  
    print(len(comparelist))

    print("Duplicate file hash check...")
    for entry in comparelist:
        # ignore .ini files (picasa file sorter/similar)
        if entry.lower().endswith(".ini"):
            continue

        # file hash comparison => open(file), "rb" = read binary , read file and digest = hash results
        filehash = hashlib.sha256(open(entry,'rb').read()).hexdigest() 

        # hashlist organizing; comparies directories of the existing hash entry with the duplicate one.
        if filehash not in hashlist:
            hashlist[filehash] = entry

        else:
            if entry != hashlist[filehash]:
                print("added entry " + entry)
                hashduplicatelist.append(entry)

    # bulk delete
    for entry in hashduplicatelist:  
        #if length of my duplicate entries is greater than 5.
        if len(hashduplicatelist) >= 5:
            BulkDelete(hashduplicatelist, 'Delete all '+ str(len(hashduplicatelist))+' files (y/N)?:')
            break
        else:
            DeleteFile(pathin,entry,'hash',"Delete duplicate file? " + entry + "(y/N)?")

    return hashlist

# Organizes Photos into Directories
def FileSorting(pathin, imageres, pathout):
    alist = os.listdir(pathin)
    for entry in alist:
        # directory check 
        if os.path.isdir(pathin + entry):
            print("Found " + entry + " directory; skipping~")
            continue

        # if os.path.basename(pathin) not in search_folders:
        #     #['Naughty', 'Videos', 'Unwanted', 'Fix Me']:
        #     continue

        # ignore .ini files (picasa file sorter/similar)
        if entry.lower().endswith(".ini"):
            #print("Found .ini file; skipping~")
            continue
        if entry.lower().endswith(".db"):
            continue

        # image sorting via dictionary dimensions comparison" > = GREATER THAN | < = LESS THAN "
        Found = False
        try:
            im = Image.open(pathin + entry)
            #imageres is the dictionary with all dimensions
            for move in range(0, len(imageres) - 1): # range function starts at X value and ends at Y-1 (range(X,Y-1)) count = interation value
                imagewidth, imageheight = imageres[move]["dimensions"] # value 1, value 2 = IMGRES[int][dictionary key]
                #if 1440 >= im.width(opened image) and 900 >= im.height(opened image)
                if (imagewidth >= im.width) and (imageheight >= im.height):
                    Found = True
                    break
            im.close()      
        except:
            pass

        # if image doesn't fit any dictionary values place in UHDP folder
        if(not Found):
            continue

        # file moving to new location via os.rename(source, new) function
        # if duplicate file exists; compare via hashlib.sha256 in binary format
        fileoutname = pathout + imageres[move]["name"] + "/" + entry
        try:
            shutil.move(pathin + entry, fileoutname)

        except FileExistsError:
            file1hash = hashlib.sha256(open(pathin + entry,"rb").read()).hexdigest() # file hash comparison => open(file), "rb" = read binary , read file and digest = hash results
            file2hash = hashlib.sha256(open(fileoutname,"rb").read()).hexdigest()

            # compare file1hash to file2hash
            # if files are same; delete file in source folder
            if file1hash == file2hash:
                # Prompt confirmation for deletion
                DeleteFile(pathin, entry,'sort',"Delete duplicate file? " + pathin + entry + "(y/N)?")
            
            else:
                # duplicate file name check and renaming
                dotloc = fileoutname.rfind(".")
                filenum = 2

                while(os.path.exists(fileoutname[0:dotloc] + str(filenum) + fileoutname[dotloc:])):
                    filenum += 1   
                print("Duplicate file name found at " + fileoutname + " --> Renaming file..." + fileoutname[0:dotloc] + str(filenum) + fileoutname[dotloc:])
                shutil.move(pathin + entry, fileoutname[0:dotloc] + str(filenum) + fileoutname[dotloc:])

        except PermissionError as e:
            print(f'Permission Error - Skipping File - {e} ')
            continue
        
        print( im.width, "X", im.height, "|", entry, ">> " + imageres[move]["name"] + " >>", fileoutname)
    return

# maaaaaaaaaaaaain~
def main():
    wd = Path(__file__).parent.absolute()
    filewd = str(wd)
    setfile = "\imagefilter.json"  
    hashfile = '\hashdatabase.json'  

    #Load Default Settings; override with Loaded.
    DefaultSettings()
    setlastdir = LoadSettings(filewd,setfile)

    pathin = UserDirectory(setlastdir,'source','Source directory (lastdir: ' + str(setlastdir[0]['Source']) + '): ')
    pathout = UserDirectory(setlastdir,'output', 'Destination directory (lastdir: ' + str(setlastdir[1]['Output']) + '): ')
    imagefolders = ImageDirCreation(pathout) #This has my Image Resolution dict
    FileSorting(pathin,imagefolders,pathout)


    #complete hash file comparison for all files in directory
    hash = input("hash? 'y/N' :")
    if hash == 'y':
        hashlist = HashDatabaseLoad(hashfile,filewd)
        hashpath = UserDirectory(setlastdir,'hash','Folder or Directory (will scan sub-directories)(lastdir: ' + str(setlastdir[2]['lastHash']) + '): ')
        hashcompare = FileHashCompare(hashpath,hashlist)
        
        HashDatabaseSave(filewd,hashfile,hashcompare)
        SaveSettings(pathin,pathout,filewd,setfile,hashpath)
    else:
        SaveSettings(pathin,pathout,filewd,setfile,wd)
        pass
    

    return 
    
if __name__ == "__main__":
    print("Main Loaded")
    main()