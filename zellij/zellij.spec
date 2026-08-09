%global debug_package %{nil}
%undefine _package_note_file

Name: zellij
Version: 0.44.1
Release: 3%{?dist}
Summary: A terminal workspace with batteries included

License: MIT
URL: https://github.com/zellij-org/zellij
Source0: %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires: cargo >= 1.92
BuildRequires: rust >= 1.92
BuildRequires: gcc
BuildRequires: cmake
BuildRequires: make
# Use system curl/OpenSSL instead of zellij's default vendored_curl feature
# (which builds OpenSSL from source via openssl-sys and needs a pile of Perl).
BuildRequires: pkgconfig(libcurl)
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(zlib)

%description
Zellij is a workspace aimed at developers, ops-oriented people and anyone who
loves the terminal. At its core, it is a terminal multiplexer (similar to tmux
and screen), but this is merely its infrastructure layer. Zellij includes a
layout system, and a plugin system allowing one to create plugins in any
language that compiles to WebAssembly.

%prep
%autosetup
# Fedora 45+/rawhide ships OpenSSL 4. Upstream's lockfile pins openssl-sys
# 0.9.111, which only accepts OpenSSL <= 3.x. 0.9.114+ adds OpenSSL 4 support.
# Keep F43/F44 on the locked deps unchanged.
%if 0%{?fedora} >= 45
cargo update -p openssl-sys --precise 0.9.117
%endif

%install
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_OPT_LEVEL=3
# Default features include vendored_curl; drop it and keep the rest.
RUSTFLAGS='-C strip=symbols' \
    cargo install \
        --root=%{buildroot}%{_prefix} \
        --path=. \
        --locked \
        --no-default-features \
        --features plugins_from_target,web_server_capability
rm -f %{buildroot}%{_prefix}/.crates.toml \
    %{buildroot}%{_prefix}/.crates2.json

%files
%license LICENSE.md
%doc README.md CONTRIBUTING.md
%{_bindir}/%{name}

%changelog
* Sun Aug 09 2026 vitrasti <vitrasti@protonmail.com> - 0.44.1-3
- Rawhide/F45+: bump openssl-sys to 0.9.117 for OpenSSL 4 compatibility

* Sun Aug 09 2026 vitrasti <vitrasti@protonmail.com> - 0.44.1-2
- Build against system libcurl/OpenSSL instead of vendored OpenSSL
- Use cargo --locked for reproducible dependency resolution

* Sun Aug 09 2026 vitrasti <vitrasti@protonmail.com> - 0.44.1-1
- Initial release for personal copr repo.
