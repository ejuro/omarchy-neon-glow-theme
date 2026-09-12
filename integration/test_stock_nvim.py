#!/usr/bin/python
"""Test packaged Omarchy Neovim in an isolated home; requires omarchy-nvim."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory(prefix='neon-stock-nvim-') as temp:
        home=Path(temp); config=home/'.config/nvim'
        shutil.copytree('/etc/skel/.config/nvim',config,symlinks=True)
        shutil.copytree('/etc/skel/.local/share/nvim/lazy',home/'.local/share/nvim/lazy',symlinks=True)
        current=home/'.local/state/omarchy/current'; (current/'theme').mkdir(parents=True)
        path=current/'theme/neovim.lua'
        (config/'lua/plugins/theme.lua').unlink(missing_ok=True)
        (config/'lua/plugins/theme.lua').symlink_to(path)
        (current/'theme.name').write_text('neon-glow\n')
        shutil.copy2(ROOT/'palettes/ruby-red/neovim.lua',path)
        env=os.environ|{'HOME':str(home),'XDG_CONFIG_HOME':str(home/'.config'),'XDG_DATA_HOME':str(home/'.local/share'),'XDG_STATE_HOME':str(home/'.local/state'),'XDG_CACHE_HOME':str(home/'.cache')}
        socket=home/'nvim.sock'
        with (home/'nvim.log').open('w') as log:
            proc=subprocess.Popen(['nvim','--headless','--listen',str(socket),'+lua vim.api.nvim_buf_set_lines(0,0,-1,false,{"unsaved stock test"})'],env=env,stdout=log,stderr=log)
            def query():
                lua='vim.json.encode({accent=require("aether.config").options.colors.accent, modified=vim.bo.modified, lines=vim.api.nvim_buf_get_lines(0,0,-1,false)})'
                return json.loads(subprocess.check_output(['nvim','--server',str(socket),'--remote-expr','luaeval('+json.dumps(lua)+')'],env=env,text=True))
            try:
                time.sleep(4)
                assert query()['accent']=='#ff4d5b'
                for slug,replace_dir,expected in [('blue',False,'#60ccff'),('orchid',True,'#e49aff'),('ruby-red',False,'#ff4d5b')]:
                    if replace_dir: shutil.rmtree(current/'theme'); (current/'theme').mkdir()
                    tmp=current/'theme/new.lua'; shutil.copy2(ROOT/'palettes'/slug/'neovim.lua',tmp); tmp.replace(path)
                    deadline=time.monotonic()+10
                    while time.monotonic()<deadline:
                        result=query()
                        if result['accent']==expected: break
                        time.sleep(.2)
                    else: raise AssertionError((slug,result))
                    assert result['modified'] and result['lines']==['unsaved stock test']
                    print('PASS: stock Neovim '+slug+(' after directory replacement' if replace_dir else ''),flush=True)
            finally:
                if proc.poll() is None:
                    subprocess.run(['nvim','--server',str(socket),'--remote-send','<Cmd>qa!<CR>'],env=env,capture_output=True)
                    try: proc.wait(timeout=5)
                    except subprocess.TimeoutExpired: proc.terminate(); proc.wait(timeout=5)

if __name__=='__main__': main()
