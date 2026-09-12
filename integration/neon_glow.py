#!/usr/bin/python
"""Follow Omarchy's selected wallpaper and apply its Neon Glow palette."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import fcntl
import json
import os
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
                # Without the marker the next poll retries after the shell starts.
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
            previous = None
            while True:
                try:
                    choice = self.desired()
                    if choice == previous:
                        self.apply()
                    previous = choice
                except Exception as error:
                    print(f'Neon Glow: {error}', flush=True)
                    time.sleep(2)
                time.sleep(.3)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once',action='store_true')
    args=parser.parse_args()
    follower=Follower()
    if args.once: follower.apply()
    else: follower.watch()
