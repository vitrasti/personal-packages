#!/usr/bin/bash
# RPM wrapper for a private install under /usr/share/hermes-agent.
# User state stays in $HERMES_HOME (default ~/.hermes), which is writable on
# Fedora CoreOS / Kinoite / bootc. Nothing in this wrapper writes under /usr.
#
# Do not set HERMES_MANAGED: upstream treats that as Nix-style managed mode
# and blocks `hermes config set` / `hermes setup`. Updates are refused via
# the `.install_method` stamp next to the code instead.

declare -r INST_DIR=/usr/share/hermes-agent

: "${HERMES_BUNDLED_SKILLS:=${INST_DIR}/skills}"
: "${HERMES_OPTIONAL_SKILLS:=${INST_DIR}/optional-skills}"
: "${HERMES_OPTIONAL_MCPS:=${INST_DIR}/optional-mcps}"
: "${HERMES_BUNDLED_LOCALES:=${INST_DIR}/locales}"

export HERMES_BUNDLED_SKILLS
export HERMES_OPTIONAL_SKILLS
export HERMES_OPTIONAL_MCPS
export HERMES_BUNDLED_LOCALES
export PYTHONPATH="${INST_DIR}${PYTHONPATH:+:${PYTHONPATH}}"

# Immutable /usr: never pip/uv-install into the image at runtime.
export HERMES_DISABLE_LAZY_INSTALLS="${HERMES_DISABLE_LAZY_INSTALLS:-1}"
# Do not try to write .pyc under /usr.
export PYTHONDONTWRITEBYTECODE="${PYTHONDONTWRITEBYTECODE:-1}"

exec /usr/bin/hermes-cli "$@"
