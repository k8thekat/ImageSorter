A simple script to automating sorting of an ongoing library of pictures.

Simply hit `enter` on any prompt you want to use "default" setting, otherwise enter `"y"`

Run the script, by default you will get prompts for settings.
1. Would you like to seperate Wallpaper sized pictures into their own folder? 'y/N' (default: N)
2. Would you like the search to recursive? 'y/N' (default: N)
3. Would you like to check for duplicate images? 'y/N' (default: N)
4. Source Directory of the images.
5. Destination Directory - *(note- This is where the folder's will be created if they do not exists)*

It will do basic `256 hash comparisson` of images and store the hash and file directory of the image to a json file for reference.

| Resolution Name/ Folder Name | Resolution Minimum |
|------------------------------------|------------------------|
| Phone Res | 1080 x 2400 |
| Low Res  | 1440 x 900 |
| Mid Res | 1920 x 1400 |
| High Res | 2560 x 1600 |
| UHD Res | 3840 x 2160 |
| UHDP Res | 9000 x 9000 |

Once finished a prompt will appear to delete duplicate images; if 5 or more duplicate images it will prompt for bulk delete. Otherwise it will prompt for each image deletion.