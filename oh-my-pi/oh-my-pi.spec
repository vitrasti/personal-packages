# Package the official standalone Bun executable without modifying its payload.
%global debug_package %{nil}
%global __strip /bin/true

Name:           oh-my-pi
Version:        18.8.2
Release:        1%{?dist}
Summary:        Terminal coding agent with code intelligence and native tools

# First-party MIT plus bundled code/data licenses listed in upstream notices.
License:        MIT AND Apache-2.0 AND ISC AND BSD-2-Clause AND BSD-3-Clause AND 0BSD AND BSL-1.0 AND CC0-1.0 AND CC-BY-4.0 AND CDDL-1.0 AND Unicode-3.0 AND WTFPL AND Zlib
URL:            https://github.com/can1357/oh-my-pi

# Include both architectures in the SRPM for multi-arch COPR builds.
Source0:        %{url}/releases/download/v%{version}/omp-linux-x64#/%{name}-%{version}-linux-x64
Source1:        %{url}/releases/download/v%{version}/omp-linux-arm64#/%{name}-%{version}-linux-arm64
Source2:        LICENSE
Source3:        %{url}/releases/download/v%{version}/THIRD-PARTY-NOTICES.txt#/%{name}-%{version}-THIRD-PARTY-NOTICES.txt
Source4:        %{url}/raw/v%{version}/README.md#/%{name}-%{version}-README.md

ExclusiveArch:  x86_64 aarch64

# Embedded native addons are extracted and loaded by Bun at runtime, so RPM
# cannot discover their ELF requirements by scanning the installed executable.
Requires:       libutil.so.1()(64bit)
Suggests:       git

BuildRequires:  bash

%description
Oh My Pi is a terminal coding agent based on Pi, with language server
integration, session management, extensions, and built-in native tools.

This package installs the upstream standalone executable as omp. Runtime
assets are embedded; no separate Bun or Node.js installation is needed for
the core CLI. Optional feature runtimes are managed by upstream setup commands.

On Fedora CoreOS and other rpm-ostree systems, update this package through
the package manager instead of using omp update to replace files in /usr.

%prep
%setup -q -c -n %{name}-%{version} -T
cp -p %{SOURCE2} LICENSE
cp -p %{SOURCE3} THIRD-PARTY-NOTICES.txt
cp -p %{SOURCE4} README.md

%build
# Standalone executable - nothing to compile.

%install
%ifarch x86_64
install -Dpm0755 %{SOURCE0} %{buildroot}%{_bindir}/omp
%endif
%ifarch aarch64
install -Dpm0755 %{SOURCE1} %{buildroot}%{_bindir}/omp
%endif

# Generate completions from the packaged CLI metadata.
install -dm0755 %{buildroot}%{_datadir}/bash-completion/completions
install -dm0755 %{buildroot}%{_datadir}/zsh/site-functions
install -dm0755 %{buildroot}%{_datadir}/fish/vendor_completions.d
%{buildroot}%{_bindir}/omp completions bash > %{buildroot}%{_datadir}/bash-completion/completions/omp
%{buildroot}%{_bindir}/omp completions zsh > %{buildroot}%{_datadir}/zsh/site-functions/_omp
%{buildroot}%{_bindir}/omp completions fish > %{buildroot}%{_datadir}/fish/vendor_completions.d/omp.fish

%check
version=$(%{buildroot}%{_bindir}/omp --version)
test "$version" = "omp/%{version}"
test -s %{buildroot}%{_datadir}/bash-completion/completions/omp
test -s %{buildroot}%{_datadir}/zsh/site-functions/_omp
test -s %{buildroot}%{_datadir}/fish/vendor_completions.d/omp.fish

%files
%license LICENSE THIRD-PARTY-NOTICES.txt
%doc README.md
%{_bindir}/omp
%{_datadir}/bash-completion/completions/omp
%{_datadir}/zsh/site-functions/_omp
%{_datadir}/fish/vendor_completions.d/omp.fish

%changelog
* Wed Oct 07 2026 vitrasti <vitrasti@protonmail.com> - 18.8.2-1
- Update to 18.8.2

* Tue Oct 06 2026 vitrasti <vitrasti@protonmail.com> - 18.6.3-1
- Update to 18.6.3

* Sun Oct 04 2026 vitrasti <vitrasti@protonmail.com> - 18.6.1-1
- Initial package for personal COPR
- Install the official standalone executable and shell completions
- Include upstream license and third-party notices
