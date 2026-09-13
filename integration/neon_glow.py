#!/usr/bin/python
"""Follow Omarchy's selected wallpaper and apply its Neon Glow palette."""
import argparse
import base64
import ctypes
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import os
import select
import struct
from pathlib import Path
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
REFRESH = (
 'omarchy-restart-terminal', 'omarchy-restart-hyprctl', 'omarchy-restart-btop',
 'omarchy-restart-opencode', 'omarchy-restart-helix', 'omarchy-theme-set-foot',
 'omarchy-theme-set-tmux', 'omarchy-theme-set-gnome', 'omarchy-theme-set-pi',
 'omarchy-theme-set-claude', 'omarchy-theme-set-hermes', 'omarchy-theme-set-t3code',
 'omarchy-theme-set-browser', 'omarchy-theme-set-vscode', 'omarchy-theme-set-obsidian',
 'omarchy-theme-set-keyboard',
)

def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.neon-glow-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
        os.chmod(name, 0o644)
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

class ChangeWatcher:
    """Wait for Linux filesystem notifications without extra Python packages."""
    MASK = 0x00000FC8  # CLOSE_WRITE, MOVE, CREATE, DELETE, DELETE_SELF, MOVE_SELF
    EVENT = struct.Struct('iIII')

    def __init__(self, current):
        self.current = current
        self.libc = ctypes.CDLL('libc.so.6', use_errno=True)
        self.libc.inotify_init1.argtypes = [ctypes.c_int]
        self.libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self.libc.inotify_rm_watch.argtypes = [ctypes.c_int, ctypes.c_int]
        self.fd = self.checked(self.libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC))
        self.theme_wd = None
        self.theme_identity = None
        try:
            self.current_wd = self.add(current)
            self.sync_theme()
        except Exception:
            self.close()
            raise

    @staticmethod
    def checked(result):
        if result < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        return result

    def add(self, path):
        return self.checked(self.libc.inotify_add_watch(self.fd, os.fsencode(path), self.MASK))

    def sync_theme(self):
        # Omarchy replaces this directory when applying a theme.
        try:
            info = (self.current/'theme').stat()
            identity = (info.st_dev, info.st_ino)
        except FileNotFoundError:
            identity = None
        if identity == self.theme_identity:
            return
        if self.theme_wd is not None:
            self.libc.inotify_rm_watch(self.fd, self.theme_wd)
        self.theme_wd = None
        self.theme_identity = None
        if identity is not None:
            try:
                self.theme_wd = self.add(self.current/'theme')
                self.theme_identity = identity
            except FileNotFoundError:
                pass  # Its removal/replacement is queued on the parent watch.

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            remaining = None if deadline is None else max(0, deadline - time.monotonic())
            if not select.select([self.fd], [], [], remaining)[0]:
                return False
            changed = False
            data = os.read(self.fd, 65536)
            offset = 0
            while offset < len(data):
                wd, mask, _, length = self.EVENT.unpack_from(data, offset)
                offset += self.EVENT.size
                name = data[offset:offset + length].split(b'\0', 1)[0]
                offset += length
                if wd == self.current_wd and mask & 0x0000AC00:
                    raise RuntimeError('Omarchy current directory disappeared; restarting watcher')
                if mask & 0x00004000:  # Queue overflow: reconcile current state.
                    changed = True
                if wd == self.current_wd and name in (b'theme.name', b'background', b'theme'):
                    changed = True
                if wd == self.theme_wd:
                    if mask & 0x00008C00:
                        self.libc.inotify_rm_watch(self.fd, self.theme_wd)
                        self.theme_wd = None
                        self.theme_identity = None
                        changed = True
                    elif name in (b'colors.toml', b'shell.toml', b'neon-glow-variant'):
                        changed = True
            if changed:
                return True

    def close(self):
        os.close(self.fd)

class Follower:
    def __init__(self, home=None, root=ROOT, runtime=None, runner=None):
        self.home = Path(home or Path.home())
        self.root = Path(root)
        prepared = self.home / '.local/state/neon-glow/palettes'
        self.palettes = prepared if prepared.is_dir() else self.root / 'palettes'
        self.current = self.home / '.local/state/omarchy/current'
        self.saved = self.home / '.local/state/neon-glow/selection.json'
        self.runtime = Path(runtime or os.environ.get('XDG_RUNTIME_DIR', '/tmp'))
        self.runner = runner or self.run
        self.manifest = json.loads((self.root / 'palettes.json').read_text())
        self.mapping = {name: slug for slug, item in self.manifest.items() for name in item['backgrounds']}

    def desired(self):
        try:
            if (self.current / 'theme.name').read_text().strip() != 'neon-glow': return None
            background = (self.current / 'background').resolve(strict=True)
            slug = self.mapping.get(background.name)
            if slug: return slug, background.name
        except (OSError, RuntimeError):
            pass
        return None

    def matches(self, slug):
        try:
            # A normal theme reapply replaces these, even if the background is unchanged.
            for name in ('colors.toml', 'shell.toml', 'neon-glow-variant'):
                if (self.current/'theme'/name).read_bytes() != (self.palettes/slug/name).read_bytes():
                    return False
            return True
        except OSError:
            return False

    @staticmethod
    def run(command):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=20)
            if result.returncode and result.stderr.strip():
                print(f'{command[0]}: {result.stderr.strip()}', flush=True)
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired) as error:
            print(f'{command[0]}: {error}', flush=True)
            return False

    def remember(self, choice):
        data = (json.dumps({'variant': choice[0], 'background': choice[1]}, indent=2)+'\n').encode()
        if not self.saved.exists() or self.saved.read_bytes()!=data:
            atomic_write(self.saved, data)

    def apply(self):
        choice = self.desired()
        if not choice: return False
        if self.matches(choice[0]):
            self.remember(choice)
            return False
        # Same lock as Omarchy theme set: re-check selection after acquiring it.
        with (self.runtime/'omarchy-theme-set.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if self.desired()!=choice: return False
            slug = choice[0]
            palette = self.palettes/slug
            theme = self.current/'theme'
            if self.matches(slug):
                self.remember(choice)
                return False
            # Consumers wait for the completion marker before refreshing.
            (theme/'neon-glow-variant').unlink(missing_ok=True)
            for source in sorted(palette.iterdir()):
                if source.is_file() and source.name!='neon-glow-variant':
                    atomic_write(theme/source.name, source.read_bytes())
            payload = [base64.b64encode((theme/name).read_bytes()).decode() for name in ('colors.toml','shell.toml')]
            accepted = self.runner(['omarchy-shell','-q','shell','applyTheme',*payload])
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda cmd: self.runner([cmd]), REFRESH))
            if not accepted:
                # Without the marker the watcher retries after the shell starts.
                (theme/'neon-glow-variant').unlink(missing_ok=True)
                return False
            atomic_write(theme/'neon-glow-variant',(palette/'neon-glow-variant').read_bytes())
            self.remember(choice)
            print(f'Applied Neon Glow: {slug}', flush=True)
            return True

    def watch(self):
        # Prevent a second follower from racing the service.
        with (self.runtime/'neon-glow-watcher.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            watcher = ChangeWatcher(self.current)
            try:
                while True:
                    retry = None
                    try:
                        watcher.sync_theme()
                        self.apply()
                        choice = self.desired()
                        if choice and not self.matches(choice[0]):
                            retry = 2
                    except Exception as error:
                        print(f'Neon Glow: {error}', flush=True)
                        retry = 2
                    # No periodic wakeups when idle, including on other themes.
                    if watcher.wait(retry):
                        # Coalesce a burst of writes/renames before applying.
                        time.sleep(.3)
            finally:
                watcher.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    follower=Follower()
    if args.once: follower.apply()
    else: follower.watch()
