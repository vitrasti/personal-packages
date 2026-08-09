%global debug_package %{nil}
%undefine _package_note_file

Name: starship
Version: 1.26.0
Release: 1%{?dist}
Summary: Minimal, blazing-fast, and infinitely customizable prompt for any shell!

License: ISC
URL: https://github.com/starship/starship
Source0: %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires: cargo >= 1.74
BuildRequires: cmake4
BuildRequires: gcc
BuildRequires: rust >= 1.74
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(zlib)

%description
Minimal, blazing-fast, and infinitely customizable prompt for any shell!

%prep
%autosetup

%install
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_OPT_LEVEL=3
export CMAKE=cmake4
RUSTFLAGS='-C strip=symbols' cargo install --root=%{buildroot}%{_prefix} --path=.
rm -f %{buildroot}%{_prefix}/.crates.toml \
    %{buildroot}%{_prefix}/.crates2.json

%files
%license LICENSE
%doc README.md CONTRIBUTING.md
%{_bindir}/%{name}

%changelog
* Sun Aug 09 2026 vitrasti <vitrasti@protonmail.com> - 1.26.0
- Initial release for personal copr repo.
