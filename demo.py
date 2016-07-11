import sys
import numpy as np

from matplotlib import pyplot as plt

from ekgstore import Parser


if __name__ == '__main__':
  if len(sys.argv) == 2:
    flname = sys.argv[1]
  else:
    flname = 'dat/sample1.pdf'

  parse = Parser(flname)
  waves, units = parse.get_waves()
  x_unit, y_unit = units

  for i, wave in waves:
    plt.plot(wave * y_unit)
    plt.ylim(-20, 20)
    plt.xlim(0, len(wave))
    plt.suptitle(i, fontsize=16)
    plt.show()
    break
