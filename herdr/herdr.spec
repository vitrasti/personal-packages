# Herdr is not in the Fedora repositories.
#
# Fedora CoreOS / rpm-ostree notes:
# - No scriptlets of any kind; safe for ostree layering.
# - All payload installs under /usr (part of the ostree image).
# - Updates are owned by the package manager (rpm-ostree / dnf from this
#   COPR). Herdr has a built-in updater (`herdr update`), but when installed
#   via rpm-ostree the package manager owns the binary path.
#
# The vendored libghostty-vt (vendor/libghostty-vt) is a Zig library built
# by the ghostty-vt Rust crate's build.rs. It requires Zig 0.16, which is
# the version shipped in Fedora's base repos (the zig017 package in this
# COPR is for Ghostty 1.4+ which needs 0.17; they conflict).
#
# The portable-pty crate is patched via [patch.crates-io] to use a vendored
# copy (vendor/portable-pty), so no external git dependency is needed.

%global debug_package %{nil}
%undefine _package_note_file

Name:           herdr
Version:        0.9.5
Release:        1%{?dist}
Summary:        Terminal workspace manager for AI coding agents

License:        Apache-2.0
URL:            https://github.com/herdrdev/herdr
Source0:        %{url}/archive/refs/tags/v%{version}/%{name}-%{version}.tar.gz

# Herdr's rust-toolchain.toml pins 1.96.1; Fedora 45 ships 1.100.
BuildRequires:  cargo >= 1.96
BuildRequires:  rust >= 1.96
# Linker driver for the Rust build; the vendored libghostty-vt is compiled
# by zig's own C compiler (zig cc), so gcc is only needed for linking.
BuildRequires:  gcc
# zig 0.16 from Fedora base; used by crates/ghostty-vt/build.rs to compile
# the vendored libghostty-vt static archive.
BuildRequires:  zig

%description
Herdr is a terminal workspace manager for AI coding agents. It keeps
terminals running in a background server when you close the client or
lose your SSH connection, supports multiple machines in one window,
and provides agent-native integrations via CLI and socket API.

%prep
%autosetup

%build
# --locked for reproducible builds; the Cargo.lock is committed at the tag.
# The ghostty-vt build script (crates/ghostty-vt/build.rs) invokes
# `zig build -Demit-lib-vt` in vendor/libghostty-vt to produce the
# static archive, which cargo then links into the final binary.
export RUSTFLAGS='-C strip=symbols'
cargo build --release --locked

%install
install -Dpm 0755 target/release/%{name} %{buildroot}%{_bindir}/%{name}

# Generate shell completions using the built binary.
install -d "%{buildroot}%{_datadir}/bash-completion/completions"
target/release/%{name} completion bash \
    > "%{buildroot}%{_datadir}/bash-completion/completions/%{name}"

install -d "%{buildroot}%{_datadir}/fish/vendor_completions.d"
target/release/%{name} completion fish \
    > "%{buildroot}%{_datadir}/fish/vendor_completions.d/%{name}.fish"

install -d "%{buildroot}%{_datadir}/zsh/site-functions"
target/release/%{name} completion zsh \
    > "%{buildroot}%{_datadir}/zsh/site-functions/_%{name}"

%check
target/release/%{name} --version | grep -q "%{version}"

%files
%license LICENSE
%doc README.md
%{_bindir}/%{name}
%{_datadir}/bash-completion/completions/%{name}
%{_datadir}/fish/vendor_completions.d/%{name}.fish
%{_datadir}/zsh/site-functions/_%{name}

%changelog
* Tue Nov 24 2026 vitrasti <vitrasti@protonmail.com> - 0.9.5-1
- Initial package for personal COPR
