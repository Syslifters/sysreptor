#!/bin/bash
set -e

skip_license () {
  copyright_file="$1"
  if test -f "$copyright_file"; then
    license=`cat "$copyright_file" | grep -m 1 "^License:" | cut -d" " -f 2`
    if test -n "$license" && echo "$skip_licenses" | grep -wq "$license"; then
      return 0
    fi
  fi
  return 1
}

fetch_source() {
  package="$1"
  package_name=`echo $package | cut -d= -f1 | cut -d: -f1`
  if echo "$skip_packages" | grep -wq "$package_name"; then
    echo "Skipping $package"
    return
  fi
  if skip_license "/usr/share/doc/$package_name/copyright"; then
    echo "$package_name (installed) $license license doesn't require source code distribution"
    return
  fi
  echo "Fetching $package"
  mkdir "$package"
  cd "$package"
  apt-get source "$package" --download-only > /dev/null 2>&1
  cd ..
  echo "Done $package"
}

skip_packages="fonts-dejavu-core
libgl1
libglvnd0
libglx0
libtiff6
fontconfig
fontconfig-config
fonts-noto-color-emoji
libavahi-client3
libavahi-common-data
libavahi-common3
libcairo-gobject2
libcairo2
libdrm-amdgpu1
libdrm-common
libdrm-intel1
libdrm-nouveau2
libdrm-radeon1
libdrm2
libfontconfig1
libfontenc1
libice6
libpciaccess0
libpixman-1-0
libsensors-config
libsensors5
libsm6
libwebp7
libx11-6
libx11-data
libx11-xcb1
libxau6
libxaw7
libxcb-dri2-0
libxcb-dri3-0
libxcb-glx0
libxcb-present0
libxcb-randr0
libxcb-render0
libxcb-shape0
libxcb-shm0
libxcb-sync1
libxcb-xfixes0
libxcb1
libxcomposite1
libxcursor1
libxdamage1
libxdmcp6
libxext6
libxfixes3
libxft2
libxi6
libxinerama1
libxkbcommon0
libxkbfile1
libxmu6
libxmuu1
libxpm4
libxrandr2
libxrender1
libxshmfence1
libxslt1.1
libxt6
libxtst6
libxv1
libxxf86dga1
libxxf86vm1
unzip
x11-common
x11-utils
xfonts-encodings
xfonts-utils
xkb-data"

skip_licenses="MIT
curl
CC-BY-SA-3.0
LGPL-2+
BSD-3-clause
OFL-1.1
SIL-1.1
CC0
LPGL-2.1+
APACHE-2-LLVM-EXCEPTIONS
Apache-2.0-with-GPL2-LGPL2-Exception
BSD-2-clause
Expat
FTL
BSD-BY-LC-NE
Apache-2.0
zlib
BSD-2
libpng
PostgreSQL
X11
MIT-1"

cd /src
sed -i "s/^Types: deb$/Types: deb deb-src/" /etc/apt/sources.list.d/*.sources
apt-get update > /dev/null 2>&1

# Diff with previously installed packages
for package in `grep -Fxv -f pre_installed.txt post_installed.txt`; do
  fetch_source "$package"
done

apt-get clean > /dev/null 2>&1
rm -rf /var/lib/apt/lists/*