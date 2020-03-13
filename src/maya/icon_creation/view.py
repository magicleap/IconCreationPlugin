# -*- coding: latin-1 -*-

import os
import platform
import logging

from PySide2 import QtWidgets, QtCore, QtGui

from . import constants
from . import utils
from . import core


LOG = logging.getLogger(__name__)


def newIcon():
    mayaWindow = utils.mayaMainWindow()

    dialog = NewPortalIconDialog(mayaWindow)
    dialog.show()


def openIcon():
    mayaWindow = utils.mayaMainWindow()

    dialog = OpenIconDialog(mayaWindow)
    dialog.show()


class LogoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(LogoWidget, self).__init__(parent=parent)

        mainLayout = QtWidgets.QHBoxLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.logo = QtWidgets.QLabel('')
        self.logo.setPixmap(utils.magicLeapLogoIcon().pixmap(296/2, 46/2))
        mainLayout.addWidget(self.logo)
        self.pressPos = None
        self.window = None

    # Support moving the window when clicking and dragging the widget.

    def setWindow(self, window):
        self.window = window

    def mousePressEvent(self, event):
        if not self.window:
            return

        self.pressPos = event.pos()
        self.isMoving = True

    def mouseMoveEvent(self, event):
        if self.window and self.isMoving:
            diff = event.pos() - self.pressPos
            self.window.move(self.window.pos()+diff)

    def mouseReleaseEvent(self, event):
        if not self.window:
            return
        self.isMoving = False

class CopyrightFooterWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(CopyrightFooterWidget, self).__init__(parent=parent)

        spacer = QtWidgets.QWidget()

        self.info = QtWidgets.QLabel(text='Copyright © 2018 - 2020 Magic Leap, Inc.')

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignRight)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addWidget(self.info, 0)


class NewPortalIconDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(NewPortalIconDialog, self).__init__(parent=parent)

        # Configure the QWidget properties.
        self.setObjectName('NewPortalIconDialog')
        self.setWindowTitle('New Portal Icon')
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        mainLayout.setContentsMargins(10, 10, 10, 10)
        mainLayout.setSpacing(5)

        self.logoWidget = LogoWidget()
        self.logoWidget.setWindow(self)
        mainLayout.addWidget(self.logoWidget)

        # Try adding a gif
        self.sampleIconGIF = QtWidgets.QLabel('')
        self.sampleIconGIFMovie = utils.samplePortalIconMovie()
        self.sampleIconGIFMovie.start()
        self.sampleIconGIF.setMovie(self.sampleIconGIFMovie)
        mainLayout.addWidget(self.sampleIconGIF)

        subNewIconLayout = QtWidgets.QHBoxLayout()
        subNewIconLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.addLayout(subNewIconLayout)

        subNewIconLayout.addStretch(1)
        subNewIconLayout.addWidget(self.sampleIconGIF, 0)

        subTextLayout = QtWidgets.QVBoxLayout()
        subTextLayout.setContentsMargins(0,0,0,0)
        subTextLayout.addStretch(1)

        self.title = QtWidgets.QLabel(text='New Portal Icon')
        self.title.setStyleSheet('font: 18pt;')
        subTextLayout.addWidget(self.title)

        self.info = QtWidgets.QLabel(text="<a href=\"https://developer.magicleap.com/learn/guides/configure-and-add-portal-icon\" style=\"color: rgb(241, 39, 66) ;\">What's a portal icon?</a>")
        self.info.setTextFormat(QtCore.Qt.RichText);
        self.info.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction);
        self.info.setOpenExternalLinks(True)
        subTextLayout.addWidget(self.info)

        subTextLayout.addStretch(1)
        subNewIconLayout.addLayout(subTextLayout, 0)
        subNewIconLayout.addStretch(1)
        mainLayout.addLayout(subNewIconLayout)
        mainLayout.addSpacing(6)

        self.filePathField = FilePathWidget(title='Save Maya File:', displayText='', saveFile=True, getFile=False, getDirectory=False)
        mainLayout.addWidget(self.filePathField)

        self.okButton = QtWidgets.QPushButton('Create')
        self.okButton.setDefault(True);
        self.cancelButton = QtWidgets.QPushButton('Cancel')

        subWidget = QtWidgets.QWidget()
        mainLayout.addWidget(subWidget)
        subLayout = QtWidgets.QHBoxLayout(subWidget)
        subLayout.setContentsMargins(0, 0, 0, 0)
        
        subLayout.addWidget(self.okButton)
        subLayout.addWidget(self.cancelButton)

        mainLayout.addSpacing(12)

        copyrightWidget = CopyrightFooterWidget()
        mainLayout.addWidget(copyrightWidget)

        self.okButton.clicked.connect(self.onOK)
        self.cancelButton.clicked.connect(self.onCancel)

    def sizeHint(self):
        desktopWidget = QtWidgets.QApplication.desktop()
        geometry = desktopWidget.screenGeometry()
        return QtCore.QSize(geometry.width()/4, geometry.height()/8)

    def onOK(self):
        filePath = self.filePathField.filePath
        scene = utils.newScene(filePath)
        LOG.info(scene)

        LOG.info('Importing Icon template.')

        core.importTemplate()

        panel = PortalIconTool.run()
        panel.setupWidget.setFPS()
        panel.setupWidget.setUnits()
        
        self.accept()

    def onCancel(self):
        LOG.info('User cancelled creating a new Icon.')
        self.reject()


class OpenIconDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(OpenIconDialog, self).__init__(parent=parent)

        # Configure the QWidget properties.
        self.setObjectName('OpenIconDialog')
        self.setWindowTitle('Open Icon')
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        mainLayout.setContentsMargins(5, 5, 5, 5)
        mainLayout.setSpacing(5)

        self.logoWidget = LogoWidget()
        mainLayout.addWidget(self.logoWidget)

        self.title = QtWidgets.QLabel(text='Open Icon')
        self.title.setStyleSheet('font: 24pt;')
        mainLayout.addWidget(self.title)

        self.info = QtWidgets.QLabel(text='Open an existing Icon created by this tool to edit.')
        mainLayout.addWidget(self.info)

        self.filePathField = FilePathWidget(title='Open Maya File:', displayText='', saveFile=False, getFile=True, getDirectory=False)
        mainLayout.addWidget(self.filePathField)

        self.okButton = QtWidgets.QPushButton('Open')
        self.cancelButton = QtWidgets.QPushButton('Cancel')

        subWidget = QtWidgets.QWidget()
        mainLayout.addWidget(subWidget)
        subLayout = QtWidgets.QHBoxLayout(subWidget)

        subLayout.addWidget(self.okButton)
        subLayout.addWidget(self.cancelButton)

        copyrightWidget = CopyrightFooterWidget()
        mainLayout.addWidget(copyrightWidget)

        self.okButton.clicked.connect(self.onOK)
        self.cancelButton.clicked.connect(self.onCancel)

    def sizeHint(self):
        desktopWidget = QtWidgets.QApplication.desktop()
        geometry = desktopWidget.screenGeometry()
        return QtCore.QSize(geometry.width()/4, geometry.height()/8)

    def onOK(self):
        filePath = self.filePathField.filePath

        sceneOpened = utils.openScene(filePath)

        if not sceneOpened:
            return

        PortalIconTool.run()
        
        self.accept()

    def onCancel(self):
        LOG.info('User cancelled opening an Icon.')
        self.reject()


class PortalIconTool(QtWidgets.QWidget):
    @staticmethod
    def run():
        mayaWindow = utils.mayaMainWindow()

        if not core.iconTemplateExists():
            QtWidgets.QMessageBox.critical(mayaWindow, '', 'Icon Error\nUse the Magic Leap menu to start a new Icon or open an existing one.')
            return

        widget = PortalIconTool(parent=mayaWindow)
        widget.move(
            mayaWindow.frameGeometry().center() - QtCore.QRect(QtCore.QPoint(),
            widget.sizeHint()).center()
        )
        widget.show()

        return widget

    def __init__(self, parent=None):
        super(PortalIconTool, self).__init__(parent=parent)

        # Configure the QWidget properties.
        self.setObjectName('PortalIconToolWidget')
        
        self.setWindowTitle('Portal Icon')
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.Window)
        if utils.isMacOS():
            # MacOS is special, and the QtCore.Qt.Window flag does not sort the windows properly,
            # so instead QtCore.Qt.Tool is used.
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.Tool)

        logoWidget = LogoWidget()
        self.setupWidget = IconSetupWidget(self)
        self.materialsWidget = IconMaterialsWidget(self)
        self.animationsWidget = AnimationWidget(self)
        self.finalizeWidget = IconFinalizeWidget(self)
        self.previewWidget = IconPreviewWidget(self)
        copyrightWidget = CopyrightFooterWidget()

        # Setup root QLayout object, all children widgets will be children of this QLayout.
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        main_layout.addWidget(logoWidget)
        main_layout.addWidget(self.setupWidget)
        main_layout.addWidget(self.materialsWidget)
        main_layout.addWidget(self.animationsWidget)
        main_layout.addWidget(self.finalizeWidget)
        main_layout.addWidget(self.previewWidget)
        main_layout.addStretch(1)
        main_layout.addWidget(copyrightWidget)

    def sizeHint(self):
        return QtCore.QSize(350, 500)


class FilePathWidget(QtWidgets.QWidget):
    filePathChanged = QtCore.Signal(str)

    def __init__(self, title, displayText, getDirectory=True, getFile=False, saveFile=False, parent=None):
        super(FilePathWidget, self).__init__(parent=parent)

        self._getDirectory = getDirectory
        self._getFile = getFile
        self._saveFile = saveFile
        self._title = title

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)

        main_layout.addWidget(QtWidgets.QLabel(title))

        sub_layout = QtWidgets.QHBoxLayout()
        sub_layout.setContentsMargins(0, 0, 0, 0)
        sub_layout.setSpacing(5)

        main_layout.addLayout(sub_layout)

        self.outputField = QtWidgets.QLineEdit()
        self.outputField.setMinimumHeight(24)
        self.outputField.setPlaceholderText(displayText)
        sub_layout.addWidget(self.outputField)

        self.openFileBrowserButton = ActionButton('...')
        self.openFileBrowserButton.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sub_layout.addWidget(self.openFileBrowserButton)

        self.openFileBrowserButton.clicked.connect(self.openOutputDialog)
        self.outputField.textChanged.connect(self.filePathChanged.emit)

    def openOutputDialog(self):
        if self._getDirectory:
            result = QtWidgets.QFileDialog.getExistingDirectory(self, self._title, utils.getProjectDirectory())
        elif self._getFile:
            result = QtWidgets.QFileDialog.getOpenFileName(self, self._title, utils.getProjectDirectory())[0]
        elif self._saveFile:
            result = QtWidgets.QFileDialog.getSaveFileName(self, self._title, utils.getProjectDirectory(), 'Maya Ascii (*.ma)')[0]

        if not result:
            return

        self.outputField.setText(result)
        self.filePathChanged.emit(self.outputField.text())

    @property
    def filePath(self):
        return self.outputField.text()

    @filePath.setter
    def filePath(self, text):
        self.outputField.setText(text)


class AnimationWidget(QtWidgets.QWidget):
    clipChanged = QtCore.Signal(object)
    statusChecked = QtCore.Signal()

    defaultStepData = dict(message='Set the animation clips', status=False, required=False)

    def __init__(self, parent=None):
        super(AnimationWidget, self).__init__(parent=parent)

        self._stepData = IconStepObject()
        self._stepData.statusChanged.connect(self.updateProgress)
        self._stepData['callback'] = self.check
        for k, v in self.defaultStepData.items():
            self._stepData[k] = v
        
        self.data = dict()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(1)

        contentLayout = QtWidgets.QVBoxLayout()
        
        # Add editable animation clips.
        clipOffset = 1
        animData = core.getAnimationData()
        
        for clipName, duration in constants.ICON_ANIMATION_CLIPS:
            newClipWidget = AnimationClipWidget(clipName, clipOffset, (clipOffset + duration - 1))
            newClipWidget.playClipToggled.connect(self.stopOtherClips)
            self.data[clipName] = newClipWidget
            contentLayout.addWidget(newClipWidget)
            
            if clipName in animData:
                newClipWidget.clipEnabled = True
                newClipWidget.startFrame = animData[clipName]['startFrame']
                newClipWidget.endFrame = animData[clipName]['endFrame']

            clipOffset += duration + 1

        self.frameWidget = CollapseWidget(title='Setup Animations (Optional)', stepData=self._stepData.serialized, parent=parent)
        self.frameWidget.setContentLayout(contentLayout)
        main_layout.addWidget(self.frameWidget)

        for clipWidget in self.data.values():
            clipWidget.clipChanged.connect(self.updateClipData)

    def showEvent(self, event):
        self._stepData.checkStepStatus.emit()
        super(AnimationWidget, self).showEvent(event)

    def enterEvent(self, event):
        self._stepData.checkStepStatus.emit()
        super(AnimationWidget, self).enterEvent(event)

    @property
    def stepData(self):
        return self._stepData

    def stopOtherClips(self):
        for clipWidget in self.data.values():
            if clipWidget._isPlaying:
                clipWidget.playClip()

    def updateClipData(self, payload):
        core.updateClipData(payload)

        self._stepData.checkStepStatus.emit()

    def updateProgress(self, checked):
        self.frameWidget.completed.emit(checked)
        self.statusChecked.emit()

    def check(self):
        checked = False

        for clipWidget in self.data.values():
            if not clipWidget.clipEnabled:
                continue
            
            checked = True

            currentRange = clipWidget.endFrame - clipWidget.startFrame
            if currentRange > clipWidget.maxClipSize:
                LOG.exception('%s take requires (%s), current (%s)', clipWidget.clipName, clipWidget.maxClipSize, currentRange)
                checked = False

            clipChecked = core.checkTakeForAnimation(clipWidget.startFrame, clipWidget.endFrame)
            if not clipChecked:
                LOG.exception('%s take missing keyframe at start or end.', clipWidget.clipName)
                checked = False

        return checked


class AnimationClipWidget(QtWidgets.QWidget):
    setRangeIcon = utils.setRangeIcon()
    playIcon = utils.playIcon()
    pauseIcon = utils.pauseIcon()

    minClipFrame = 0
    maxClipFrame = 10000

    clipChanged = QtCore.Signal(object)
    playClipToggled = QtCore.Signal()

    def __init__(self, clipName, startFrame, endFrame, parent=None):
        super(AnimationClipWidget, self).__init__(parent=parent)

        self._isPlaying = False
        self._maxClipSize = endFrame - startFrame + 1

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignLeft)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        self.enableClip = QtWidgets.QCheckBox('')
        self.enableClip.setToolTip('Toggle clip export.')
        main_layout.addWidget(self.enableClip)

        self.title = QtWidgets.QLineEdit('')
        self.title.setToolTip('Clip name (Not Editable). Max number of frames - {0}.'.format(self.maxClipSize))
        self.title.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        self.title.setReadOnly(True)
        main_layout.addWidget(self.title)

        self.startField = QtWidgets.QSpinBox()
        self.startField.setToolTip('First frame of clip.')
        self.startField.setMinimum(self.minClipFrame)
        self.startField.setMaximum(self.maxClipFrame)
        self.startField.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.startField.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        main_layout.addWidget(self.startField)

        self.endField = QtWidgets.QSpinBox()
        self.endField.setToolTip('Last frame of clip.')
        self.endField.setMinimum(self.minClipFrame)
        self.endField.setMaximum(self.maxClipFrame)
        self.endField.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.endField.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        main_layout.addWidget(self.endField)

        self.playButton = QtWidgets.QPushButton(self.playIcon, '')
        self.playButton.setIconSize(QtCore.QSize(10, 10))
        self.playButton.setToolTip('Play the clip.')
        main_layout.addWidget(self.playButton)

        self.setRangeButton = QtWidgets.QPushButton()
        self.setRangeButton.setIcon(self.setRangeIcon)
        self.setRangeButton.setIconSize(QtCore.QSize(10, 10))
        self.setRangeButton.setToolTip('Set timeline to clip start/end frames.')
        main_layout.addWidget(self.setRangeButton)

        # Set default values.
        self.title.setText(clipName)
        self.startField.setValue(startFrame)
        self.endField.setValue(endFrame)

        # Hook up signals.
        self.enableClip.stateChanged.connect(self.updateClipData)
        self.startField.valueChanged.connect(self.updateClipData)
        self.endField.valueChanged.connect(self.updateClipData)
        self.setRangeButton.clicked.connect(self.setActiveClip)
        self.playButton.clicked.connect(self.playClip)

    def paintEvent(self, event):
        if self.clipSize > self.maxClipSize:
            widgetPalette = self.title.palette()
            widgetPalette.setColor(QtGui.QPalette.Base, QtCore.Qt.red)
            self.title.setPalette(widgetPalette)
        else:
            widgetPalette = self.title.palette()
            widgetPalette.setColor(QtGui.QPalette.Base, QtCore.Qt.transparent)
            self.title.setPalette(widgetPalette)

        super(AnimationClipWidget, self).paintEvent(event)

    @property
    def clipName(self):
        return self.title.text()

    @property
    def maxClipSize(self):
        return self._maxClipSize

    @property
    def clipSize(self):
        return self.endFrame - self.startFrame + 1

    @property
    def clipEnabled(self):
        return self.enableClip.isChecked()
    
    @clipEnabled.setter
    def clipEnabled(self, checked):
        self.enableClip.setChecked(checked)

    @property
    def startFrame(self):
        return self.startField.value()

    @startFrame.setter
    def startFrame(self, value):
        self.startField.setValue(value)

    @property
    def endFrame(self):
        return self.endField.value()
        
    @endFrame.setter
    def endFrame(self, value):
        self.endField.setValue(value)

    @property
    def payload(self):
        return {
            'name': self.clipName,
            'enabled': self.clipEnabled,
            'startFrame': self.startFrame,
            'endFrame': self.endFrame
        }

    def updateClipData(self, value):
        self.clipChanged.emit(self.payload)

    def playClip(self):
        if not self._isPlaying:
            self.playClipToggled.emit()

        self._isPlaying = not(self._isPlaying)

        utils.playAnimation(self.startFrame, self.endFrame, self._isPlaying)

        if self._isPlaying:
            self.playButton.setIcon(self.pauseIcon)
        else:
            self.playButton.setIcon(self.playIcon)

    def setActiveClip(self):
        utils.setAnimationTimeline(self.startFrame, self.endFrame)


class IconStepObject(QtCore.QObject):
    checkStepStatus = QtCore.Signal()
    statusChanged = QtCore.Signal(bool)

    defaultStepData = dict(message='Templated message', status=False, required=False, callback=None)

    def __init__(self, parent=None):
        super(IconStepObject, self).__init__(parent=parent)

        self._stepData = self.defaultStepData.copy()
        self.checkStepStatus.connect(self.check)

    def __getitem__(self, key):
        return self._stepData[key]

    def __setitem__(self, key, value):
        self._stepData[key] = value

    @property
    def stepData(self):
        return self._stepData

    @property
    def serialized(self):
        return self._stepData

    def check(self):
        if self._stepData['callback'] is not None:
            checked = self._stepData['callback']()
            self._stepData['status'] = checked
            self.statusChanged.emit(checked)


class FieldWidget(QtWidgets.QWidget):
    text = 0
    dropdown = 1
    number = 2

    showError = QtCore.Signal()
    hideError = QtCore.Signal()
    toggleError = QtCore.Signal(bool)
    toolClicked = QtCore.Signal()

    def __init__(self, title, fieldType, required=False, parent=None):
        super(FieldWidget, self).__init__(parent=parent)

        self._title = title
        self._required = required
        self._fieldType = fieldType

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.setAlignment(QtCore.Qt.AlignTop)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        labelText = title
        if self._required:
            labelText += ' (required)'
        self.fieldLabel = QtWidgets.QLabel(labelText)
        mainLayout.addWidget(self.fieldLabel)

        subWidget = QtWidgets.QWidget()
        mainLayout.addWidget(subWidget)
        subLayout = QtWidgets.QHBoxLayout(subWidget)
        subLayout.setAlignment(QtCore.Qt.AlignLeft)
        subLayout.setContentsMargins(0, 0, 0, 0)
        subLayout.setSpacing(5)

        self.field = QtWidgets.QLineEdit()
        subLayout.addWidget(self.field, 1)

        self.toolButton = QtWidgets.QPushButton('')
        self.toolButton.setStyleSheet('QPushButton { padding: 0;margin: 0 }')
        self.toolButton.setIcon(utils.wrenchIcon())
        subLayout.addWidget(self.toolButton, 0)

        self.fieldErrorMessage = QtWidgets.QLabel()
        mainLayout.addWidget(self.fieldErrorMessage)
        # self.fieldErrorMessage.hide()

        self.toolButton.clicked.connect(self.toolClicked.emit)
        self.toggleError.connect(self.onToggleError)
        self.showError.connect(self.onShowError)
        self.hideError.connect(self.onHideError)

        self._setErrorMessageColor()

    def _setErrorMessageColor(self):
        palette = self.fieldErrorMessage.palette()
        palette.setColor(self.fieldErrorMessage.foregroundRole(), QtGui.QColor(241, 39, 66))
        self.fieldErrorMessage.setPalette(palette)

    def onToggleError(self, errored):
        if errored:
            self.showError.emit()
        else:
            self.hideError.emit()

    def onShowError(self):
        self.fieldErrorMessage.show()

    def onHideError(self):
        self.fieldErrorMessage.hide()

    def setErrorMessage(self, text):
        self.fieldErrorMessage.setText(text)

    def setDisplayOnly(self, value):
        self.field.setReadOnly(value)


class IconSetupWidget(QtWidgets.QWidget):
    statusChecked = QtCore.Signal()

    defaultStepData = dict(message='Using the Icon Template', status=False, required=True)

    def __init__(self, parent=None):
        super(IconSetupWidget, self).__init__(parent=parent)

        self._stepData = IconStepObject()
        self._stepData.statusChanged.connect(self.updateProgress)
        self._stepData['callback'] = self.check
        for k, v in self.defaultStepData.items():
            self._stepData[k] = v

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.unitsField = FieldWidget('Units', FieldWidget.text, required=True)
        self.unitsField.setDisplayOnly(True)
        self.unitsField.setErrorMessage('Scene units not set to Centimeters(CM)')

        self.fpsField = FieldWidget('Time', FieldWidget.text, required=True)
        self.fpsField.setDisplayOnly(True)
        self.fpsField.setErrorMessage('Scene FPS not set to 60')

        contentLayout = QtWidgets.QVBoxLayout()
        contentLayout.addWidget(self.unitsField)
        contentLayout.addWidget(self.fpsField)

        self.frameWidget = CollapseWidget(title='Configure Scene', stepData=self._stepData.serialized, parent=parent)
        self.frameWidget.setContentLayout(contentLayout)
        main_layout.addWidget(self.frameWidget)

        self.unitsField.toolClicked.connect(self.setUnits)
        self.fpsField.toolClicked.connect(self.setFPS)

    def showEvent(self, event):
        self.unitsField.field.setText(core.getUnitsValue())
        self.fpsField.field.setText(core.getFPSValue())

        self._stepData.checkStepStatus.emit()

        super(IconSetupWidget, self).showEvent(event)

    def enterEvent(self, event):
        sceneChecks = core.checkSceneSettings()

        self.unitsField.toggleError.emit(not sceneChecks['units'])

        self.fpsField.toggleError.emit(not sceneChecks['fps'])

        super(IconSetupWidget, self).enterEvent(event)

    def setUnits(self):
        core.setSceneSettings(units=True, fps=False)
        
        self.unitsField.field.setText(core.getUnitsValue())
        
        sceneChecks = core.checkSceneSettings()
        self.unitsField.toggleError.emit(not sceneChecks['units'])

        self._stepData.checkStepStatus.emit()

    def setFPS(self):
        core.setSceneSettings(units=False, fps=True)

        self.fpsField.field.setText(core.getFPSValue())
        
        sceneChecks = core.checkSceneSettings()
        self.fpsField.toggleError.emit(not sceneChecks['fps'])

        self._stepData.checkStepStatus.emit()

    @property
    def stepData(self):
        return self._stepData

    def updateProgress(self, checked):
        self.frameWidget.completed.emit(checked)
        self.statusChecked.emit()

    def check(self):
        sceneChecks = core.checkSceneSettings()
        
        return all([x for x in sceneChecks.values()])


class IconMaterialsWidget(QtWidgets.QWidget):
    statusChecked = QtCore.Signal()
    
    defaultStepData = dict(message='Use up to 5 materials to use across your Icon.', status=False, required=True)

    maxMaterialsForIcon = 5
    portalSkySphereMaterialCount = 1

    def __init__(self, parent=None):
        super(IconMaterialsWidget, self).__init__(parent=parent)

        self._stepData = IconStepObject()
        self._stepData.statusChanged.connect(self.updateProgress)
        self._stepData['callback'] = self.check
        for k, v in self.defaultStepData.items():
            self._stepData[k] = v

        self._materials = []
        self._unsupportedMaterials = []
        self._data = []

        self.errorMessage = QtWidgets.QLabel('')
        self.errorMessage.hide()
        
        self.refreshButton = ActionButton('Refresh Material List')
        
        contentLayout = QtWidgets.QVBoxLayout(self)

        contentLayout.addWidget(self.refreshButton)
        contentLayout.addWidget(self.errorMessage)

        for index in range(self.maxMaterialsForIcon + self.portalSkySphereMaterialCount):
            widget = MaterialSelectorWidget()
            widget.materialUpdated.connect(self._stepData.checkStepStatus.emit)
            contentLayout.addWidget(widget)
            self._data.append(widget)

        self.frameWidget = CollapseWidget(title='Assign Materials', stepData=self._stepData.serialized, parent=parent)
        self.frameWidget.setContentLayout(contentLayout)
        self.frameWidget.expand()
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        main_layout.addWidget(self.frameWidget)

        self.loadMaterials()
        self.populateMaterials()

        self.refreshButton.clicked.connect(self.refresh)

    def showEvent(self, event):
        self._stepData.checkStepStatus.emit()
        super(IconMaterialsWidget, self).showEvent(event)

    @property
    def stepData(self):
        return self._stepData

    @property
    def materialCount(self):
        return len(self._materials)

    @property
    def materialCountMax(self):
        return self.maxMaterialsForIcon + self.portalSkySphereMaterialCount

    def updateProgress(self, checked):
        self.frameWidget.completed.emit(checked)
        self.statusChecked.emit()

    def check(self):
        checked = True

        if self.materialCount >= self.materialCountMax or self.materialCount == 0:
            checked = False

        textures = core.getTexturesFromMaterials(self._materials)
        if len(textures) != len(self._materials):
            checked = False

        for texture in textures:
            if not core.getFilePathFromTexture(texture):
                checked = False
                break

        if self._unsupportedMaterials:
            self._setErrorMessage()
            checked = False
        else:
            self.errorMessage.hide()

        return checked

    def refresh(self):
        self.loadMaterials()

        self.populateMaterials()

        self._stepData.checkStepStatus.emit()

    def _setErrorMessage(self):
        self.errorMessage.show()
        err = 'Found unsupported material types on some meshes:'
        for mat in self._unsupportedMaterials:
            err += '\n -{0}'.format(mat)
        err += '\n Lambert, Phong, and Blinn materials are only supported.'
        self.errorMessage.setText(err)
        palette = self.errorMessage.palette()
        palette.setColor(self.errorMessage.foregroundRole(), QtGui.QColor(241, 39, 66))
        self.errorMessage.setPalette(palette)
        self.errorMessage.setMargin(5)

    def loadMaterials(self):
        modelNode = core.getModelComponentNode()
        portalNode = core.getPortalComponentNode()
        componentNodes = [modelNode, portalNode]

        if modelNode is None or portalNode is None:
            return

        materials = []
        unsupportedMaterials = []
        for node in componentNodes:
            meshes = core.getMeshesRecursive(node=node)
            mats, unsupported = core.getMaterialsForMeshes(meshes)
            materials.extend(mats)
            unsupportedMaterials.extend(unsupported)

        self._materials = list(set(materials))
        self._unsupportedMaterials = list(set(unsupportedMaterials))

        LOG.info('unsupported mats on load: {0}'.format(self._unsupportedMaterials))

    def populateMaterials(self):
        self.clear()

        LOG.info('Loading materials %s', self._materials)

        for n, mat in enumerate(self._materials):
            self._data[n].loadMaterial(mat)

    def clear(self):
        for index in reversed(range(self.maxMaterialsForIcon + self.portalSkySphereMaterialCount)):
            widget = self._data[index]
            widget.materialOption.setText('Unused Material')
            widget.openMaterialButton.clearMaterial()
            widget.setEnabled(False)
            

class MaterialSelectorWidget(QtWidgets.QWidget):
    materialUpdated = QtCore.Signal()

    def __init__(self, materialName='', parent=None):
        super(MaterialSelectorWidget, self).__init__(parent=parent)

        self._materialNodePath = None
        self.setEnabled(True)

        self.materialOption = QtWidgets.QPushButton(materialName)
        self.materialOption.setFlat(True)

        self.openMaterialButton = MaterialButton()

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignRight)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(5)

        main_layout.addWidget(self.materialOption, 1)
        main_layout.addWidget(self.openMaterialButton, 0)

        self.materialOption.clicked.connect(self.selectMaterial)
        self.openMaterialButton.materialChanged.connect(self.setMaterial)

    def setMaterial(self, textureFilePath):
        core.setColorTexture(self._materialNodePath, textureFilePath)
        self.materialUpdated.emit()
        self.materialOption.setToolTip('Material: {0}\n Texture: {1}'.format(self._materialNodePath, textureFilePath))

    def selectMaterial(self):
        core.selectNodes(self._materialNodePath)
        utils.openAttributeEditor()

    def loadMaterial(self, nodePath):
        self.setEnabled(True)
        self._materialNodePath = nodePath
        # This length value is hardcoded so it fits the default size of the widget.
        if len(nodePath) > 30:
            self.materialOption.setText(nodePath[:30] + '...')
        else:
            self.materialOption.setText(nodePath)

        texture = core.getTexture(self._materialNodePath)
        if texture:
            textureFilePath = core.getFilePathFromTexture(texture)
            if textureFilePath:
                self.openMaterialButton.setMaterial(textureFilePath)


class MaterialButton(QtWidgets.QPushButton):
    materialChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(MaterialButton, self).__init__(text='', parent=parent)

        self.setToolTip('Click to set the material color texture.')
        self.clearMaterial()

        self.clicked.connect(self.addNewTexture)

    def sizeHint(self):
        return QtCore.QSize(35, 35)

    def setMaterial(self, filePath):
        icon = QtGui.QIcon(filePath)
        self.setIcon(icon)
        self.setIconSize(self.sizeHint())

        self.materialChanged.emit(filePath)

    def clearMaterial(self):
        icon = utils.materialEmptyIcon()
        self.setIcon(icon)
        self.setIconSize(self.sizeHint())

    def addNewTexture(self):
        result = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Add Texture',
            utils.getSceneDirectory(),
            'PNG (*.png)'
        )

        if result[0]:
            self.setMaterial(result[0])


class IconPreviewWidget(QtWidgets.QWidget):
    statusChecked = QtCore.Signal()

    defaultStepData = dict(message='Preview on the ML1', status=False, required=False)

    def __init__(self, parent=None):
        super(IconPreviewWidget, self).__init__(parent=parent)

        self._previewed = False

        self._stepData = IconStepObject()
        self._stepData.statusChanged.connect(self.updateProgress)
        self._stepData['callback'] = self.check
        for k, v in self.defaultStepData.items():
            self._stepData[k] = v

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.sdkPathWidget = FilePathWidget(title='MLSDK Path', displayText='/path/to/mlsdk')
        self.sdkPathWidget.setToolTip('Where your MLSDK version folder resides.')

        self.previewButton = QtWidgets.QPushButton('Upload to ML Device')
        self.previewButton.setToolTip('Load the Icon you created onto your Magic Leap device.')

        contentLayout = QtWidgets.QVBoxLayout()
        contentLayout.addWidget(self.sdkPathWidget)
        contentLayout.addWidget(self.previewButton)

        self.frameWidget = CollapseWidget(title='Preview On Device', stepData=self._stepData.serialized, parent=parent)
        self.frameWidget.setContentLayout(contentLayout)
        main_layout.addWidget(self.frameWidget)

        self.sdkPathWidget.filePathChanged.connect(self.saveSDKPath)
        self.previewButton.clicked.connect(self.showPreview)

    def showEvent(self, event):
        self.loadData()
        self._stepData.checkStepStatus.emit()
        super(IconPreviewWidget, self).showEvent(event)

    @property
    def stepData(self):
        return self._stepData

    def showPreview(self):
        LOG.info('Start preview Icon on device.')

        settingsData = core.getIconSettings()
        
        sdkPath = settingsData.get('sdkPath', None)
        if sdkPath is None:
            QtWidgets.QMessageBox.critical(self, '', 'Preview Error\nSet the `MLSDK Path` field before previewing.')
            return

        outputPath = settingsData.get('outputPath', None)
        if outputPath is None:
            QtWidgets.QMessageBox.critical(self, '', 'Preview Error\nSet the `Output Folder` field before previewing.')
            return

        core.buildIcon(validate=True, export=True, cleanup=False)

        iconZipPath = core.createIconZip()

        result = core.openIconPreviewer(iconZipPath, settingsData['sdkPath'])

        if not result:
            self._previewed = True
        else:
            self._previewed = False
            QtWidgets.QMessageBox.critical(self, 'Preview Error', result)

        self._stepData.checkStepStatus.emit()

    def saveSDKPath(self, text):
        core.saveSDKPath(text)
        self._stepData.checkStepStatus.emit()
        self.statusChecked.emit()

    def loadData(self):
        settingsData = core.getIconSettings()
        if 'sdkPath' in settingsData:
            self.sdkPathWidget.filePath = settingsData['sdkPath']

    def updateProgress(self, checked):
        self.frameWidget.completed.emit(checked)
        self.statusChecked.emit()

    def check(self):
        hasMLSDKPath = False

        if self.sdkPathWidget.filePath:
            hasMLSDKPath = True

        return all([x for x in [hasMLSDKPath, self._previewed]])


class IconFinalizeWidget(QtWidgets.QWidget):
    statusChecked = QtCore.Signal()

    defaultStepData = dict(message='Validate the Icon', status=False, required=True)

    def __init__(self, parent=None):
        super(IconFinalizeWidget, self).__init__(parent=parent)

        self._validated = False

        self._stepData = IconStepObject()
        self._stepData.statusChanged.connect(self.updateProgress)
        self._stepData['callback'] = self.check
        for k, v in self.defaultStepData.items():
            self._stepData[k] = v

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.setAlignment(QtCore.Qt.AlignTop)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)

        self.outputWidget = FilePathWidget(title='Output Folder', displayText='/path/to/icon')
        self.outputWidget.setToolTip('Which directory the Icon will be exported to.')

        self.validateButton = ActionButton('Validate')
        self.validateButton.setToolTip('Check that the Icon you made is publish ready.')

        self.exportButton = ActionButton('Export')
        self.exportButton.setToolTip('Export the Icon to the set Output Folder.')

        contentLayout = QtWidgets.QVBoxLayout()
        contentLayout.addWidget(self.outputWidget)
        contentLayout.addWidget(self.validateButton)
        contentLayout.addWidget(self.exportButton)

        self.frameWidget = CollapseWidget(title='Validate And Export', stepData=self._stepData.serialized, parent=parent)
        self.frameWidget.setContentLayout(contentLayout)
        self.frameWidget.expand()
        main_layout.addWidget(self.frameWidget)

        self.outputWidget.filePathChanged.connect(self.saveOutputPath)
        self.validateButton.clicked.connect(self.validate)
        self.exportButton.clicked.connect(self.export)

    def showEvent(self, event):
        self.loadData()
        self._stepData.checkStepStatus.emit()
        super(IconFinalizeWidget, self).showEvent(event)

    @property
    def stepData(self):
        return self._stepData

    def saveOutputPath(self, text):
        core.saveOutputPath(text)
        self._stepData.checkStepStatus.emit()
        self.statusChecked.emit()

    def loadData(self):
        settingsData = core.getIconSettings()
        if 'outputPath' in settingsData:
            self.outputWidget.filePath = settingsData['outputPath']

    def updateProgress(self, checked):
        self.frameWidget.completed.emit(checked)
        self.statusChecked.emit()

    def check(self):
        hasOutputPath = False
        rootPathExists = False

        if self.outputWidget.filePath:
            hasOutputPath = True

        if os.path.exists(os.path.dirname(self.outputWidget.filePath)):
            rootPathExists = True

        return all([x for x in [hasOutputPath, rootPathExists, self._validated]])

    def validate(self):
        LOG.info('Start Icon validation.')

        result = core.buildIcon(validate=True, cleanup=True)
        self._validated = result
        
        self._stepData.checkStepStatus.emit()

        settingsData = core.getIconSettings()

        if not result:
            QtWidgets.QMessageBox.critical(self, '', 'Icon Validation Failed\nCheck the script editor for details.')
            LOG.info('Icon failed validation - {0}'.format(settingsData['outputPath']))
            return
        
        LOG.info('Icon passed validation - {0}'.format(settingsData['outputPath']))
        QtWidgets.QMessageBox.information(self, '', 'Icon Validation Passed\nThe Icon is ready for submission!')

    def export(self):
        if not utils.isSceneSaved():
            QtWidgets.QMessageBox.critical(self, '', 'File Not Saved\nSave your file first, and click Export again.')
            return

        LOG.info('Start Icon export.')
        result = core.buildIcon(validate=True, export=True, cleanup=False)
        self._validated = result
        
        self._stepData.checkStepStatus.emit()

        if not result:
            settingsData = core.getIconSettings()
            LOG.info('Icon failed to export - {0}'.format(settingsData['outputPath']))
            QtWidgets.QMessageBox.critical(self, '', 'Export Failed\nSomething went wrong!')
            return

        zipFile = core.createIconZip()
        LOG.info('Icon export Completed: %s', zipFile)
        QtWidgets.QMessageBox.information(self, '', 'Icon Export Completed\n{0}'.format(zipFile))

class CollapseWidget(QtWidgets.QWidget):
    completed = QtCore.Signal(bool)

    def __init__(self, title, stepData, parent=None):
        super(CollapseWidget, self).__init__(parent=parent)

        self._stepData = stepData
        self.stepStatusWidget = IconStatusStepWidget(stepData)

        self.toggleButton = QtWidgets.QToolButton(
            text=title, checkable=True, checked=False
        )
        self.toggleButton.setStyleSheet("QToolButton { border: none; }")
        self.toggleButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggleButton.setArrowType(QtCore.Qt.RightArrow)
        self.toggleButton.setChecked(False)
        self.toggleButton.released.connect(self.onReleased)

        self.contentArea = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.contentArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.contentArea.setWidgetResizable(True)
        self.contentArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.contentArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.contentArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.contentArea.setFrameShape(QtWidgets.QFrame.Box)

        headerLayout = QtWidgets.QHBoxLayout()
        headerLayout.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        headerLayout.setSpacing(0)
        headerLayout.setContentsMargins(0, 0, 0, 0)
        headerLayout.addWidget(self.stepStatusWidget)
        headerLayout.addWidget(self.toggleButton)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(headerLayout)
        lay.addWidget(self.contentArea)

        self.completed.connect(self.stepStatusWidget.setStatus)

    def expand(self):
        self.toggleButton.setChecked(True)
        self.onReleased()

    def collapse(self):
        self.toggleButton.setChecked(False)
        self.onReleased()

    def onReleased(self):
        checked = self.toggleButton.isChecked()

        if not checked:
            self.toggleButton.setArrowType(QtCore.Qt.RightArrow)
            self.contentArea.setMaximumHeight(self.collapsedHeight)
            self.setMaximumHeight(self.collapsedHeight)
            self.contentArea.setFrameShape(QtWidgets.QFrame.NoFrame)
            self.contentArea.hide()
        else:
            self.toggleButton.setArrowType(QtCore.Qt.DownArrow)
            self.contentArea.setMaximumHeight(self.contentHeight + self.collapsedHeight)
            self.setMaximumHeight(self.contentHeight + self.collapsedHeight)
            self.contentArea.setFrameShape(QtWidgets.QFrame.Box)
            self.contentArea.show()

    @property
    def collapsedHeight(self):
        return self._collapsedHeight

    @collapsedHeight.setter
    def collapsedHeight(self, value):
        self._collapsedHeight = value

    @property
    def contentHeight(self):
        return self._contentHeight

    @contentHeight.setter
    def contentHeight(self, value):
        self._contentHeight = value

    def setContentLayout(self, layout):
        oldWidget = self.contentArea.widget()
        if  oldWidget is not None:
            oldWidget.deleteLater()

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.contentArea.setWidget(widget)

        self.collapsedHeight = self.sizeHint().height() - self.contentArea.maximumHeight()
        self.contentHeight = layout.sizeHint().height()


class IconStatusStepWidget(QtWidgets.QWidget):
    def __init__(self, stepData, parent=None):
        super(IconStatusStepWidget, self).__init__(parent=parent)

        self.setToolTip(stepData.get('message', ''))

        self._required = stepData.get('required', False)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignLeft)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.icon = QtWidgets.QLabel('')
        self.setStatus(stepData.get('status', False))
        layout.addWidget(self.icon)

    def setStatus(self, status):
        if self._required:
            if status:
                self.setStatusComplete()
            else:
                self.setStatusIncomplete()
        else:
            if status:
                self.setStatusComplete()
            else:
                self.setStatusOk()

    def setStatusComplete(self):
        iconPath = utils.mergePaths(os.path.dirname(__file__), 'resources', 'statusCompleted_icon.png')
        pixmap = QtGui.QPixmap(iconPath)
        pixmap = pixmap.scaled(16, 16, QtCore.Qt.KeepAspectRatio)
        self.icon.setPixmap(pixmap)

    def setStatusIncomplete(self):
        iconPath = utils.mergePaths(os.path.dirname(__file__), 'resources', 'statusIncompleted_icon.png')
        pixmap = QtGui.QPixmap(iconPath)
        pixmap = pixmap.scaled(16, 16, QtCore.Qt.KeepAspectRatio)
        self.icon.setPixmap(pixmap)

    def setStatusOk(self):
        iconPath = utils.mergePaths(os.path.dirname(__file__), 'resources', 'statusOk_icon.png')
        pixmap = QtGui.QPixmap(iconPath)
        pixmap = pixmap.scaled(16, 16, QtCore.Qt.KeepAspectRatio)
        self.icon.setPixmap(pixmap)


class ActionButton(QtWidgets.QPushButton):
    def __init__(self, title, parent=None):
        super(ActionButton, self).__init__(title, parent=parent)

        self.setMinimumHeight(24)
        self.setMaximumHeight(24)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    def sizeHint(self):
        return QtCore.QSize(24, 24)