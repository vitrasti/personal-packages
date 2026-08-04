%global toolchain clang
%global crate zed
%global appid dev.zed.Zed

%global rustflags_debuginfo 0

Name:           zed
Version:        1.13.2
Release:        1%{?dist}
Summary:        High-performance, multiplayer code editor

License:        Apache-2.0 AND GPL-3.0-or-later AND MIT AND BSD-2-Clause AND BSD-3-Clause AND ISC AND MPL-2.0 AND Zlib AND CC0-1.0 AND Unicode-3.0
URL:            https://zed.dev/
Source0:        https://github.com/zed-industries/zed/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  cargo
BuildRequires:  rust
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  clang
BuildRequires:  cmake
BuildRequires:  mold
BuildRequires:  gettext-envsubst
BuildRequires:  alsa-lib-devel
BuildRequires:  fontconfig-devel
BuildRequires:  wayland-devel
BuildRequires:  libxkbcommon-x11-devel
BuildRequires:  openssl-devel
BuildRequires:  libzstd-devel
BuildRequires:  libcurl-devel
BuildRequires:  vulkan-loader
BuildRequires:  perl-FindBin
BuildRequires:  perl-IPC-Cmd
BuildRequires:  perl-File-Compare
BuildRequires:  perl-File-Copy
BuildRequires:  perl-lib
%ifarch x86_64
BuildRequires:  libedit(x86-64)
%endif

Requires:       hicolor-icon-theme

%description
Zed is a high-performance, multiplayer code editor from the creators of Atom
and Tree-sitter. It is designed for speed and collaboration.

%prep
%autosetup -n %{crate}-%{version} -p1

# Do NOT use %%cargo_prep – it forces offline mode and Zed needs git deps.
# COPR has network enabled, so we let cargo fetch normally.
mkdir -p .cargo

# Generate .desktop and AppStream metadata
export DO_STARTUP_NOTIFY="true"
export APP_ID="%{appid}"
export APP_ICON="%{appid}"
export APP_NAME="Zed"
export APP_CLI="zed"
export APP="%{_libexecdir}/zed-editor"
export APP_ARGS="%U"
export ZED_UPDATE_EXPLANATION="Update the zed package."
export ZED_RELEASE_CHANNEL=stable
export BRANDING_LIGHT="#e9aa6a"
export BRANDING_DARK="#1a5fb4"

envsubst < crates/zed/resources/zed.desktop.in > %{appid}.desktop
sed -i 's|@release_info@||g' crates/zed/resources/flatpak/zed.metainfo.xml.in
envsubst < crates/zed/resources/flatpak/zed.metainfo.xml.in > %{appid}.metainfo.xml

%build
echo "stable" > crates/zed/RELEASE_CHANNEL
export ZED_UPDATE_EXPLANATION="Update the zed package."

# Compiled into the binary via option_env!("RELEASE_VERSION"); without it
# `zed --version` and the About dialog report a blank version.
export RELEASE_VERSION=%{version}

# Online build (network is available on COPR)
export CARGO_HOME=%{_builddir}/.cargo
cargo build -j%{?_smp_ncpus_max}%{!?_smp_ncpus_max:4} \
    --release \
    --package zed \
    --package cli

%install
# Binaries land in target/release/ with a normal --release build
install -Dm755 target/release/zed %{buildroot}%{_libexecdir}/zed-editor
install -Dm755 target/release/cli %{buildroot}%{_bindir}/zed

install -Dm644 %{appid}.desktop %{buildroot}%{_datadir}/applications/%{appid}.desktop
install -Dm644 crates/zed/resources/app-icon.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{appid}.png
install -Dm644 %{appid}.metainfo.xml %{buildroot}%{_metainfodir}/%{appid}.metainfo.xml

%files
%doc README.md CODE_OF_CONDUCT.md
%license LICENSE-APACHE LICENSE-GPL
%{_bindir}/zed
%{_libexecdir}/zed-editor
%{_datadir}/applications/%{appid}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{appid}.png
%{_metainfodir}/%{appid}.metainfo.xml

%changelog
* Mon Aug 03 2026 vitrasti <vitrasti@protonmail.com> - 1.13.2-1
- Initial package for personal COPR
