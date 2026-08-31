# Shared setup for screencast scenes. Sourced by scenes/*.setup.sh.
#
# Everything here runs before asciinema starts, so it is off camera. Its job is
# to build the machine state a scene claims to start from: a project directory
# that looks freshly cloned, a cache that is cold or warm on purpose, a depot
# that already has artifacts in it.
#
# It never fakes output. What the recording shows is envy really running.

set -Eeuo pipefail

SCREENCASTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS_DIR="$SCREENCASTS_DIR/.tools"

# The envy release the demo projects pin, and the package-specs commit their
# bundles pin. Both are real and public; bump them together when they move.
ENVY_VERSION="0.2.1"
SPECS_REPO="https://github.com/envy-package-manager/package-specs.git"
SPECS_REF="ded36a39bbf13744f5a0e539f2f4741fecb61dd0"

# One home for every scene, so the recorded prompt is always `~/work/<project>`
# and never a path off this machine. drive.py resolves symlinks before handing
# it to the shell, so /tmp vs /private/tmp does not leak into the prompt either.
DEMO_HOME="${DEMO_HOME:-/tmp/envy-screencast/home}"
DEMO_CACHE="$DEMO_HOME/.cache/envy"

# The envy binary the setup scripts drive. Not the one the recording uses: a
# scene's project bootstraps its own pinned copy on camera, which is the point.
envy_tool() {
  local dir="$TOOLS_DIR/envy-$ENVY_VERSION" bin="$TOOLS_DIR/envy-$ENVY_VERSION/envy"
  if [[ ! -x "$bin" ]]; then
    local os arch asset
    case "$(uname -s)" in
      Darwin) os=darwin ;;
      Linux)  os=linux ;;
      *) echo "unsupported host: $(uname -s)" >&2; return 1 ;;
    esac
    case "$(uname -m)" in
      arm64|aarch64) arch=arm64 ;;
      x86_64|amd64)  arch=x86_64 ;;
      *) echo "unsupported host: $(uname -m)" >&2; return 1 ;;
    esac
    asset="envy-$os-$arch.tar.gz"
    mkdir -p "$dir"
    curl -fsSL -o "$dir/$asset" \
      "https://github.com/envy-package-manager/envy/releases/download/v$ENVY_VERSION/$asset"
    tar xzf "$dir/$asset" -C "$dir"
    rm -f "$dir/$asset"
    chmod +x "$bin"
  fi
  printf '%s\n' "$bin"
}

# Run the setup envy against the demo cache.
envy_run() {
  ENVY_CACHE_ROOT="$DEMO_CACHE" "$(envy_tool)" "$@"
}

demo_reset() {
  rm -rf "$DEMO_HOME"
  mkdir -p "$DEMO_HOME/work"
}

# Write a manifest, then deploy the bin/ wrappers into it, exactly as they would
# be committed. `use` writes the version and sha256sums pins from the real
# release, so the bootstrap script in the recording verifies a real checksum.
demo_project() {
  local dir="$1"
  mkdir -p "$dir"
  cat > "$dir/envy.lua"
  quietly "$dir" use "$ENVY_VERSION" --pin-sums
  quietly "$dir" sync --platform all
}

# Setup should be silent when it works and loud when it does not. Swallowing
# stderr outright once hid a real build failure behind a recording that just
# showed the error on camera.
quietly() {
  local dir="$1" out; shift
  if ! out="$( cd "$dir" && envy_run "$@" 2>&1 )"; then
    printf 'setup: envy %s failed in %s\n%s\n' "$1" "$dir" "$out" >&2
    return 1
  fi
}

# Put the cache back to what a machine that has never seen this project has:
# no packages, no specs, no downloaded envy. The shell hook stays, because it
# belongs to the person's shell rather than to any project.
#
# The contents go, not the directories. envy prints a one-time "caching packages
# in <path>" notice whenever <root>/packages is missing, which is the right thing
# to tell someone running it for the first time and the wrong thing to put in a
# screencast: the path it names is this machine's throwaway /tmp cache. An empty
# packages/ is still a cold cache, and it stops the recordings claiming to be
# anyone's first run.
demo_cold_cache() {
  local d
  for d in packages specs envy locks; do
    if [[ -d "$DEMO_CACHE/$d" ]]; then
      find "$DEMO_CACHE/$d" -mindepth 1 -delete
    fi
  done
  mkdir -p "$DEMO_CACHE/packages"
}

# Ensure the hook exists for the demo home. Any envy command writes it.
demo_hook() {
  envy_run cache >/dev/null
  mkdir -p "$DEMO_CACHE/packages"
}
