%global goipath github.com/getsops/sops/v3

Name:           sops
Version:        3.13.3
Release:        1%{?dist}
Summary:        Editor of encrypted files supporting YAML, JSON, ENV, INI and BINARY formats

License:        MPL-2.0
URL:            https://github.com/getsops/sops
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  golang >= 1.25
BuildRequires:  git

Provides:       %{name} = %{version}-%{release}

%description
sops is an editor of encrypted files that supports YAML, JSON, ENV, INI and
BINARY formats and encrypts with AWS KMS, GCP KMS, Azure Key Vault, HashiCorp
Vault, age, and PGP.

%prep
%autosetup -n %{name}-%{version}

%build
# Fetch modules from the Go proxy; upstream does not ship a vendor/ directory.
export GOPROXY=https://proxy.golang.org
export GOFLAGS=-mod=mod
export CGO_ENABLED=0

go build \
    -ldflags "-X %{goipath}/version.Version=%{version}" \
    -o %{name} \
    %{goipath}/cmd/sops

%install
install -Dpm 0755 %{name} %{buildroot}%{_bindir}/%{name}

%check
./%{name} --version --disable-version-check | grep -q "%{version}"

%files
%license LICENSE
%doc README.rst
%{_bindir}/%{name}

%changelog
* Mon Aug 03 2026 vitrasti <vitrasti@protonmail.com> - 3.13.3-1
