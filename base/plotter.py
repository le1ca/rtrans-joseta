import time
import matplotlib.pyplot as plt
from Queue import Queue, Empty

class plotter:

        markers = ['o', 'v', '^', 's', 'p', '+', 'x', 'd']

        def __init__(self, path, series, x):
                self.path = path
                self.series = list(set(series) - set([x]))
                self.x = x
                self._mrk_cnt = 0
                self._q = Queue()
        
        def _mrk(self, reset = False):
                if reset:
                        self._mrk_cnt = 0
                ret = plotter.markers[self._mrk_cnt]
                self._mrk_cnt += 1
                if self._mrk_cnt >= len(plotter.markers):
                        self._mrk_cnt = 0
                return ret

        def _proc_plot(self, data):
                f, axes = plt.subplots(len(self.series), sharex=True, figsize=(5, 8.5))
                self._mrk(True)
                for i in range(0,len(self.series)):
                        axes[i].scatter(data[self.x], data[self.series[i]], s=10, marker=self._mrk(), label=self.series[i])
                        axes[i].set_title(self.series[i])
                        #plt.legend(loc='upper left')
                plt.tight_layout(pad=0.5, w_pad=0.8, h_pad=0.4)
                plt.savefig(self.path, format='pdf')
                plt.close()
                
        def make_plot(self, data):
                self._q.put(data)
        
        def plot_loop(self):
                try:
                        while True:
                                try: 
                                        data = self._q.get_nowait()
                                        self._proc_plot(data)
                                        self._q.task_done()
                                except Empty:
                                        time.sleep(0.1)
                except KeyboardInterrupt:
                        return
