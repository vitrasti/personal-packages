# llama-cpp-vulkan

Source-built llama.cpp 0.6.0 for Fedora x86_64, with Vulkan, portable CPU
backends, and `llama-server` with its embedded Web UI. Intel Vulkan drivers
(`mesa-vulkan-drivers`) are required by the RPM.

## COPR build

Use `llama-cpp-vulkan.spec` with a Fedora chroot matching the Fedora release
in your CoreOS image. Enable **buildroot network access**: the Web UI uses
`npm ci` with the upstream release's lockfile. No Node.js/npm is needed at
runtime. CMake's automatic Web UI downloads are disabled.

The package conflicts with `llama-cpp`, which owns the same commands.

## Fedora CoreOS image build

After adding your COPR `.repo` file to the image, install the package in your
existing CoreOS Containerfile using its package-install mechanism, for example:

```dockerfile
COPY personal-packages.repo /etc/yum.repos.d/personal-packages.repo
RUN rpm-ostree install llama-cpp-vulkan && ostree container commit
```

For a Fedora bootc base using DNF instead:

```dockerfile
COPY personal-packages.repo /etc/yum.repos.d/personal-packages.repo
RUN dnf install -y llama-cpp-vulkan && dnf clean all
```

All application files are installed under `/usr`. Provision models separately
in writable storage, such as `/var/lib/llama-cpp`; do not download models into
the package's library directory. The Fedora RPM must match the base image's
Fedora release, rather than copying a binary built for a newer release.

## Run

The booted host needs a supported Intel GPU, its kernel driver/firmware, and
permission for the runtime user to access `/dev/dri/renderD*`.

```sh
llama-cli --list-devices
llama-server -m /var/lib/llama-cpp/model.gguf -ngl 99 --host 127.0.0.1 --port 8080
```

Open `http://127.0.0.1:8080` for the Web UI. Use `-ngl 0` for CPU-only
inference. When running as an application container on CoreOS, also pass the
GPU devices (`--device /dev/dri`) and grant the container user device access.

## Packaging references

- [sneed/llama-cpp-vulkan](https://copr.fedorainfracloud.org/coprs/sneed/llama-cpp-vulkan/)
  and its [source](https://github.com/Unrest6585/fedora-llamacpp)
- [georgiou/llama-cpp](https://copr.fedorainfracloud.org/coprs/georgiou/llama-cpp/)
- [lacamar's Vulkan-enabled spec](https://codeberg.org/lacamar/arm64-misc/src/branch/main/specfiles/llama-cpp/llama-cpp.spec)

Verified with a full Fedora 44 RPM build, installed command/library smoke
checks, and server startup/Web UI asset serving without a GPU or model.
Intel GPU offload and the booted CoreOS image require target-hardware testing.
