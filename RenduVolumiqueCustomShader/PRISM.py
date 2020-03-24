import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy,math, time
import json
import imp
import shutil

from Resources.CustomShader import CustomShader

#
# PRISM
#

class PRISM(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "PRISM"
    self.parent.categories = ["Projet"]
    self.parent.dependencies = []
    self.parent.contributors = ["Simon Drouin"]
    self.parent.helpText = """A scripted module to edit custom volume rendering shaders."""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText =""" This file was developped by Simon Drouin at Ecole de Technologie Superieure (Montreal, Canada)"""
#
# PRISMWidget
#

class PRISMWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.logic = PRISMLogic()

    # Instantiate and connect widgets ...

    #
    # Data Area
    #
    dataCollapsibleButton = ctk.ctkCollapsibleButton()
    dataCollapsibleButton.text = "Data"
    self.layout.addWidget(dataCollapsibleButton)

    # Layout within the data collapsible button
    dataFormLayout = qt.QFormLayout(dataCollapsibleButton)

    # Head image volume selector
    self.imageSelector = slicer.qMRMLNodeComboBox()
    self.imageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.imageSelector.selectNodeUponCreation = True
    self.imageSelector.addEnabled = False
    self.imageSelector.removeEnabled = False
    self.imageSelector.noneEnabled = False
    self.imageSelector.showHidden = False
    self.imageSelector.showChildNodeTypes = False
    self.imageSelector.setMRMLScene( slicer.mrmlScene )
    self.imageSelector.setToolTip( "Select the reference head image volume" )
    self.imageSelector.connect("nodeAdded(vtkMRMLNode*)", self.onImageSelectorNodeAdded)
    dataFormLayout.addRow("Image Volume : ", self.imageSelector)

    # For aesthetics
    self.layout.addSpacing(20)

    #
    # View Setup Area
    #
    viewSetupCollapsibleButton = ctk.ctkCollapsibleButton()
    viewSetupCollapsibleButton.text = "View Setup"
    self.layout.addWidget(viewSetupCollapsibleButton)

    # Layout within the view setup collapsible button
    viewSetupLayout = qt.QVBoxLayout(viewSetupCollapsibleButton)

    # Checkbox to activate volume rendering
    self.volumeRenderingCheckBox = qt.QCheckBox()
    self.volumeRenderingCheckBox.toggled.connect(self.onVolumeRenderingCheckBoxToggled)
    self.volumeRenderingCheckBox.text = "Volume Rendering"    

    viewSetupLayout.addWidget(self.volumeRenderingCheckBox)

    #
    # Custom Shader Area
    #
    self.customShaderCollapsibleButton = ctk.ctkCollapsibleButton()
    self.customShaderCollapsibleButton.text = "Custom Shader"
    self.layout.addWidget(self.customShaderCollapsibleButton)



    # Create a layout that will be populated with the parameters of the
    # active custom shader
    self.customShaderParametersLayout = qt.QFormLayout(self.customShaderCollapsibleButton)

    # Custom shader combobox to select a type of custom shader
    self.customShaderCombo = qt.QComboBox()
    # Populate combobox with every types of shader available
    allShaderTypes = CustomShader.GetAllShaderClassNames()
    for shaderType in allShaderTypes:
      self.customShaderCombo.addItem(shaderType)
    self.customShaderCombo.setCurrentIndex(len(allShaderTypes)-1)
    self.customShaderCombo.currentIndexChanged.connect(self.onCustomShaderComboIndexChanged)
    self.customShaderParametersLayout.addRow("Choose Custom Shader: ", self.customShaderCombo)
    self.customShaderCollapsibleButton.hide()


    #
    # Creation of new Custom Shader Area
    #
    self.newCustomShaderCollapsibleButton = ctk.ctkCollapsibleButton()
    self.newCustomShaderCollapsibleButton.text = "Create new Custom Shader"
    self.layout.addWidget(self.newCustomShaderCollapsibleButton)

    self.newCustomShaderNameInput = qt.QLineEdit()
    self.newCustomShaderNameInput.setPlaceholderText("Class name")
    self.newCustomShaderNameInput.textChanged.connect(self.onSelect)
    self.newCustomShaderNameInput.setToolTip("Name of the class that will be created." )
    
    self.error_msg = qt.QLabel()
    self.error_msg.hide()
    self.error_msg.setStyleSheet("color: red")

    self.newCustomShaderDisplayInput = qt.QLineEdit()
    self.newCustomShaderDisplayInput.setPlaceholderText("Display name")
    self.newCustomShaderDisplayInput.textChanged.connect(self.onSelect)
    self.newCustomShaderDisplayInput.setToolTip("Name of the shader that will be displayed in the combo box." )

    self.createCustomShaderButton = qt.QPushButton("Create")
    self.createCustomShaderButton.setToolTip("Creates a new custom shader class." )
    self.createCustomShaderButton.clicked.connect(self.onNewCustomShaderButtonClick)
    self.createCustomShaderButton.enabled = False

    self.editSourceButton = qt.QPushButton("Edit")
    self.editSourceButton.toolTip = "Edit the new custom shader source code."
    self.editSourceButton.connect('clicked()', self.onEditSource)
    self.editSourceButton.hide()
    
    newCustomShaderlayout = qt.QVBoxLayout(self.newCustomShaderCollapsibleButton)
    newCustomShaderlayout.addWidget(self.newCustomShaderNameInput)
    newCustomShaderlayout.addWidget(self.error_msg)
    newCustomShaderlayout.addWidget(self.newCustomShaderDisplayInput)
    newCustomShaderlayout.addWidget(self.createCustomShaderButton)
    newCustomShaderlayout.addWidget(self.editSourceButton)
    newCustomShaderlayout.addSpacing(50)




    """
    # 
    # VR Actions Area
    #
    self.vrhelperActionsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.vrhelperActionsCollapsibleButton.text = "VR Actions"
    self.layout.addWidget(self.vrhelperActionsCollapsibleButton)

    VRActionsVBoxLayout = qt.QVBoxLayout(self.vrhelperActionsCollapsibleButton)

    # Activate VR
    self.setVRActiveButton = qt.QPushButton("Set VR Active")
    self.setVRActiveButton.setToolTip( "Set virtual reality Active." )
    self.setVRActiveButton.clicked.connect(self.logic.activateVR)
    VRActionsVBoxLayout.addWidget(self.setVRActiveButton)

    # Checkbox to display controls in VR
    self.displayControlsCheckBox = qt.QCheckBox()
    self.displayControlsCheckBox.toggled.connect(self.onDisplayControlsCheckBoxToggled)
    self.displayControlsCheckBox.text = "Display VR controls"
    VRActionsVBoxLayout.addWidget(self.displayControlsCheckBox)
    """
    # Add vertical spacer
    self.layout.addStretch(1)

    # Initialize state
    self.onSelect()
    self.initState()

  def onEditSource(self):
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+self.newCustomShaderFile, qt.QUrl.TolerantMode))

  def onSelect(self):
    self.createCustomShaderButton.enabled = len(self.newCustomShaderNameInput.text) > 0 and len(self.newCustomShaderDisplayInput.text) > 0
    self.error_msg.hide()

  def duplicate_file(self, old_file_name, new_file_name):
    """create a new class from the template
    """

    file_path = os.path.realpath(__file__)
    file_dir, filename = os.path.split(file_path)
    file_dir = file_dir + "\\Resources\\Shaders\\"
    
    src_file = os.path.join(file_dir, old_file_name)
    dst_file = os.path.join(file_dir, new_file_name + ".py")
    
    #check if file already exists
    if (os.path.exists(dst_file)):
      self.error_msg.text = "The class \""+new_file_name+"\" exists already. Please check the name and try again."
      self.error_msg.show()
      self.createCustomShaderButton.enabled = False
      return False
    else:
      self.createCustomShaderButton.enabled = True

    if (shutil.copy(src_file, dst_file)) :
      return dst_file
    else :
      self.error_msg.text = "There is an error with the class name \""+new_file_name+"\". Please check the name and try again."
      self.error_msg.show()

  def setup_file(self, file_, className, displayName):
    """modifies the new class with regex to match the given infos
    """
    import os, sys
    import re

    classFile = open(file_, 'rt')
    data = classFile.read()
    dataClassName = re.sub(r'\bTemplate\b', className, data)
    classFile.close()

    classFile = open(file_, 'wt')
    classFile.write(dataClassName)
    classFile.close()

    classFile = open(file_, 'rt')
    data = classFile.read()
    dataDisplayName = re.sub(r'\bTemplateName\b', displayName, data)
    classFile.close()

    classFile = open(file_, 'wt')
    classFile.write(dataDisplayName)
    classFile.close()

  def onNewCustomShaderButtonClick(self):
    """creates a new file with the associated class
    """
    self.error_msg.hide()
    className = self.newCustomShaderNameInput.text
    displayName = self.newCustomShaderDisplayInput.text
    self.newCustomShaderFile = self.duplicate_file("Template", className)
    if(self.newCustomShaderFile):
      self.setup_file(self.newCustomShaderFile, className, displayName)
      self.editSourceButton.show()
      CustomShader.GetAllShaderClassNames()
      self.customShaderCombo.addItem(displayName)


  def initState(self):
    """ Function call to initialize the all user interface based on current scene.
    """
    # initilaize the view

    # init shader
    if self.volumeRenderingCheckBox.isChecked() and self.imageSelector.currentNode():
      self.logic.renderVolume(self.imageSelector.currentNode())
      self.imageSelector.currentNodeChanged.connect(self.onImageSelectorChanged)
      self.imageSelector.nodeAdded.disconnect()
      self.UpdateShaderParametersUI()    

  #
  # Data callbacks
  #

  def onImageSelectorNodeAdded(self, calldata):
    """ Callback function when a volume node is added to the scene by the user.

    Args:
        calldata (vtkMRMLVolumeNode): Volume node added (about to be added) to the scene.
    """
    node = calldata
    if isinstance(node, slicer.vtkMRMLVolumeNode):
      # Call showVolumeRendering using a timer instead of calling it directly
      # to allow the volume loading to fully complete.
      if self.volumeRenderingCheckBox.isChecked():
        qt.QTimer.singleShot(0, lambda: self.logic.renderVolume(node))
        self.UpdateShaderParametersUI()
      self.imageSelector.currentNodeChanged.connect(self.onImageSelectorChanged)
      self.imageSelector.nodeAdded.disconnect()

  def onImageSelectorChanged(self, node):
    """ Callback function when the volume node has been changed in the dedicated combobox.
        Setup slice nodes to display selected node and render it in the 3d view.
    """
    if not node:
      return

    # render selected volume
    if self.volumeRenderingCheckBox.isChecked():
      self.logic.renderVolume(self.imageSelector.currentNode())
      self.UpdateShaderParametersUI()

  #
  # View setup callbacks
  #

  def onVolumeRenderingCheckBoxToggled(self)      :
    """ Callback function when the volume rendering check box is toggled. Activate or deactivate 
    the rendering of the selected volume.
    """
    if self.volumeRenderingCheckBox.isChecked():
      if self.imageSelector.currentNode():
        self.logic.renderVolume(self.imageSelector.currentNode())
        self.UpdateShaderParametersUI()
        self.customShaderCollapsibleButton.show()
    else:
      if self.logic.volumeRenderingDisplayNode:
        self.logic.volumeRenderingDisplayNode.SetVisibility(False)
      self.customShaderCollapsibleButton.hide()

  def onDisplayControlsCheckBoxToggled(self):
    """ Callback function triggered when the display controls check box is toggled.
        Show/hide in the VR view scene the controls at the location of the Windows Mixed Reality controllers.
    """
    if self.displayControlsCheckBox.isChecked():
      self.logic.vrhelper.showVRControls()
    else:
      self.logic.hideVRControls()

  #
  # Volume rendering callbacks
  #

  def onCustomShaderComboIndexChanged(self,i):
    self.logic.setCustomShaderType(self.customShaderCombo.currentText)
    self.logic.customShader.setPathEnds( self.logic.getEntry(), self.logic.getTarget() )
    self.UpdateShaderParametersUI()

  def UpdateShaderParametersUI(self):
    if not self.logic.customShader:
      return
    
    # Clear all the widgets except the combobox selector
    while self.customShaderParametersLayout.count() != 2:
      item = self.customShaderParametersLayout.takeAt(self.customShaderParametersLayout.count() - 1)
      if item != None:
        widget = item.widget()
        if widget != None:
          widget.setParent(None)

    # Instanciate a slider for each parameter of the active shader
    params = self.logic.customShader.shaderParams
    paramNames = params.keys()
    for p in paramNames:
      label = qt.QLabel(params[p]['displayName'])
      label.setMinimumWidth(80)
      slider = ctk.ctkSliderWidget()
      slider.minimum = params[p]['min']
      slider.maximum = params[p]['max']
      slider.singleStep = ( (slider.maximum - slider.minimum) * 0.01 )
      slider.setObjectName(p)
      slider.setValue(self.logic.customShader.getShaderParameter(p))
      slider.valueChanged.connect( lambda value, p=p : self.onCustomShaderParamChanged(value,p) )
      self.customShaderParametersLayout.addRow(label,slider)

  def onCustomShaderParamChanged(self, value, paramName ):
    self.logic.customShader.setShaderParameter(paramName,value)
  
  def onReload(self):

    logging.debug("Reloading CustomShader")
    packageName='Resources'
    submoduleName = 'CustomShader'
    f, filename, description = imp.find_module(packageName)
    package = imp.load_module(packageName, f, filename, description)
    f, filename, description = imp.find_module(submoduleName, package.__path__)
    try:
      imp.load_module(packageName+'.'+submoduleName, f, filename, description)
    finally:
      f.close()
    
    logging.debug("Reloading PRISM")
    packageName='PRISM'
    f, filename, description = imp.find_module(packageName)
    try:
      imp.load_module(packageName, f, filename, description)
    finally:
      f.close()

    ScriptedLoadableModuleWidget.onReload(self)

#
# PRISMLogic
#

class PRISMLogic(ScriptedLoadableModuleLogic):
  
  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    # init path model 3d models
    self.points = vtk.vtkPoints()
    self.points.SetNumberOfPoints(2)
    self.pathModel = None
    self.tubeFilter = None
    self.sphereSource = None
    self.pathRadius = 2.5

    self.createEndPoints()


    # VR interaction parameters
    self.movingEntry = False
    self.moveRelativePosition = False

    # init volume rendering active node
    self.volumeRenderingDisplayNode = None

    # hide volume rendering display node possibly loaded with the scene
    renderingDisplayNodes = slicer.util.getNodesByClass("vtkMRMLVolumeRenderingDisplayNode")
    for displayNode in renderingDisplayNodes:
      displayNode.SetVisibility(False)
    renderingDisplayNodes = None

    # By default, no special shader is applied
    self.customShaderType = 'None'
    self.customShader = None
  
  #
  # End points functions
  #

  def createEndPoints(self):
    # retrieve end points in the scene or create the node
    allEndPoints = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsFiducialNode','EndPoints')
    if allEndPoints.GetNumberOfItems() > 0:
      # set node used before reload in the current instance
      self.endPoints = allEndPoints.GetItemAsObject(0)
      # self.endPoints.HideFromEditorsOn()
      self.endPoints.SetAttribute('hide', 'yes')
      # do the same for the path between end points
      allPaths = slicer.mrmlScene.GetNodesByClassByName("vtkMRMLModelNode", "Insertion Path")
      if allPaths.GetNumberOfItems() > 0:
        self.pathModel = allPaths.GetItemAsObject(0)
      self.updatePathModel()
    else:
      self.endPoints = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
      self.endPoints.SetName("EndPoints")
      # self.endPoints.HideFromEditorsOn()
      self.endPoints.SetAttribute('hide', 'yes')
      self.endPoints.GetMarkupsDisplayNode().SetColor(0,1,1)
    allEndPoints = None
    allPaths = None      
 
  
  
  def getEntry(self):
    """ Get Entry point position. If not yet placed, return (0,0,0).

    Returns:
        array[double]: Entry markups position if placed, empty array if not.
    """
    entry = [0, 0, 0]
    if self.endPoints.GetNumberOfControlPoints() >= 2:
      self.endPoints.GetNthFiducialPosition(1, entry)
    return entry
  
  def setEntry(self,entry):
    self.endPoints.SetNthFiducialPositionFromArray(1, entry)

  def getTarget(self):
    """ Get Target point position. If not yet placed, return (0,0,0).

    Returns:
        array[double]: Entry markups position if placed, empty array if not.
    """
    target = [0, 0, 0]
    if self.endPoints.GetNumberOfControlPoints() >= 1:
      self.endPoints.GetNthFiducialPosition(0, target)
    return target

  def setTarget(self,target):
    self.endPoints.SetNthFiducialPositionFromArray(0, target)   

  def updatePathModel(self, updateTransform = True):
    """ Update 3D Segment from Entry and Target markups positions.
    """
    if not self.endPoints.GetNumberOfControlPoints() == 2:
      if not self.pathModel == None:
        self.points = vtk.vtkPoints()
        self.points.SetNumberOfPoints(2)
        slicer.mrmlScene.RemoveNode(self.pathModel)
        self.pathModel = None
      return
    target = [0,0,0]
    entry = [0,0,0]
    self.endPoints.GetNthFiducialPosition(0, target)
    self.endPoints.GetNthFiducialPosition(1, entry)
    self.points.SetPoint(0, target)
    self.points.SetPoint(1, entry)
    self.points.Modified()

    if self.pathModel == None:
      self.createPathModel()
    if updateTransform:
      self.updatePathTransform(target, entry)

  #
  # VR Related functions
  #


  def activateVR(self):
    from Resources.VirtualRealityHelper import VirtualRealityHelper
    self.vrhelper = VirtualRealityHelper(self.volumeRenderingDisplayNode)
    self.vrhelper.vr.viewWidget().RightControllerTriggerPressed.connect(self.onRightControllerTriggerPressed)
    self.vrhelper.vr.viewWidget().RightControllerTriggerReleased.connect(self.onRightControllerTriggerReleased)
    self.vrhelper.vr.viewWidget().LeftControllerTriggerPressed.connect(self.onLeftControllerTriggerPressed)
    self.vrhelper.vr.viewWidget().LeftControllerTriggerReleased.connect(self.onLeftControllerTriggerReleased)

    qt.QTimer.singleShot(0, lambda: self.delayedInitVRObserver())  


  def delayedInitVRObserver(self):
    ltn = self.vrhelper.getLeftTransformNode()
    self.leftTransformModifiedTag = ltn.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent,self.onLeftControllerMoved)
    rtn = self.vrhelper.getRightTransformNode()
    self.rightTransformModifiedTag = rtn.AddObserver(slicer.vtkMRMLTransformNode.TransformModifiedEvent,self.onRightControllerMoved)


  def onRightControllerTriggerPressed(self):
    """ Callback function on trigger pressed event. If controller is near the entry point, starts modification of its position.
    """
    if not self.getNumberOfPoints(self.endPoints) == 2:
      return
    controllerPos = self.vrhelper.getRightControllerPosition()
    entryPos = self.getEntry()
    diff = numpy.subtract(entryPos,controllerPos)
    dist = numpy.linalg.norm(diff)
    # Check distance from controller to entry point
    if dist < 30.0:
      # When created in Slicer, markups are selected. To change the color of the point selected by the VR controller,
      # we need to unselect the point and change the unselected color to fit Slicer color code. This can be miss leading
      # for developpers. The other approach would be missleading for Slicer users expecting markups to be red when inactive
      # and green when modified.
      self.endPoints.SetNthControlPointSelected(1, False)
      # store previous position for motion tracking
      self.vrhelper.lastControllerPos = controllerPos
      self.movingEntry = True
      self.endPoints.GetMarkupsDisplayNode().SetColor(0,1,0) # Unselected color
    elif not self.endPoints.GetNthControlPointSelected(1):
      self.endPoints.SetNthControlPointSelected(1, True)

  def onRightControllerTriggerReleased(self):
    """ Callback function when right trigger is released. Drop entry point at current controller position.
    """
    if self.movingEntry:
      # Unselect point to restore default red color. Check comment above.
      self.endPoints.SetNthControlPointSelected(1, True)
      self.endPoints.GetMarkupsDisplayNode().SetColor(0,1,1)
      self.movingEntry = False

  def onRightControllerMoved(self,caller,event):
    """ Callback function when a the right controller position has changed.
    """
    if self.vrhelper.rightControlsDisplayMarkups.GetDisplayNode().GetVisibility():
      self.vrhelper.setControlsMarkupsPositions("Right")
    if not self.getNumberOfPoints(self.endPoints) == 2:
      return
    controllerPos = self.vrhelper.getRightControllerPosition()
    diff = numpy.subtract(controllerPos,self.vrhelper.lastControllerPos)
    entryPos = self.getEntry()
    newEntryPos = numpy.add(entryPos,diff)
    dist = numpy.linalg.norm(numpy.subtract(entryPos,controllerPos))
    # If controller is near, unselected the markup the change color
    if dist < 30.0:
      self.endPoints.SetNthControlPointSelected(1, False)
    elif not self.movingEntry:
      self.endPoints.SetNthControlPointSelected(1, True)
    # Check if entry point is currently being modified by user
    if self.movingEntry:
      # Set entry point at current controller position
      self.setEntry(newEntryPos)
      # As markup position changed, update path model
      self.updatePathModel()
    self.vrhelper.lastControllerPos = controllerPos

  def onLeftControllerTriggerPressed(self):
    """ Callback function on trigger pressed event. If a shader with "relativePosition" parameter has been selected
        allows user to change this parameter based on future position compared to the position when pressed.
    """
    if not self.customShader:
      return
    if self.customShader.hasShaderParameter('relativePosition'):
      # Set init position to be compared with future positions
      self.leftInitPos = self.getLeftControllerPosition()
      self.leftInitRatio = self.customShader.getShaderParameter("relativePosition")
      self.moveRelativePosition = True

  def onLeftControllerTriggerReleased(self):
    """ Callback function on trigger released event. Stop changing the relativePosition shader parameter.
    """
    self.moveRelativePosition = False

  def onLeftControllerMoved(self,caller,event):
    """ Callback function when a the left controller position has changed. Used to change "relativePosition"
        current shader parameter and laser position.
    """
    # Check if the trigger is currently being pressed
    if self.moveRelativePosition:
      # Compute distance between entry and target, then normalize
      entry = self.getEntry()
      target = self.getTarget()
      diff = numpy.subtract(target, entry)
      range = numpy.linalg.norm(diff)
      dir = diff / range
      # Compute current position compared to the position when the trigger has been pressed
      curPos = self.getLeftControllerPosition()
      motion = numpy.subtract(curPos,self.leftInitPos)
      offsetRatio = numpy.dot( motion, dir )/range
      # Change relative position based on the position
      newRatio = numpy.clip(self.leftInitRatio + offsetRatio,0.0,1.0)
      self.customShader.setShaderParameter("relativePosition",newRatio)
    self.vrhelper.updateLaserPosition()
    if self.vrhelper.rightControlsDisplayMarkups.GetDisplayNode().GetVisibility():
      self.vrhelper.setControlsMarkupsPositions("Left")           

  #
  # Volume Rendering functions
  #

  def renderVolume(self, volumeNode):
    """ Use Slicer Volume Rendering module to initialize and setup rendering of the given volume node.
    Args:
        volumeNode (vtkMRMLVolumeNode): Volume node to be rendered.
    """
    logic = slicer.modules.volumerendering.logic()

    # Set custom shader to renderer
    self.setupCustomShader()

    # Turn off previous rendering
    if self.volumeRenderingDisplayNode:
      self.volumeRenderingDisplayNode.SetVisibility(False)

    # Check if node selected has a renderer
    displayNode = logic.GetFirstVolumeRenderingDisplayNode(volumeNode)
    if displayNode:
      self.volumeRenderingDisplayNode = displayNode
      self.volumeRenderingDisplayNode.SetVisibility(True)
      self.volumeRenderingDisplayNode.SetNodeReferenceID("shaderProperty", self.shaderPropertyNode.GetID())
      return

    # if not, create a renderer
    # Slicer default command to create renderer and add node to scene
    displayNode = logic.CreateDefaultVolumeRenderingNodes(volumeNode)
    slicer.mrmlScene.AddNode(displayNode)
    displayNode.UnRegister(logic)
    logic.UpdateDisplayNodeFromVolumeNode(displayNode, volumeNode)
    volumeNode.AddAndObserveDisplayNodeID(displayNode.GetID())

    displayNode.SetNodeReferenceID("shaderProperty", self.customShader.shaderPropertyNode.GetID())

    # Add a color preset based on volume range
    self.updateVolumeColorMapping(volumeNode, displayNode)

    # Prevent volume to be moved in VR
    volumeNode.SetSelectable(False)
    volumeNode.GetImageData()
    # Display given volume
    displayNode.SetVisibility(True)

    # Set value as class parameter to be accesed in other functions
    self.volumeRenderingDisplayNode = displayNode
 
  def setCustomShaderType(self, shaderTypeName):
    """ Set given shader type as current active shader

    Args:
        shaderTypeName (string): 'Sphere Carving', 'Opacity Peeling'. Name corresponding to the type of rendering needed.
    """
    self.customShaderType = shaderTypeName
    self.setupCustomShader()

  def setupCustomShader(self):
    """ Get or create shader property node and initialize custom shader.
    """
    shaderPropertyName = "ShaderProperty"
    # TODO: not sure we want to get any node from the scene here. It might be better to find out if one is already associated with the volume
    
    allShaderProperty = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLShaderPropertyNode',shaderPropertyName)
    if allShaderProperty.GetNumberOfItems() == 0:
      self.shaderPropertyNode = slicer.vtkMRMLShaderPropertyNode()
      self.shaderPropertyNode.SetName(shaderPropertyName)
      slicer.mrmlScene.AddNode(self.shaderPropertyNode)
    else:
      self.shaderPropertyNode = allShaderProperty.GetItemAsObject(0)
    allShaderProperty = None
    self.customShader = CustomShader.InstanciateCustomShader(self.customShaderType,self.shaderPropertyNode)
    self.customShader.setupShader()

  def updateVolumeColorMapping(self, volumeNode, displayNode, volumePropertyNode = None):
    """ Given a volume, compute a default color mapping to render volume in the given display node.
        If a volume property node is given to the function, uses it as color mapping.

    Args:
        volumeNode: (vtkMRMLVolumeNode): Volume node to be rendered.
        displayNode: (vtkMRMLVolumeRenderingDisplayNode) Default rendering display node. (CPU RayCast, GPU RayCast, Multi-Volume)
        volumePropertyNode (vtkMRMLVolumePropertyNode): Volume propery node that carries the color mapping wanted.
    """
    if not displayNode:
      return
    if volumePropertyNode:
      displayNode.GetVolumePropertyNode().Copy(volumePropertyNode)
    else:
      logic = slicer.modules.volumerendering.logic()
      # Select a color preset based on volume range
      scalarRange = volumeNode.GetImageData().GetScalarRange()
      if scalarRange[1]-scalarRange[0] < 1500:
        # small dynamic range, probably MRI
        displayNode.GetVolumePropertyNode().Copy(logic.GetPresetByName('MR-Default'))
      else:
        # larger dynamic range, probably CT
        displayNode.GetVolumePropertyNode().Copy(logic.GetPresetByName('CT-Chest-Contrast-Enhanced'))
      # Turn off shading
      displayNode.GetVolumePropertyNode().GetVolumeProperty().SetShade(False)


