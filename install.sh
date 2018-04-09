#!/bin/sh

if [ "$(id -u)" != "0" ] ; then
    echo "Please, run as root!"
    exit 1
fi

echo "==> Cloning the repository"
git clone https://github.com/WEEE-Open/turbofresa
echo "==> Installing the new version"
cd turbofresa
mv turbofresa /usr/bin
cd ..
rm -fr turbofresa

if [ ! -d /home/$USER/.local ]; then
    mkdir /home/$USER/.local
fi

if [ ! -d /home/$USER/.local/share ]; then
    mkdir /home/$USER/.local/share
fi

if [ ! -d /home/$USER/.local/share/turbofresa ]; then
   mkdir /home/$USER/.local/share/turbofresa
fi

echo "Done!"
