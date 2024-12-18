# Printing to a Brother Laser From the command line on Linux

This will work from WSL and the only assumption it makes is your printer is connected on 192.168.1.5.


```sh
sudo apt-get update
sudo apt-get install cups-client cups-pdf printer-driver-brlaser
sudo lpadmin -p "MFC-L2740DW" -E -v ipp://192.168.1.5/ipp/print -m everywhere
cd /mnt/c/Users/JustinDearing/source/repos/christmas-cards/
lp -d MFC-L2740DW avery_5160_labels.pdf
```
