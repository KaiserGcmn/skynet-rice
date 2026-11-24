# ~/.profile: executed by the command interpreter for login shells.
# This file is not read by bash(1), if ~/.bash_profile or ~/.bash_login
# exists.
# see /usr/share/doc/bash/examples/startup-files for examples.
# the files are located in the bash-doc package.

# the default umask is set in /etc/profile; for setting the umask
# for ssh logins, install and configure the libpam-umask package.
#umask 022

# if running bash
if [ -n "$BASH_VERSION" ]; then
    # include .bashrc if it exists
    if [ -f "$HOME/.bashrc" ]; then
	. "$HOME/.bashrc"
    fi
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/bin" ] ; then
    case ":$PATH:" in
        *":$HOME/bin:"*) ;;
        *) PATH="$HOME/bin:$PATH" ;;
    esac
fi

# set PATH so it includes user's private bin if it exists
if [ -d "$HOME/.local/bin" ] ; then
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) PATH="$HOME/.local/bin:$PATH" ;;
    esac
fi

# Select Node once per login so desktop applications and child terminals
# inherit its executable path. .bashrc can then skip repeated selection.
# nvm remains optional; no version is installed or downloaded here.
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    case "${NVM_BIN-}" in
        "$NVM_DIR"/versions/node/*/bin)
            if [ ! -x "$NVM_BIN/node" ] ||
               [ "$(command -v node)" != "$NVM_BIN/node" ]; then
                \. "$NVM_DIR/nvm.sh"
            fi
            ;;
        *) \. "$NVM_DIR/nvm.sh" ;;
    esac
fi
