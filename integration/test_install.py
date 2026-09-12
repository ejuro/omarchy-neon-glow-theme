#!/usr/bin/python
"""Fresh Git install with real Omarchy staging/templates and a simulated user service manager."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import tomllib

ROOT=Path(__file__).resolve().parents[1]

def call(*args, env=None):
    return subprocess.run(args,env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

def main():
    with tempfile.TemporaryDirectory(prefix='neon-install-test-') as temp:
        temp=Path(temp); source=temp/'omarchy-neon-glow-theme'
        shutil.copytree(ROOT,source,ignore=shutil.ignore_patterns('.git','__pycache__'))
        call('git','init','-q',str(source))
        call('git','-C',str(source),'add','.')
        call('git','-C',str(source),'-c','user.name=Installation Test','-c','user.email=test@example.invalid','commit','-qm','Test snapshot')
        home=temp/'home'; home.mkdir(); runtime=temp/'runtime'; runtime.mkdir()
        fake=temp/'bin'; fake.mkdir()
        systemctl=fake/'systemctl'
        systemctl.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$HOME/systemctl.log"\nexit 0\n')
        systemctl.chmod(0o755)
        env=os.environ|{'HOME':str(home),'XDG_RUNTIME_DIR':str(runtime),'OMARCHY_PATH':'/usr/share/omarchy','OMARCHY_THEME_HEADLESS':'1','PATH':str(fake)+':/usr/share/omarchy/bin:/usr/bin:/bin'}
        # Sentinels prove setup/uninstall never replace user app configuration.
        sentinels={home/'.config/nvim/init.lua':b'-- custom nvim\n',home/'.config/cliamp/config.toml':b'theme = "custom"\n'}
        for p,data in sentinels.items(): p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
        result=call('omarchy','theme','install',source.as_uri(),env=env)
        installed=home/'.config/omarchy/themes/neon-glow'
        assert (installed/'.git').is_dir()
        assert (home/'.local/state/omarchy/current/theme/neovim.lua').is_file()
        # In a Git checkout, a normal install only activates the base theme.
        assert not (home/'.config/systemd/user/neon-glow.service').exists()
        print('PASS: normal Omarchy Git installation and theme staging',flush=True)
        before=call('git','-C',str(installed),'status','--porcelain').stdout
        print(call('bash',str(installed/'install.sh'),env=env).stdout.strip(),flush=True)
        assert call('git','-C',str(installed),'status','--porcelain').stdout==before
        generated=home/'.local/state/neon-glow/palettes'
        manifest=json.loads((installed/'palettes.json').read_text())
        assert len(list(generated.iterdir()))==12
        module_spec=importlib.util.spec_from_file_location('release_follower',installed/'integration/neon_glow.py')
        module=importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(module)
        follower=module.Follower(home=home,root=installed,runtime=runtime,runner=lambda command: True)
        assert follower.palettes==generated
        for slug in manifest:
            link=follower.current/'background'; link.unlink()
            link.symlink_to(installed/'backgrounds'/manifest[slug]['backgrounds'][0])
            assert follower.apply()
            assert follower.matches(slug)
            assert tomllib.loads((follower.current/'theme/colors.toml').read_text())['background']=='#000000'
        initial_link=(follower.current/'background').readlink()
        call('bash',str(installed/'install.sh'),env=env)
        assert (follower.current/'background').readlink()==initial_link
        for p,data in sentinels.items(): assert p.read_bytes()==data
        print('PASS: setup, all 12 generated palettes, idempotent reinstall, app config preservation',flush=True)
        # Template changes must be incorporated on reinstall without dirtying the repo.
        templates=home/'.config/omarchy/themed'; templates.mkdir(parents=True,exist_ok=True)
        (templates/'foot.ini.tpl').write_text('[colors]\nbackground={{ background_strip }}\nforeground={{ foreground_strip }}\n# local-template-test\n')
        call('bash',str(installed/'install.sh'),env=env)
        assert 'local-template-test' in (generated/'ruby-red/foot.ini').read_text()
        print('PASS: local user templates respected',flush=True)
        # A failed prepare must not stop a working service or discard valid palettes.
        previous=(generated/'ruby-red/colors.toml').read_bytes()
        manifest_path=installed/'palettes.json'
        original=manifest_path.read_bytes(); manifest_path.write_text('{"missing": {"backgrounds": ["missing.png"]}}')
        log_before=(home/'systemctl.log').read_text()
        failure=subprocess.run(['bash',str(installed/'install.sh')],env=env,capture_output=True)
        assert failure.returncode!=0
        assert (generated/'ruby-red/colors.toml').read_bytes()==previous
        assert '--user stop' not in (home/'systemctl.log').read_text()[len(log_before):]
        manifest_path.write_bytes(original)
        print('PASS: invalid update leaves working installation intact',flush=True)
        appearance=(follower.current/'theme/colors.toml').read_bytes()
        call('bash',str(installed/'uninstall.sh'),env=env)
        call('bash',str(installed/'uninstall.sh'),env=env)
        assert not generated.exists()
        assert not (home/'.config/systemd/user/neon-glow.service').exists()
        assert (follower.current/'theme/colors.toml').read_bytes()==appearance
        assert installed.exists()
        for p,data in sentinels.items(): assert p.read_bytes()==data
        print('PASS: idempotent uninstall preserves appearance, theme repository, and app configs',flush=True)

if __name__=='__main__': main()
