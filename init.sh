#!/bin/bash

#additional config
user=industrial
git=drunktective
script=siap-bca-v2.0

echo "[CONFIG] update packages"
sudo apt-get update
e1=$?

echo "[CONFIG] enable serial"
sudo usermod -a -G dialout,tty $user
e2=$?

echo "[CONFIG] setting git"
yes yes | sudo apt-get install git
git config --global user.name "drunktective"
git config --global user.email "drunktective@ruru.be"
e3=$?

echo "[CONFIG] getting $script"
cd /home/$user
git clone https://github.com/$git/$script
cd $script
e4=$?

echo "[CONFIG] setting watchdog"
yes yes | sudo apt-get install watchdog
sudo cp config/watchdog.conf /etc/watchdog.conf
e5=$?

echo "[CONFIG] enable usb flashdisk to store id"
echo '/dev/sdb1 /media/bcafile vfat defaults 0 0' | sudo tee -a /etc/fstab
e6=$?

echo "[CONFIG] getting siap-bca dependencies"
yes yes | sudo apt-get install python3-pip
pip3 install -r "config/libs.txt"
e7=$?

echo "[CONFIG] config bca.service"
sudo cp config/bca.service /etc/systemd/system/bca.service
sudo systemctl daemon-reload
sudo systemctl enable bca.service
e8=$?

errorinfo=($e1,$e2,$e3,$e4,$e5,$e6,$e7,$e8)
echo "[CONFIG] setting config done. recheck error code >> $errorinfo"
echo "[CONFIG] reboot required!"