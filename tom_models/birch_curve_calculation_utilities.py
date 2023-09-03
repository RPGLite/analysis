import matplotlib.pyplot as plt
from functools import partial, lru_cache


def delta_birch(c, rgr, y):
  return (rgr * y * (1-y)) / (1 - y + c*y)


def gencurve(c, rgr, start=0.1, limit=0.9):
  delta = partial(delta_birch, c, rgr)
  yvals = [start]
  while yvals[-1] < limit:
    yvals.append(yvals[-1] + delta(yvals[-1]))
  xvals = range(1, len(yvals)+1)
  fig, ax = plt.subplots()
  ax.plot(xvals, yvals)
  ax.set(xlabel="games played", ylabel="birch curve value", title=f"birch curve from {start} to {limit} with rgr={rgr}, c={c}")
  ax.grid()
  fig.savefig(f"birch_c{c}_rgr{rgr}_start{start}_limit{limit}.png")
  plt.show()


@lru_cache
def curve_points(c, rgr, start=0.1, limit=0.9):
  points = [start]
  while points[-1] < limit:
    points.append(points[-1] + delta_birch(c, rgr, points[-1]))
  return points

@lru_cache
def rgr_yielding_num_games_for_c(num_games, c, start=0.1, limit=0.9):
  rgr=0.9999
  while len(curve_points(c, rgr, start, limit)) < num_games:
    rgr -= 0.0001
  return rgr

