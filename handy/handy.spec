Name:           handy
Version:        0.9.4
Release:        1%{?dist}
Summary:        Free, open-source, offline speech-to-text application
License:        MIT
URL:            https://handy.computer/
# Binary republish of the official Tauri-built RPM
Source0:        https://github.com/cjpais/Handy/releases/download/v%{version}/Handy-%{version}-1.x86_64.rpm
# For aarch64 builds change Source0 to Handy-%%{version}-1.aarch64.rpm
ExclusiveArch:  x86_64
BuildRequires:  rpmdevtools
BuildRequires:  cpio

# Prebuilt binaries: skip debuginfo extraction and stripping
%global debug_package %{nil}
%global __brp_strip %{nil}
%global __brp_strip_static_archive %{nil}
%global __brp_strip_comment_note %{nil}

# Explicit deps from tauri.conf.json + auto-detected ones
Requires:       libgtk-layer-shell.so.0()(64bit)
Requires:       libopenblas.so.0()(64bit)
Requires:       libappindicator3.so.1()(64bit)
Requires:       libwebkit2gtk-4.1.so.0()(64bit)
Requires:       libgtk-3.so.0()(64bit)

# Nice-to-have package names (helps dnf resolve on Fedora)
Requires:       gtk-layer-shell
Requires:       openblas
Requires:       libappindicator-gtk3
Requires:       webkit2gtk4.1
Requires:       gtk3

%description
Handy is a free, open source, and extensible speech-to-text application
that works completely offline. Press a shortcut, speak, and the
transcription is pasted into the focused text field. Uses Whisper /
Parakeet models locally.

%prep
# nothing

%build
# nothing — binary package

%install
mkdir -p %{buildroot}
# Extract the upstream RPM payload straight into the build root
rpm2cpio %{SOURCE0} | cpio -idmv -D %{buildroot}

%files
/usr/bin/handy
/usr/lib/Handy/
/usr/share/applications/Handy.desktop
/usr/share/icons/hicolor/32x32/apps/handy.png
/usr/share/icons/hicolor/128x128/apps/handy.png
/usr/share/icons/hicolor/256x256@2/apps/handy.png

%changelog
* Tue Jul 21 2026 vitrasti <vitrasti@protonmail.com> - 0.9.4-1
- Initial COPR package (binary republish of upstream Tauri RPM)
