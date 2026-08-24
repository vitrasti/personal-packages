%global debug_package %{nil}
%undefine _package_note_file

Name:           mise
Version:        2026.8.12
Release:        1%{?dist}
Summary:        Dev tools, env vars, and tasks in one CLI

License:        MIT
URL:            https://github.com/jdx/mise
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cargo
BuildRequires:  rust >= 1.95
BuildRequires:  gcc
BuildRequires:  cmake
BuildRequires:  git
BuildRequires:  pkgconfig(openssl)
BuildRequires:  pkgconfig(zlib)

%description
mise prepares your development environment before each command runs. It installs
and switches between project tools, loads environment variables, and runs tasks
from the same configuration.

%prep
%autosetup

%install
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_OPT_LEVEL=3
# Drop self_update so package/rpm-ostree owns upgrades (required on immutable
# Fedora CoreOS where /usr cannot be rewritten in place). Keep the rest of the
# upstream default feature set: native-tls + vendored lua for vfox.
RUSTFLAGS='-C strip=symbols' \
    cargo install \
        --root=%{buildroot}%{_prefix} \
        --path=. \
        --locked \
        --ignore-rust-version \
        --no-default-features \
        --features native-tls,vfox/vendored-lua
rm -f %{buildroot}%{_prefix}/.crates.toml \
    %{buildroot}%{_prefix}/.crates2.json

install -Dpm0644 man/man1/mise.1 %{buildroot}%{_mandir}/man1/mise.1

install -Dpm0644 completions/mise.bash \
    %{buildroot}%{_datadir}/bash-completion/completions/mise
install -Dpm0644 completions/_mise \
    %{buildroot}%{_datadir}/zsh/site-functions/_mise
install -Dpm0644 completions/mise.fish \
    %{buildroot}%{_datadir}/fish/vendor_completions.d/mise.fish

# Install under /usr/lib (not /opt) so the package layers cleanly on
# rpm-ostree/immutable Fedora, where /opt is typically a symlink to /var/opt.
# mise looks for this file relative to the install prefix (lib/mise/...).
mkdir -p %{buildroot}%{_prefix}/lib/mise
cat > %{buildroot}%{_prefix}/lib/mise/mise-self-update-instructions.toml <<'TOML'
message = "To update mise, run:\n\n  sudo dnf upgrade mise\n\nOn Fedora CoreOS / rpm-ostree:\n\n  sudo rpm-ostree upgrade\n"
TOML

%check
%{buildroot}%{_bindir}/mise --version | grep -Fqe "%{version}"

%files
%license LICENSE
%doc README.md
%{_bindir}/mise
%{_mandir}/man1/mise.1*
%{_datadir}/bash-completion/completions/mise
%{_datadir}/zsh/site-functions/_mise
%{_datadir}/fish/vendor_completions.d/mise.fish
%dir %{_prefix}/lib/mise
%{_prefix}/lib/mise/mise-self-update-instructions.toml

%changelog
* Mon Aug 24 2026 vitrasti <vitrasti@protonmail.com> - 2026.8.12-1
- Initial release for personal copr repo.
- Build without self_update for package/rpm-ostree managed upgrades
- Install update instructions under /usr/lib/mise for Fedora CoreOS
