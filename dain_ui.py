from textwrap import indent
from numpy.lib.utils import info
import wx
from wx import xrc
import wx.adv
from pathlib import Path
import threading
import multiprocessing
import os
from wx.xrc import XRCID


class myThread (multiprocessing.Process):
    def __init__(self, threadID, name, inputFile, outputPath, interpNum):
        #    threading.Thread.__init__(self)
        multiprocessing.Process.__init__(self)
        self.threadID = threadID
        self.name = name
        self.inputFile = inputFile
        self.outputPath = outputPath
        self.interpNum = interpNum

    def run(self):
        from feature_flow_interface import Resolution720p, Resolution360p
        index = SettersGetterIndex()
        print('Index: ', index.getInterpolationIndex())
        print("Starting " + self.name)

        resolution = CheckResolution(self.inputFile)
        if resolution.getWidth() < int(1280) and resolution.getHeight() < int(720):
            interpolate360 = Resolution360p(
                self.inputFile, self.interpNum, self.outputPath, indexObj, rangeObj)
            interpolate360.runFeatureFlow()
            # interpolate360.imageToVideo()
        else:
            interpolate720 = Resolution720p(
                self.inputFile, self.interpNum, self.outputPath, indexObj, rangeObj)
            interpolate720.splitVideoIntoSections()
            interpolate720.runFeatureFlow()
            interpolate720.stitchVideo()
        print("Exiting " + self.name)


class DainApp(wx.App):
    def OnInit(self):
        self.xrcFile: str = str(Path.cwd() / 'formbuilder' / 'noname.xrc')
        self.res = xrc.XmlResource(self.xrcFile)
        self.init_frame()
        return True

    def init_frame(self):
        self.interpNum: int = 2
        self.inputFile: str = ''
        self.outputPath: str = ''
        self.imgToVideoInputPath: str = ''
        self.FPS: float = 0.0
        self.newFPS: float = 0.0
        self.condition = threading.Condition()

        self.mainFrame = self.res.LoadFrame(None, 'mainFrame')
        self.mainMenuBar = xrc.XRCCTRL(self.mainFrame, 'mainMenuBar')

        self.quitFromMenuBar = xrc.XRCCTRL(self.mainFrame, 'exitMenuItem')
        self.mainFrame.Bind(wx.EVT_MENU, self.onQuit,
                            id=xrc.XRCID('exitMenuItem'))

        self.ogFPS = xrc.XRCCTRL(self.mainFrame, 'ogFPSTextCtrl')
        self.mainFrame.Bind(wx.EVT_BUTTON, self.onSelectFile,
                            id=xrc.XRCID('ogFPSTextCtrl'))

        self.interpFPS = xrc.XRCCTRL(self.mainFrame, 'interpFPSTextCtrl')
        self.mainFrame.Bind(wx.EVT_CHOICE, self.getChoice,
                            id=xrc.XRCID('interpFPSTextCtrl'))

        self.choice = xrc.XRCCTRL(self.mainFrame, 'interpolationChoice')
        self.mainFrame.Bind(wx.EVT_CHOICE, self.getChoice,
                            id=xrc.XRCID('interpolationChoice'))

        self.videoPicker = xrc.XRCCTRL(self.mainFrame, 'videoFilePicker')
        self.mainFrame.Bind(wx.EVT_FILEPICKER_CHANGED,
                            self.onSelectFile, id=xrc.XRCID('videoFilePicker'))

        self.outputPicker = xrc.XRCCTRL(self.mainFrame, 'outputDirPicker')
        self.mainFrame.Bind(wx.EVT_DIRPICKER_CHANGED,
                            self.onSelectOutputDir, id=xrc.XRCID('outputDirPicker'))

        self.interpBtn = xrc.XRCCTRL(self.mainFrame, 'interpBtn')
        self.mainFrame.Bind(
            wx.EVT_BUTTON, self.applicationThreads, id=xrc.XRCID('interpBtn'))

        self.imgToVidInputFolder = xrc.XRCCTRL(
            self.mainFrame, 'imgToVidInputDirPicker')
        self.mainFrame.Bind(wx.EVT_DIRPICKER_CHANGED, self.onSelectImgToVidInputDir, id=xrc.XRCID(
            'imgToVidInputDirPicker'))

        """ self.imgToVidBtn = xrc.XRCCTRL(self.mainFrame, 'imgToVidBtn')
        self.mainFrame.Bind(wx.EVT_BUTTON, self.imgToVideo,
                            id=xrc.XRCID('imgToVidBtn')) """

        self.mainFrame.Show()

    def onQuit(self, event):
        self.mainFrame.Close()

    def getChoice(self, event):
        choice = self.choice.GetStringSelection()
        self.choice.GetCurrentSelection()
        if choice == '2x':
            self.interpFPS.SetValue('')
            print('Interpolation Number: ', choice)
            self.interpNum = 2
            self.newFPS = float(self.FPS * self.interpNum)
            self.interpFPS.write(str(self.newFPS))
        elif choice == '4x':
            self.interpFPS.SetValue('')
            print('Interpolation Number: ', choice)
            self.interpNum = 4
            self.newFPS = float(self.FPS * self.interpNum)
            self.interpFPS.write(str(self.newFPS))
        elif choice == '8x':
            self.interpFPS.SetValue('')
            print('Interpolation Number: ', choice)
            self.interpNum = 8
            self.newFPS = float(self.FPS * self.interpNum)
            self.interpFPS.write(str(self.newFPS))
        # print(self.interpNum)

    def onSelectFile(self, event):
        file = self.videoPicker.GetPath()
        self.inputFile = file

        # fps = FrameRate.getInitialFPS(self.inputFile)
        fps = 0
        self.FPS = fps
        self.ogFPS.SetValue(str(self.FPS))
        print('INPUT FILE : ', self.inputFile)

    def onSelectOutputDir(self, event):
        path = self.outputPicker.GetPath()
        self.outputPath = path
        print('Output Folder: ', self.outputPath)

    def onSelectImgToVidInputDir(self, event):
        path = self.imgToVidInputFolder.GetPath()
        self.imgToVideoInputPath = path
        print('Img To Vid Folder: ', self.imgToVideoInputPath)

    """ def imgToVideo(self, event):
        # from imgToVideoScaled import ImgToVid
        fileName = os.path.splitext(os.path.basename(self.inputFile))[0]
        # img2Vid = ImgToVid()
        img2Vid.run(self.imgToVideoInputPath, fileName) """

    def completeDialog(self):
        wx.MessageBox('Feature Flow has finished interpolating your video. \n Please check your output directory',
                      'Interpolation Complete', wx.OK | wx.ICON_EXCLAMATION)

    def missingFileDialog(self):
        wx.MessageBox('You have not selected an Input Video or and Output Directory. \n Please specify them',
                      'Error', wx.OK | wx.ICON_ERROR)

    def applicationThreads(self, event):
        fflowThread = myThread(
            1, "FeatureFlow", self.inputFile, self.outputPath, self.interpNum)
        dlg = None
        counter = 0
        if self.inputFile == '' and self.outputPath == '':
            self.missingFileDialog()
        else:
            fflowThread.start()
            dlg = wx.ProgressDialog('Interpolating Frames', 'Please wait..',
                                    style=wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME | wx.PD_CAN_ABORT | wx.STAY_ON_TOP)
            # while fflowThread.isAlive():
            while fflowThread.is_alive():
                wx.MilliSleep(300)
                """ dlg.Pulse("Interpolation In Progress {} out of {}".format(
                    indexObj.getInterpolationIndex(), rangeObj.getInterpolationRange())) """
                dlg.Pulse("Interp in progress")
                wx.GetApp().Yield()
                counter += 1
            del dlg
        fflowThread.kill()
        fflowThread.join()
        self.completeDialog()


if __name__ == "__main__":
    app = DainApp(False)
    app.MainLoop()
