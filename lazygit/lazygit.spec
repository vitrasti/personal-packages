%global debug_package %{nil}

Name:           lazygit
Version:        0.64.1
Release:        1%{?dist}
Summary:        Simple, pragmatic TUI (Terminal UI) frontend for GIT

License:        MIT
URL:            https://github.com/jesseduffield/lazygit
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  git-core >= 2.0
%if 0%{?fedora}
BuildRequires:  go-md2man
%endif
# 1.22 is the version where they introduced the `GOTOOLCHAIN=auto`
BuildRequires:  golang >= 1.22

%description
Simple, pragmatic TUI (Terminal UI) frontend for GIT. Written in Go with the
gocui library.

From the official GIT repository:

Rant time: You've heard it before, git is powerful, but what good is that
power when everything is so damn hard to do? Interactive rebasing requires you
to edit a goddamn TODO file in your editor? Are you kidding me? To stage part
of a file you need to use a command line program to step through each hunk and
if a hunk can't be split down any further but contains code you don't want to
stage, you have to edit an arcane patch file by hand? Are you KIDDING me?!
Sometimes you get asked to stash your changes when switching branches only to
realise that after you switch and unstash that there weren't even any
conflicts and it would have been fine to just checkout the branch directly?
YOU HAVE GOT TO BE KIDDING ME!

If you're a mere mortal like me and you're tired of hearing how powerful git
is when in your daily life it's a powerful pain in your ass, lazygit might be
for you.

%prep
%autosetup -p1

%build
# Fetch modules from the Go proxy; upstream does not ship a vendor/ directory.
export GOPROXY=https://proxy.golang.org
export GOFLAGS=-mod=mod
export CGO_ENABLED=0

go build \
    -ldflags "-X main.version=%{version}" \
    -o _build/%{name}

%if 0%{?fedora}
# Man page
go-md2man -in README.md -out %{name}.1
%endif

%install
install -Dpm 0755 _build/%{name} %{buildroot}%{_bindir}/%{name}

%if 0%{?fedora}
# Man page
install -Dpm 0644 %{name}.1 %{buildroot}%{_mandir}/man1/%{name}.1
%endif

%check
./_build/%{name} --version | grep -q "%{version}"

%files
%license LICENSE
%doc README.md CONTRIBUTING.md docs/
%{_bindir}/%{name}
%if 0%{?fedora}
%{_mandir}/man1/*.1*
%endif

%changelog
* Sun Aug 16 2026 vitrasti <vitrasti@protonmail.com> - 0.64.1-1
- Update to 0.64.1

* Sun Aug 09 2026 vitrasti <vitrasti@protonmail.com> - 0.64.0-1
- Initial release for personal copr repo.
