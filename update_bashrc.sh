#!/bin/bash

echo "export WORKON_HOME=$HOME/.virtualenvs" >> $HOME/.bashrc
echo "export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3" >> $HOME/.bashrc
echo "source /usr/local/bin/virtualenvwrapper.sh" >> $HOME/.bashrc
echo "export VIRTUALENVWRAPPER_ENV_BIN_DIR=bin" >> $HOME/.bashrc
