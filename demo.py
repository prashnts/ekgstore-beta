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
    plt.plot(wave)
    plt.ylim(-6 * y_unit, 6 * y_unit)
    plt.xlim(0, len(wave))
    plt.xticks(np.arange(0, len(wave) + 1, x_unit))
    plt.yticks(np.arange(-6 * y_unit, 6 * y_unit, y_unit))
    plt.tick_params(
        axis='both',
        which='both',
        bottom='off',
        top='off',
        labelbottom='off',
        right='off',
        left='off',
        labelleft='off')
    plt.suptitle(i, fontsize=16)
    plt.grid()
    plt.show()
    break
