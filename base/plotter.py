import matplotlib.pyplot as plt

class plotter:

        markers = ['o', 'v', '^', 's', 'p', '+', 'x', 'd']

        def __init__(self, path, series, x):
                self.path = path
                self.series = list(set(series) - set(x))
                self.x = x
                self._mrk_cnt = 0
        
        def _mrk(self, reset = False):
                if reset:
                        self._mrk_cnt = 0
                ret = plotter.markers[self._mrk_cnt]
                self._mrk_cnt += 1
                if self._mrk_cnt >= len(plotter.markers):
                        self._mrk_cnt = 0
                return ret

        def make_plot(self, data):
                fig = plt.figure()
                f, axes = plt.subplots(len(self.series), sharex=True)
                self._mrk(True)
                for i in range(0,len(self.series)):
                        axes[i].scatter(data[self.x], data[self.series[i]], s=10, marker=self._mrk(), label=self.series[i])
                        axes[i].set_title(self.series[i])
                        #plt.legend(loc='upper left')
                plt.savefig(self.path, format='pdf')
                plt.close()
