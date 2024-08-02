from scanspec.specs import Line, Spiral, Static
from scanspec.regions import Circle, Rectangle
from pcaspy import SimpleServer, Driver
from scanspec.plot import plot_spec
import matplotlib.pyplot as plt
from PIL import Image as im
import numpy as np
import random
import pvdb
import csv
import io

### TODO: getPoints == createScan(), SUBMIT == runScan(), PLOT == plotScan()
###       
class myDriver(Driver):
    def __init__(self):
        super(myDriver, self).__init__()
        # shell execution thread id
        self.tid = None
        ### PVs for ScanSpec
        ## ScanSpec settings
        self.settingsDict = {'scanType': 'Line', 'maskType': 'None',
                             'useX': False, 'useY': False, 'useZ': False,
                             'xAxis': '', 'yAxis': '', 'zAxis': ''}
        self.scanX = False
        ## Start points
        self.startingDict = {'X0': ['xList', 1], 'Y0': ['yList', 0], 'Z0': ['zList', 0]}
        ## End points
        self.endingDict = {'X1': ['xList', 5], 'Y1': ['yList', 0], 'Z1': ['zList', 0]}
        ## Number of scan points
        self.numPointsDict = {'numX': 3, 'numY': 0, 'numZ': 0}
        ## Generated points lists
        self.listDict = {'xList': ['xPoints', [], 'X0', 'X1'], 'yList': ['yPoints', [], 'Y0', 'Y1'], 
                         'zList': ['zPoints', [], 'Z0', 'Z1'], 'axisList': []}
        ## Status bits
        self.scanStatus = {'READY': True, 'RUNNING': False, 
                           'WAITING': False}
        ### PVs for CSS
        ## Buttons
        self.buttonDict = {'getPoints': False, 'CLEAR': False, 
                           'PLOT': False, 'SUBMIT': False}

    
    def createScan(self):
        scanType = self.settingsDict['scanType']
        if self.settingsDict['useX']:
            xAxis = self.settingsDict['xAxis']
            if not xAxis:
                xAxis = 'x'
            x0 = self.startingDict['X0'][1]
            x1 = self.endingDict['X1'][1]
            numX = self.numPointsDict['numX']
            self.scanX = eval(scanType)(axis=xAxis, start=x0, stop=x1, num=numX)
            for p in self.scanX.midpoints():
                self.listDict['xList'][1].append(p[xAxis])
            self.setParam('xPoints', self.listDict['xList'][1])
    
    def plotScan(self):
        if self.listDict['xList'][1]:
            xAxis = self.settingsDict['xAxis']
            if not xAxis:
                xAxis = 'x'
            fig = plt.figure(figsize=(7,5))
            # ax = plt.subplots()
            plt.plot(self.listDict['xList'][1])
            plt.plot(self.listDict['xList'][1], 'bo')
            plt.xlabel(xAxis)
            plt.grid()
            cssPath = '/nsls2/users/sclark2/css-workspace-xf31id/CSS'
            filename = f'{cssPath}/savedImage.png'
            fig.savefig(filename, format='png')
            fig.savefig('savedImage.png', format='png')
            img = im.open(filename)
            
            print(np.asarray(img).shape)
            # io_buf = io.BytesIO()
            # fig.savefig(io_buf, format='jpg', dpi=150)
            # io_buf.seek(0)
            # # img_arr = np.reshape(np.frombuffer(io_buf.getvalue(), dtype=np.uint8), \
            #         #  newshape=(int(fig.bbox.bounds[3]), int(fig.bbox.bounds[2]), -1))
            # img_arr = np.frombuffer(io_buf.getvalue(), dtype=np.uint8)
            # io_buf.close()
            # print(img_arr.shape)
            # array = np.reshape(img_arr, (200, 400))
            # data = im.fromarray(array)
            # data.save(filename)
    
    def submitScan(self):
        pass
    
    def read(self, reason):
        return self.getParam(reason)
    
    def write(self, reason, value):
        status = True
        if reason == 'COMMAND':
            if not self.tid:
                command = value
                self.tid = thread.start_new_thread(self.runShell,(command,))
            else:
                status = False
        elif (reason == 'SUBMIT'):
            self.submitScan()
            return False
        elif reason == 'CLEAR':
            self.__init__()
            return False
        elif reason == 'getPoints':
            self.createScan()
            return False
        elif reason == 'PLOT':
            self.plotScan()
            return False
        elif (reason == 'X0') or (reason == 'Y0') or (reason == 'Z0'):
            try:
                value = float(value)
                self.startingDict[reason][1] = value
            except Exception as _:
                status = False
        elif (reason == 'X1') or (reason == 'Y1') or (reason == 'Z1'):
            try:
                value = float(value)
                self.endingDict[reason][1] = value
            except Exception as _:
                status = False
        elif (reason == 'xList') or (reason == 'yList') or (reason == 'zList'):
            sniffer = csv.Sniffer()
            value = value.strip('[]').strip('{}')
            for v in value.split(sniffer.sniff(value).delimiter):
                try:
                    self.listDict[reason][1].append(float(v))
                except Exception as _:
                    pass
            if self.listDict[reason][1]:
                startValue = self.startingDict[self.listDict[reason][2]][1]
                endValue = self.endingDict[self.listDict[reason][3]][1]
                if (self.listDict[reason][1][0] != startValue):
                    self.listDict[reason][1].insert(0, startValue)
                self.setParam(self.listDict[reason][0], self.listDict[reason][1])
        elif (reason == 'scanType'):
            print(pvdb.settingsDB[reason]['enums'])
            try:
                self.settingsDict[reason] = value
            except Exception as _:
                status = False
                pass
        elif (reason == 'maskType'):
            try:
                self.settingsDict[reason] = value
            except Exception as _:
                status = False
                pass
        elif (reason == 'useX') or (reason == 'useY') or (reason == 'useZ') or \
             (reason == 'xAxis') or (reason == 'yAxis') or (reason == 'zAxis'):
            try:
                self.settingsDict[reason] = value
            except Exception as _:
                status = False
                pass
        elif (reason == 'numX') or (reason == 'numY') or (reason == 'numZ'):
            try:
                value = int(value)
                self.numPointsDict[reason] = value
            except Exception as _:
                status = False
                pass
        elif (reason == 'READY') or (reason == 'RUNNING') or (reason == 'WAITING'):
            if int(value) == 0:
                self.scanStatus[reason] = int(value)
            elif int(value) == 1:
                self.scanStatus[reason] = int(value)
        else:
            status = False
        # store the values
        if status:
            self.setParam(reason, value)
        return status
    
    def runShell(self, command):
        # set status BUSY
        self.setParam('STATUS', 1)
        self.updatePVs()
        # run shell
        try:
            proc = subprocess.Popen(shlex.split(command),
                    stdout = subprocess.PIPE,
                    stderr = subprocess.PIPE)
            proc.wait()
        except OSError as m:
            self.setParam('ERROR', str(m))
            self.setParam('OUTPUT', '')
        else:
            self.setParam('ERROR', proc.stderr.read().rstrip())
            self.setParam('OUTPUT', proc.stdout.read().rstrip())
        # set status DONE
        self.setParam('STATUS', 0)
        self.updatePVs()
        self.tid = None


if __name__ == '__main__':
    server = SimpleServer()
    prefix = 'SCLARK2-TST:'
    server.createPV(prefix, pvdb.settingsDB)
    server.createPV(prefix, pvdb.startingDB)
    server.createPV(prefix, pvdb.endingDB)
    server.createPV(prefix, pvdb.numPointsDB)
    server.createPV(prefix, pvdb.pointListDB)
    server.createPV(prefix, pvdb.scanStatusDB)
    server.createPV(prefix, pvdb.buttonDB)
    server.createPV(prefix, pvdb.commandDB)
    driver = myDriver()
    while True:
        # process CA transactions
        server.process(0.1)