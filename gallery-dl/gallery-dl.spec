Name:           gallery-dl
Version:        1.32.9
Release:        1%{?dist}
License:        GPL-2.0-or-later
Summary:        Command-line program to download image galleries and collections
Url:            https://codeberg.org/mikf/gallery-dl
Source:         https://codeberg.org/mikf/%{name}/releases/download/v%{version}/gallery_dl-%{version}.tar.gz
BuildRequires:  pkgconfig(python3)
BuildRequires:  python3dist(pip)
BuildArch:      noarch
#To download videos
Recommends:     yt-dlp
#To convert videos. Not avaliabe for Fedora 35
%if 0%{?fedora} >= 36
Recommends:     ffmpeg
%endif

%description
gallery-dl is a command-line program to download image galleries and collections from several image hosting sites. It is a cross-platform tool with many configuration options and powerful filenaming capabilities.

%package        bash-completion
Summary:        Bash completion for %{name}
Group:          System/Shells
Requires:       bash-completion
Supplements:    packageand(%{name}:bash)
BuildArch:      noarch

%description    bash-completion
Bash command line completion support for %{name}.

%package        zsh-completion
Summary:        Zsh Completion for %{name}
Group:          System/Shells
Requires:       zsh
BuildRequires:  zsh
Supplements:    packageand(%{name}:zsh)
BuildArch:      noarch

%description zsh-completion
ZSH command line completion support for %{name}.

%package        fish-completion
Summary:        fish Completion for %{name}
Group:          System/Shells
Requires:       fish
BuildRequires:  fish
Supplements:    packageand(%{name}:fish)
BuildArch:      noarch

%description fish-completion
fish command line completion support for %{name}.

%prep
%autosetup -p1 -n gallery_dl-%{version}
%generate_buildrequires
%pyproject_buildrequires -r

%build
%pyproject_wheel

%install
%pyproject_install

%files
%doc README.rst CHANGELOG.md
%license LICENSE

%{_bindir}/%{name}
%{python3_sitelib}/gallery_dl/
%{python3_sitelib}/gallery_dl-%{version}.dist-info/
%{_mandir}/man1/%{name}.*
%{_mandir}/man5/%{name}.*
%files bash-completion
%{_datadir}/bash-completion/completions/%{name}

%files zsh-completion
%{_datadir}/zsh/site-functions/_%{name}

%files fish-completion
%{_datadir}/fish/vendor_completions.d/%{name}.fish


%changelog
* Mon Aug 17 2026 vitrasti <vitrasti@protonmail.com> - 1.32.9-1
- Initial release for personal copr repo.
