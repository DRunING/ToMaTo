#!/bin/bash

while read distro; do
  case $distro in
    wheezy|jessie)
      type=debian
      ;;
    lucid|natty|oneiric|precise|quantal|raring|saucy|trusty|utopic|vivid|wily|xenial|yakkety)
      type=ubuntu
      ;;
  esac
  for arch in i386 amd64; do
    mkdir -p $distro/$arch
    for file in linux initrd.gz; do
      wget -c ftp://ftp.uni-kl.de/pub/linux/$type/dists/$distro/main/installer-$arch/current/images/netboot/$type-installer/$arch/$file -O $distro/$arch/$file
    done
  done
done < ../distros.build.txt
