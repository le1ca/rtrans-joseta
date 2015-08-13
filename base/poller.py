import threading, time

class poller:
        
        def __init__(self, transport, delay=0, interval=60):
                self.delay = delay
                self.interval = interval
                self.slaves = {}
                self.transport = transport
                self._continue = True
                self.thread = None
        
        def register_slave(self, slv):
                self.slaves[slv] = slv
        
        def __poll(self):
                for s in self.slaves:
                        self.transport.poll(s)
        
        def run(self):
                time.sleep(self.delay)
                while self._continue:
                        self.__poll()
                        for i in range(0, self.interval):
                                time.sleep(1)
                                if not self._continue:
                                        break
        
        def start(self):
                self.thread = threading.Thread(target=poller.run, args=(self,))
                self.thread.start()
        
        def stop(self):
                self._continue = False
                self.thread.join()
