#!/bin/bash

echo "This script will add lines to the .bashrc file to support Python virtual environments and the virtual environment wrapper."
echo "After amending the .bashrc file the new settings will be invoked with the 'source' command."
echo "Subsequent logins will automatically invoke this and will not need to be 'source'd."

echo "# These lines added to support Python virtual environments by myHome-Doorcam" >> $HOME/.bashrc
echo "export WORKON_HOME=$HOME/.virtualenvs" >> $HOME/.bashrc
echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> $HOME/.bashrc
echo "export VIRTUALENVWRAPPER_VIRTUALENV=/usr/local/bin/virtualenv" >> $HOME/.bashrc
echo "export VIRTUALENVWRAPPER_ENV_BIN_DIR=bin" >> $HOME/.bashrc
echo "source /usr/local/bin/virtualenvwrapper.sh" >> $HOME/.bashrc

source $HOME/.bashrc
