%global debug_package %{nil}
%undefine _package_note_file

Name: zellij
Version: 0.44.1
Release: 1%{?dist}
Summary: A terminal workspace with batteries included

License: MIT
URL: https://github.com/zellij-org/zellij
Source0: %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires: cargo >= 1.92
BuildRequires: rust >= 1.92
BuildRequires: gcc
BuildRequires: cmake
BuildRequires: make
BuildRequires: perl-devel
BuildRequires: openssl-perl
BuildRequires: perl-FindBin
BuildRequires: perl-IPC-Cmd

%description
Zellij is a workspace aimed at developers, ops-oriented people and anyone who
loves the terminal. At its core, it is a terminal multiplexer (similar to tmux
and screen), but this is merely its infrastructure layer. Zellij includes a
layout system, and a plugin system allowing one to create plugins in any
language that compiles to WebAssembly.

%prep
%autosetup

%install
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_OPT_LEVEL=3
RUSTFLAGS='-C strip=symbols' cargo install --root=%{buildroot}%{_prefix} --path=.
rm -f %{buildroot}%{_prefix}/.crates.toml \
    %{buildroot}%{_prefix}/.crates2.json

%files
%license LICENSE.md
%doc README.md CONTRIBUTING.md
%{_bindir}/%{name}

%changelog
* Sun Aug 09 2026 vitrasti <vitrasti@protonmail.com> - 0.44.1-1
- Initial release for personal copr repo.
