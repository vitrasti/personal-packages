# Personal COPR package: enable buildroot networking for npm ci (locked Web UI).
# References: sneed/llama-cpp-vulkan and lacamar/arm64-misc on COPR.
%global upstream_tag v%{version}
%global llama_build_number 11429
%global llama_build_commit 8345f333951c661d166b00e6f9362e553768f292
%global privlibdir %{_libdir}/%{name}
# Keep bundled ggml/llama libraries private to this application. Their internal
# dependencies are satisfied by this RPM, not by another ggml consumer.
%global __provides_exclude_from ^%{privlibdir}/.*$
%global __requires_exclude ^lib(ggml[^ ]*|llama[^ ]*|mtmd)[.]so.*$

Name:           llama-cpp-vulkan
Version:        0.6.0
Release:        1%{?dist}
Summary:        Local LLM inference tools and HTTP server with Vulkan acceleration
# Includes bundled C/C++ code and the compiled, locked upstream Web UI.
License:        MIT AND Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND ISC AND 0BSD AND Zlib AND CC0-1.0 AND Unlicense AND OFL-1.1 AND BlueOak-1.0.0 AND MPL-2.0 AND LGPL-3.0-or-later AND Python-2.0 AND CC-BY-4.0
URL:            https://github.com/ggml-org/llama.cpp
Source0:        %{url}/archive/refs/tags/%{upstream_tag}.tar.gz#/llama.cpp-%{version}.tar.gz

ExclusiveArch:  x86_64
BuildRequires:  cmake >= 3.19
BuildRequires:  gcc-c++
BuildRequires:  ninja-build
BuildRequires:  vulkan-loader-devel
BuildRequires:  vulkan-headers
BuildRequires:  glslc
BuildRequires:  spirv-headers-devel
BuildRequires:  openssl-devel
BuildRequires:  nodejs >= 1:22.12.0
BuildRequires:  npm
BuildRequires:  python3
BuildRequires:  binutils
Requires:       vulkan-loader%{?_isa}
# Intel's Vulkan ICD is in Mesa. Make it a hard dependency so image builds
# work even when weak dependencies are disabled (common on CoreOS/bootc).
Requires:       mesa-vulkan-drivers%{?_isa}
Requires:       ca-certificates
# These packages own the same upstream command names.
Conflicts:      llama-cpp

%description
llama.cpp runs local language models in GGUF format. This package builds the
Vulkan backend for GPU acceleration, including Intel GPUs using Fedora's Mesa
drivers, plus portable runtime-selected CPU backends for CPU fallback.

Includes llama, llama-cli, llama-server (HTTP/OpenAI-compatible API and embedded
Web UI), llama-quantize, llama-bench, llama-gguf-split and other upstream tools.

Suitable for Fedora CoreOS, rpm-ostree and bootc image builds: all application
files live in /usr. Store models in a writable directory such as
/var/lib/llama-cpp or your home directory; the user cache stays outside /usr.
The runtime user needs access to the GPU's /dev/dri/renderD* device. For an
application container, pass /dev/dri through to the container as well.

%prep
%autosetup -n llama.cpp-%{version}

%build
# Build exactly the UI in this release; do not let CMake fetch a newer UI from
# Hugging Face or silently produce a server without its embedded Web UI.
export npm_config_cache="$PWD/.npm-cache"
export PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
pushd tools/ui
npm ci --no-audit --no-fund
LLAMA_UI_OUT_DIR="$PWD/dist" \
LLAMA_UI_VERSION=%{upstream_tag} \
LLAMA_BUILD_NUMBER=%{llama_build_number} npm run build
test -s dist/index.html
popd

# Preserve notices for bundled native code and Web UI dependencies.
%{python3} - <<'PY'
import json
from pathlib import Path
import shutil

notices = Path('LICENSES.bundled')
notices.mkdir(exist_ok=True)
for root in (Path('vendor'), Path('ggml'), Path('tools/ui/node_modules')):
    for path in sorted(root.rglob('*')):
        if path.is_file() and path.name.lower().startswith(('license', 'copying', 'notice')):
            dest = notices / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
inventory = []
for path in sorted(Path('tools/ui/node_modules').rglob('package.json')):
    package = json.loads(path.read_text())
    if package.get('name') and package.get('version'):
        inventory.append({key: package.get(key) for key in ('name', 'version', 'license')})
Path('BUNDLED-UI-PACKAGES.json').write_text(json.dumps(inventory, indent=2) + '\n')
PY

%cmake -G Ninja \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_INSTALL_LIBDIR=%{privlibdir} \
    -DCMAKE_INSTALL_RPATH=%{privlibdir} \
    -DGGML_BACKEND_DIR=%{privlibdir} \
    -DGGML_NATIVE=OFF \
    -DGGML_BACKEND_DL=ON \
    -DGGML_CPU_ALL_VARIANTS=ON \
    -DGGML_VULKAN=ON \
    -DGGML_CCACHE=OFF \
    -DLLAMA_BUILD_IS_DEV=OFF \
    -DLLAMA_BUILD_NUMBER=%{llama_build_number} \
    -DLLAMA_BUILD_COMMIT=%{llama_build_commit} \
    -DLLAMA_BUILD_COMMON=ON \
    -DLLAMA_BUILD_TOOLS=ON \
    -DLLAMA_BUILD_SERVER=ON \
    -DLLAMA_BUILD_APP=ON \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_TESTS_INSTALL=OFF \
    -DLLAMA_BUILD_UI=OFF \
    -DLLAMA_USE_PREBUILT_UI=OFF \
    -DLLAMA_OPENSSL=ON
%cmake_build

%install
%cmake_install
# This is an application package, not a public ggml/llama development SDK.
rm -rf %{buildroot}%{_includedir} \
       %{buildroot}%{privlibdir}/cmake \
       %{buildroot}%{privlibdir}/pkgconfig
# Real unversioned libraries (libllama-*-impl.so, backend modules, etc.) are
# runtime files; remove only development symlinks and static archives.
find %{buildroot}%{privlibdir} -type l -name '*.so' -delete
find %{buildroot}%{privlibdir} -type f -name '*.a' -delete

%check
# No GPU or model download is needed on COPR builders. Check the installed
# launchers and all ELF dependencies against the staged private libraries.
export LD_LIBRARY_PATH=%{buildroot}%{privlibdir}
%{buildroot}%{_bindir}/llama-cli --version
%{buildroot}%{_bindir}/llama-server --version
%{buildroot}%{_bindir}/llama-server --help > /dev/null
test -s %{buildroot}%{privlibdir}/libggml-vulkan.so
%{python3} - %{buildroot} %{privlibdir} <<'PY'
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
for directory in (root / 'usr/bin', root / sys.argv[2].lstrip('/')):
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.is_symlink():
            continue
        with path.open('rb') as file:
            if file.read(4) != b'\x7fELF':
                continue
        result = subprocess.run(['ldd', str(path)], capture_output=True, text=True, check=True)
        if 'not found' in result.stdout:
            raise RuntimeError(f'{path}:\n{result.stdout}')
print('Passed: installed launchers, Vulkan module and shared library dependencies')
PY

%files
%license LICENSE LICENSES.bundled BUNDLED-UI-PACKAGES.json
%doc README.md
%{_bindir}/llama
%{_bindir}/llama-*
%dir %{privlibdir}
%{privlibdir}/lib*.so*

%changelog
* Tue Oct 06 2026 vitrasti <vitrasti@protonmail.com> - 0.6.0-1
- Initial source build with Vulkan, Intel Mesa drivers and portable CPU backends
- Include llama-server with the embedded Web UI from locked upstream sources
- Install private runtime libraries under /usr for Fedora CoreOS and bootc
