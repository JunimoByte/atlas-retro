#!/usr/bin/env bash
# Build Atlas AppDir and DEB inside Ubuntu 14.04 (Trusty) container.

set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive

echo "==> Configuring Ubuntu 14.04 Trusty APT repositories..."
sed -i -e "s/main$/main universe/" -e "s/main restricted$/main restricted universe/" /etc/apt/sources.list
apt-get update || {
  sed -i -e "s/archive.ubuntu.com\|security.ubuntu.com/old-releases.ubuntu.com/g" /etc/apt/sources.list
  apt-get update
}

echo "==> Installing native build dependencies and PyQt4..."
apt-get install -y --no-install-recommends \
  python3 \
  python3-dev \
  python3-setuptools \
  python3-pyqt4 \
  build-essential \
  pkg-config \
  binutils \
  dpkg-dev \
  file \
  ca-certificates

# Ensure python points to python3
ln -sf /usr/bin/python3 /usr/local/bin/python
ln -sf /usr/bin/python3 /usr/local/bin/python3

echo "==> Deploying offline build dependencies and PyInstaller 3.3.1..."
python3 -c "import zipfile, glob, os, sys; target = '/usr/local/lib/python3.4/dist-packages'; os.path.exists(target) or os.makedirs(target); [zipfile.ZipFile(w).extractall(target) for w in glob.glob('.cache/build/*.whl')]"

tar -xzf .cache/build/PyInstaller-3.3.1.tar.gz -C /tmp/
(cd /tmp/PyInstaller-3.3.1 && python3 setup.py install)

echo "==> Building AppDir and Debian package..."
bash scripts/build_appimage.sh
bash scripts/build_deb.sh

echo "==> Setting permissions on build outputs..."
chmod -R a+rX dist/
rm -rf .cache/build/PyInstaller-3.3.1 /tmp/PyInstaller-3.3.1 build

echo "==> Container build completed successfully."
