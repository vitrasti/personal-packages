Name:		signal-desktop
Version:	8.23.0
Release:	1%{?dist}
Summary:	Private messaging from your desktop
License:	GPLv3
URL:		https://github.com/signalapp/Signal-Desktop/

Source0:	https://github.com/signalapp/Signal-Desktop/archive/v%{version}.tar.gz
Source1:	nan+2.22.2.patch

BuildRequires: binutils git gcc gcc-c++ openssl-devel bsdtar jq zlib xz ca-certificates git-lfs ruby-devel python-unversioned-command yarnpkg npm python3 libxcrypt-compat vips-devel pulseaudio-libs

AutoReqProv: no
Provides: signal-desktop
Requires: libnotify, libXtst, nss

%global __requires_exclude_from ^/%{_libdir}/%{name}/release/.*$
%define _build_id_links none

%description
Private messaging from your desktop

%prep
# https://bugzilla.redhat.com/show_bug.cgi?id=1793722
export SOURCE_DATE_EPOCH="$(date +"%s")"

# git-lfs hook needs to be installed for one of the dependencies
git lfs install

rm -rf Signal-Desktop-%{version}
tar xfz %{S:0}

cd Signal-Desktop-%{version}

# remove unneeded but pre-packaged patches
rm -f patches/socks-proxy-agent*

# replace outdated patch (required)
cp %{S:1} patches/nan+2.22.2.patch

# Allow higher Node versions
sed 's#"node": "#&>=#' -i package.json

%build
# https://bugzilla.redhat.com/show_bug.cgi?id=1793722
export SOURCE_DATE_EPOCH="$(date +"%s")"

cd %{_builddir}/Signal-Desktop-%{version}

# install nvm, nodejs and pnpm using the instructions from reproducible-builds/Dockerfile

NODE_VERSION=`cat .nvmrc`
NVM_VERSION=0.40.2
NVM_DIR=$HOME/.nvm/
PNPM_VERSION=`grep packageManager package.json | cut -f2 -d':' |tr -d ','| tr -d '"'|tr -d ' '`

export NODE_VERSION NVM_VERSION NVM_DIR

mkdir -p $NVM_DIR

# download and install nvm and set node version to required value
curl -o- "https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh" | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias $NODE_VERSION \
    && nvm use $NODE_VERSION

NODE_PATH=$NVM_DIR/v$NODE_VERSION/lib/node_modules
PATH=$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

export NODE_PATH PATH

# Install pnpm
npm install -g $PNPM_VERSION

# the following commands are taken from reproducible-builds/docker-entrypoint.sh
pnpm install --frozen-lockfile
pnpm run clean-transpile
cd sticker-creator
pnpm install --frozen-lockfile
pnpm run build
cd ..
pnpm run generate

# quick hack to overcome the 'Your node_modules directory is out of sync with the pnpm-lock.yaml file' issue
sed -i 's/verifyDepsBeforeRun: prompt/verifyDepsBeforeRun: warn/g' pnpm-workspace.yaml

pnpm run prepare-linux-build
pnpm run build-linux

%install
%global PACKDIR linux-unpacked

# copy base files
install -dm755 %{buildroot}/%{_libdir}/%{name}
cp -a %{_builddir}/Signal-Desktop-%{version}/release/%{PACKDIR}/* %{buildroot}/%{_libdir}/%{name}

install -dm755 %{buildroot}%{_bindir}
ln -s %{_libdir}/%{name}/signal-desktop %{buildroot}%{_bindir}/signal-desktop

install -dm755 %{buildroot}%{_datadir}/applications/
cat << EOF > %{buildroot}%{_datadir}/applications/signal-desktop.desktop
[Desktop Entry]
Name=Signal
Exec=/usr/bin/signal-desktop --use-tray-icon %U
Terminal=false
Type=Application
Icon=signal-desktop
StartupWMClass=signal
Comment=Private messaging from your desktop
MimeType=x-scheme-handler/sgnl;
Categories=Network;InstantMessaging;Chat;
EOF

for i in 16 24 32 48 64 128 256 512 1024; do
    install -dm755 %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/
    install -Dm 644 %{_builddir}/Signal-Desktop-%{version}/build/icons/png/${i}x${i}.png %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/%{name}.png
done

%files
%defattr(-,root,root)
%{_bindir}/*
%{_libdir}/*
%{_datadir}/*

%changelog
* Sun Aug 16 2026 vitrasti <vitrasti@protonmail.com> - 8.23.0-1
- Update to 8.23.0

* Mon Aug 03 2026 vitrasti <vitrasti@protonmail.com> - 8.21.0-1
- Cleaned x86_64-only
