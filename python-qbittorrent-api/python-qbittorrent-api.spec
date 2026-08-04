%global srcname qbittorrent-api

Name:           python-qbittorrent-api
Version:        2026.8.0
Release:        %autorelease
Summary:        Python client for the qBittorrent Web API

License:        MIT
URL:            https://github.com/rmartin16/qbittorrent-api
Source0:        %{pypi_source qbittorrent_api}

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros

# Runtime deps
BuildRequires:  python3dist(requests)
BuildRequires:  python3dist(packaging)
BuildRequires:  python3dist(urllib3)

# Build/Test
BuildRequires:  python3dist(setuptools)
BuildRequires:  python3dist(wheel)

%global _description \
Python client implementation for the qBittorrent Web API.

%description
%{_description}

%package -n python3-qbittorrent-api
Summary: %{summary}

%description -n python3-qbittorrent-api
%{_description}

%prep
%autosetup -n qbittorrent_api-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files qbittorrentapi

%check
%pyproject_check_import

%files -n python3-qbittorrent-api -f %{pyproject_files}
%license LICENSE
%doc README.md

%changelog
%autochangelog
