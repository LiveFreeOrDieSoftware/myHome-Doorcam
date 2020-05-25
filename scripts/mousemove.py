# Must be run from pi, not ssh
# https://github.com/rshk/python-libxdo
from xdo import Xdo
xdo = Xdo()
xdo.move_mouse(200,100)
