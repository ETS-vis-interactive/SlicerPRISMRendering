import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np,math, time
import json
import imp
import shutil
import textwrap

from Resources.CustomShader import CustomShader

#
# PRISM
#

class PRISM(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/   Base/Python/slicer/ScriptedLoadableModule.py
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
    self.newCustomShaderCollapsibleButton.collapsed = True
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
    

    #
    # Modification of Custom Shader Area
    #

    allShaderDecTags = {
    "Binary Mask" : "//VTK::BinaryMask::Dec",
    "Compute Lighting" : "//VTK::ComputeLighting::Dec",
    "Compute Opacity"  : "//VTK::ComputeOpacity::Dec",
    "Picking" : "//VTK::Picking::Dec",
    "Termination" : "//VTK::Termination::Dec",
    "Base" : "//VTK::Base::Dec",
    "Clipping" : "//VTK::Clipping::Dec",
    "Composite Mask" : "//VTK::CompositeMask::Dec",
    "Compute Color" : "//VTK::ComputeColor::Dec",
    "Compute Gradient" : "//VTK::ComputeGradient::Dec",
    "Compute Gradient Opacity 1D" : "//VTK::ComputeGradientOpacity1D::Dec",
    "Compute Ray Direction" : "//VTK::ComputeRayDirection::Dec",
    "Cropping" : "//VTK::Cropping::Dec",
    "Depth Peeling" : "//VTK::DepthPeeling::Dec",
    "Gradient Cache" : "//VTK::GradientCache::Dec",
    "Output" : "//VTK::Output::Dec",
    "Render To Image" : "//VTK::RenderToImage::Dec",
    "Shading" : "//VTK::Shading::Dec",
    "Transfer 2D" : "//VTK::Transfer2D::Dec",
    "Custom Uniforms" : "//VTK::CustomUniforms::Dec",
    "None":"None"
    }
    
    allShaderInitTags = {
    "Clipping": "//VTK::Clipping::Init",
    "Depth Peeling": "//VTK::DepthPeeling::Ray::Init",
    "Cropping": "//VTK::Cropping::Init",
    "Depth Pass": "//VTK::DepthPass::Init",
    "Render To Image": "//VTK::RenderToImage::Init",
    "Shading": "//VTK::Shading::Init",
    "Terminate": "//VTK::Terminate::Init",
    "Base" : "//VTK::Base::Init",
    "None":"None"
    }
    
    allShaderImplTags = {
    "Composite Mask": "//VTK::CompositeMask::Impl",
    "Render To Image": "//VTK::RenderToImage::Impl",
    "Terminate": "//VTK::Terminate::Impl",
    "Binary Mask": "//VTK::BinaryMask::Impl",
    "Call Worker": "//VTK::CallWorker::Impl",
    "Cropping": "//VTK::Cropping::Impl",
    "Depth Pass": "//VTK::DepthPass::Impl",
    "Pre Compute Gradients": "//VTK::PreComputeGradients::Impl",
    "Shading": "//VTK::Shading::Impl",
    "Base": "//VTK::Base::Impl",
    "None":"None"
    }

    allShaderExitTags = {
    "Cropping" : "//VTK::Cropping::Exit",
    "Depth Pass": "//VTK::DepthPass::Exit",
    "Base": "//VTK::Base::Exit",
    "Clipping": "//VTK::Clipping::Exit",
    "Picking": "//VTK::Picking::Exit",
    "Render To Image": "//VTK::RenderToImage::Exit",
    "Terminate": "//VTK::Terminate::Exit",
    "Shading": "//VTK::Shading::Exit",
    "None":"None"
    }

    allShaderPathCheckTags = {"DepthPeeling" : "//VTK::DepthPeeling::Ray::PathCheck"}

    self.allShaderTagTypes = {
      "Declaration": allShaderDecTags,
      "Initialization": allShaderInitTags,
      "Exit": allShaderExitTags,
      "Implementation": allShaderImplTags,
      "Path Check": allShaderPathCheckTags,
      "None":"None"
    }
    
    self.modifyCustomShaderCollapsibleButton = ctk.ctkCollapsibleButton()
    self.modifyCustomShaderCollapsibleButton.text = "Modify Custom Shader"
    self.modifyCustomShaderCollapsibleButton.collapsed = True
    self.layout.addWidget(self.modifyCustomShaderCollapsibleButton)
    
    # Custom shader combobox to select a type of custom shader
    self.modifyCustomShaderComboLabel = qt.QLabel()
    self.modifyCustomShaderCombo = qt.QComboBox()
    self.updateComboBox(allShaderTypes, self.modifyCustomShaderCombo, self.modifyCustomShaderComboLabel, "Choose the custom shader to modify : ", self.onModifyCustomShaderComboIndexChanged)

    # Custom shader combobox to select a type of custom shader
    self.shaderTagsTypeComboLabel = qt.QLabel()
    self.shaderTagsTypeCombo = qt.QComboBox()
    self.updateComboBox(list(self.allShaderTagTypes.keys()), self.shaderTagsTypeCombo, self.shaderTagsTypeComboLabel, "Choose the shader tag type : ", self.onShaderTagsTypeComboIndexChanged)
    self.shaderTagsTypeComboLabel.hide()
    self.shaderTagsTypeCombo.hide()

    self.shaderTagsComboLabel = qt.QLabel()
    self.shaderTagsCombo = qt.QComboBox()
    self.shaderTagsComboLabel.hide()
    self.shaderTagsCombo.hide()

    self.shaderModificationsLabel = qt.QLabel("Write shader code : ")
    self.shaderModificationsLabel.hide()

    self.shaderModifications = qt.QPlainTextEdit()
    self.shaderModifications.textChanged.connect(self.onModify)
    self.shaderModifications.hide()

    self.shaderOpenFileLabelButton = qt.QLabel("Or open file : ")
    self.shaderOpenFileLabelButton.hide()

    self.shaderOpenFileButton = qt.QPushButton("Open")
    self.shaderOpenFileButton.toolTip = "Open the selected custom shader source code."
    self.shaderOpenFileButton.connect('clicked()', self.onOpenFile)
    self.shaderOpenFileButton.hide()

    self.modifyCustomShaderButton = qt.QPushButton("Modify")
    self.modifyCustomShaderButton.toolTip = "Modifies selected custom shader source code."
    self.modifyCustomShaderButton.connect('clicked()', self.onModifyCustomShader)

    modifyCustomShaderlayout = qt.QGridLayout(self.modifyCustomShaderCollapsibleButton)
    modifyCustomShaderlayout.addWidget(self.modifyCustomShaderComboLabel, 0, 0, 1, 1)
    modifyCustomShaderlayout.addWidget(self.modifyCustomShaderCombo, 0, 1, 1, 3)
    modifyCustomShaderlayout.addWidget(self.shaderTagsTypeComboLabel, 1, 0, 1, 1)
    modifyCustomShaderlayout.addWidget(self.shaderTagsTypeCombo, 1, 1, 1, 3)
    modifyCustomShaderlayout.addWidget(self.shaderTagsComboLabel, 2, 0, 1, 1)
    modifyCustomShaderlayout.addWidget(self.shaderTagsCombo, 2, 1, 1, 3)
    modifyCustomShaderlayout.addWidget(self.shaderModificationsLabel, 3, 0, 1, 1)
    modifyCustomShaderlayout.addWidget(self.shaderModifications, 3, 1, 3, 1)
    modifyCustomShaderlayout.addWidget(self.shaderOpenFileLabelButton, 4, 0, 1, 1)
    modifyCustomShaderlayout.addWidget(self.shaderOpenFileButton, 5, 0, 1, 1)
    modifyCustomShaderlayout.addWidget(self.modifyCustomShaderButton, 6, 0, 1, 4)

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
    self.onModify()
    self.initState()

  def onModifyCustomShader(self):
    """ Function add the new shader replacement to a file.

    """
    shaderTagType = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    shaderTag = shaderTagType.get(self.modifiedShaderTag)
    
    #get selected shader path
    modifiedShaderClass = CustomShader.GetClassName(self.modifiedShader)
    modifiedShaderModule = modifiedShaderClass.__module__
    packageName = "Resources"
    f, filename, description = imp.find_module(packageName)
    packagePath = imp.load_module(packageName, f, filename, description).__path__[0]
    modifiedShaderPath = packagePath+'\\Shaders\\'+ modifiedShaderModule
    
    #get shader code
    shaderCode = self.shaderModifications.document().toPlainText()
    
    #indent shader code
    shaderCode =  textwrap.indent(shaderCode, 3 * '\t')
    tab = "\t\t"
    shaderReplacement = (
    "replacement =  \"\"\"/*your new shader code here*/\n" +
    shaderCode + "\n" +
    tab + "\"\"\"\n"+
    tab + "self.shaderProperty.AddFragmentShaderReplacement(\""+shaderTag+"\", True, replacement, False)\n" +
    tab + "#shaderreplacement")

    #modify file
    fin = open(modifiedShaderPath, "rt")
    data = fin.read()
    data = data.replace('#shaderreplacement', shaderReplacement)
    fin.close()

    fin = open(modifiedShaderPath, "wt")
    fin.write(data)
    fin.close()
    
    #open file window
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+modifiedShaderPath, qt.QUrl.TolerantMode))


  def onOpenFile(self):
    """ Function to open a file containing the new shader replacement.

    """
    shaderTagType = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    shaderTag = shaderTagType.get(self.modifiedShaderTag)

    #get selected shader path
    modifiedShaderClass = CustomShader.GetClassName(self.modifiedShader)
    modifiedShaderModule = modifiedShaderClass.__module__
    packageName = "Resources"
    f, filename, description = imp.find_module(packageName)
    packagePath = imp.load_module(packageName, f, filename, description).__path__[0]
    modifiedShaderPath = packagePath+'\\Shaders\\'+ modifiedShaderModule

    #modify file 
    tab = "\t\t"
    shaderReplacement = (
    "replacement = \"\"\"/*write your shader code here*/ \"\"\" \n " +
    tab + "self.shaderProperty.AddFragmentShaderReplacement(\""+shaderTag+"\", True, replacement, False) \n "+
    tab + "#shaderreplacement" )

    fin = open(modifiedShaderPath, "rt")
    data = fin.read()
    data = data.replace('#shaderreplacement', shaderReplacement)
    fin.close()

    fin = open(modifiedShaderPath, "wt")
    fin.write(data)
    fin.close()
    
    #open file window
    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+modifiedShaderPath, qt.QUrl.TolerantMode))

  def updateComboBox(self, tab, comboBox, comboBoxLabel, comboBoxLabelText, func):
    """ Function to populate a combobox from an array.

    Args:
        tab (list): List to populate the combobox.
        comboBox (qt.QComboBox): ComboBox to be modified.
        comboBoxLabel (qt.QLabel): Label to be modified.
        comboBoxLabelText (str): Text to add into the label.
        func (func): Connect function when the ComboBox index is changed.
    """
    comboBox.clear()  
    for e in tab:
      comboBox.addItem(e)
    comboBox.setCurrentIndex(len(tab)-1)
    comboBox.activated.connect(func)
    comboBoxLabel.setText(comboBoxLabelText)
  
  def onModifyCustomShaderComboIndexChanged(self, value):
    """ Function to set which shader will be modified.

    Args:
        value (list): current value of the comboBox.
    """
    self.modifiedShader = self.modifyCustomShaderCombo.currentText
    self.shaderTagsTypeComboLabel.show()
    self.shaderTagsTypeCombo.show()

  def onShaderTagsTypeComboIndexChanged(self, value):
    """ Function to set which shader tag type will be added to the shader.

    Args:
        value (list): current value of the comboBox.
    """
    self.modifiedShaderTagType = self.shaderTagsTypeCombo.currentText
    self.shaderTagsComboLabel.show()
    self.shaderTagsCombo.show()
    tab = self.allShaderTagTypes.get(self.modifiedShaderTagType, "")
    self.updateComboBox(tab, self.shaderTagsCombo, self.shaderTagsComboLabel, "Choose the "+self.modifiedShaderTagType+" shader tag to modify : ", self.onShaderTagsComboIndexChanged)
 
  def onShaderTagsComboIndexChanged(self, value):
    """ Function to set which shader tag will be added to the shader.

    Args:
        value (list): current value of the comboBox.
    """
    self.modifiedShaderTag = self.shaderTagsCombo.currentText
    self.shaderModificationsLabel.show()
    self.shaderModifications.show()
    self.shaderOpenFileLabelButton.show()
    self.shaderOpenFileButton.show()

  def onNewCustomShaderButtonClick(self):
    """ Function to create a new file with the associated class.

    """
    self.error_msg.hide()
    self.className = self.newCustomShaderNameInput.text
    displayName = self.newCustomShaderDisplayInput.text
    self.newCustomShaderFile = self.duplicate_file("Template", self.className)
    if(self.newCustomShaderFile):
      self.setup_file(self.newCustomShaderFile, self.className, displayName)
      self.editSourceButton.show()
      CustomShader.GetAllShaderClassNames()
      self.customShaderCombo.addItem(displayName)

  def onEditSource(self):
    """ Function to create a new file with the custom shader and open the file in editor

    """
    new_file_name = self.className
    file_path = os.path.realpath(__file__)
    file_dir, filename = os.path.split(file_path)
    file_dir = file_dir + "\\Resources\\Shaders\\"
    dst_file = os.path.join(file_dir, new_file_name + ".py")

    qt.QDesktopServices.openUrl(qt.QUrl("file:///"+self.newCustomShaderFile, qt.QUrl.TolerantMode))

  def onModify(self):
    """ Function to activate or deactivate the button to modify a custom shader

    """
    self.modifyCustomShaderButton.enabled = len(self.shaderModifications.document().toPlainText()) > 0

  def onSelect(self):
    """ Function to activate or deactivate the button to create a custom shader

    """
    self.createCustomShaderButton.enabled = len(self.newCustomShaderNameInput.text) > 0 and len(self.newCustomShaderDisplayInput.text) > 0
    self.error_msg.hide()

  def duplicate_file(self, old_file_name, new_file_name):
    """ Function to create a new class from the template

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
    """ Function to modify the new class with regex to match the given infos

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


  def initState(self):
    """ Function call to initialize the all user interface based on current scene.
    """
  
    # init shader
    if self.volumeRenderingCheckBox.isChecked() and self.imageSelector.currentNode():
      self.logic.renderVolume(self.imageSelector.currentNode())
      self.imageSelector.currentNodeChanged.connect(self.onImageSelectorChanged)
      self.imageSelector.nodeAdded.disconnect()
      self.UpdateShaderParametersUI()    

      #TODO remove
      parent = slicer.util.findChildren(text='Data Probe')[0]
      i = 0
      for child in parent.children():
        if (i==1):
          child.hide()
        i+=1
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

  def onCustomShaderComboIndexChanged(self, i):
    """ Callback function when the custom shader combo box is changed.

    Args:
    i (int) : index of the element
    """
    self.logic.setCustomShaderType(self.customShaderCombo.currentText)
    self.UpdateShaderParametersUI()

  def UpdateShaderParametersUI(self):
    """ Updates the shader parameters on the UI.

    """
    if not self.logic.customShader:
      return
    
    # Clear all the widgets except the combobox selector
    while self.customShaderParametersLayout.count() != 2:
      item = self.customShaderParametersLayout.takeAt(self.customShaderParametersLayout.count() - 1)
      if item != None:
        widget = item.widget()
        if widget != None:
          widget.setParent(None)

    # Instanciate a slider for each floating parameter of the active shader
    params = self.logic.customShader.shaderfParams
    paramNames = params.keys()
    for p in paramNames:
      label = qt.QLabel(params[p]['displayName'])
      label.setMinimumWidth(80)
      slider = ctk.ctkSliderWidget()
      slider.minimum = params[p]['min']
      slider.maximum = params[p]['max']
      slider.singleStep = ( (slider.maximum - slider.minimum) * 0.01 )
      slider.setObjectName(p)
      slider.setValue(self.logic.customShader.getShaderParameter(p, float))
      slider.valueChanged.connect( lambda value, p=p : self.logic.onCustomShaderParamChanged(value, p, float) )
      self.customShaderParametersLayout.addRow(label,slider)

    # Instanciate a slider for each integer parameter of the active shader
    params = self.logic.customShader.shaderiParams
    paramNames = params.keys()
    for p in paramNames:
      label = qt.QLabel(params[p]['displayName'])
      label.setMinimumWidth(80)
      slider = ctk.ctkSliderWidget()
      slider.minimum = params[p]['min']
      slider.maximum = params[p]['max']
      slider.singleStep = ( (slider.maximum - slider.minimum) * 0.05)
      slider.setObjectName(p)
      slider.setDecimals(0)
      slider.setValue(int(self.logic.customShader.getShaderParameter(p, int)))
      slider.valueChanged.connect( lambda value, p=p : self.logic.onCustomShaderParamChanged(value, p, int) )
      self.customShaderParametersLayout.addRow(label,slider)

    # Instanciate a markup
    params = self.logic.customShader.shader4fParams
    paramNames = params.keys()
    for p in paramNames:
      targetPointButton = qt.QPushButton("Initialize " + params[p]['displayName'])
      targetPointButton.setToolTip( "Place a markup" )
      targetPointButton.clicked.connect(lambda _, name = p, btn = targetPointButton : self.logic.setPlacingMarkups(paramName = name, btn = btn,  interaction = 1))
      targetPointButton.setCheckable(True)
      targetPointButton.clicked.connect(lambda _, b = targetPointButton : self.btnstate(btn = b))
      self.customShaderParametersLayout.addRow(qt.QLabel(params[p]['displayName']), targetPointButton)

  def btnstate(self, btn):
    """ Check if the button is down.
    Args:
        btn (qt.QPushButton): Button that is activated
    """
    if btn.isChecked():
      self.logic.markupButtonisChecked = True
      btn.setChecked(False)
    else:
      self.logic.markupButtonisChecked = False

  def onReload(self):
    """ Reload the modules
    """
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

    #TODO remove
    parent = slicer.util.findChildren(text='Data Probe')[0]
    i = 0
    for child in parent.children():
      if (i==1):
        child.hide()
      i+=1

    ScriptedLoadableModuleWidget.onReload(self)

##################################################################################
# PRISMLogic
##################################################################################

class PRISMLogic(ScriptedLoadableModuleLogic):
  
  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
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
    
    self.MarkupIndexes = {}
    self.CurrentMarkupBtn = None
    self.CurrentMarkupName = "None"
    self.markupButtonisChecked = False

    self.addObservers()
    # Observer scene if view node has been added
    #self.endPoint.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointAddedEvent, self.onEndPointAdded)
  
  def addObservers(self):
    """ Create all observers needed in the UI to ensure a correct behaviour
    """
    self.pointModifiedEventTag = self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.onEndPointsChanged)
    self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.onEndPointAdded)
    #slicer.mrmlScene.AddObserver(slicer.mrmlScene.EndCloseEvent, self.onCloseScene)  

  #
  # End points functions
  #

  @vtk.calldata_type(vtk.VTK_INT)
  def onEndPointsChanged(self, caller, event, call_data):
    """ Callback function to get the position of the modified point
    Note: @vtk.calldata_type(vtk.VTK_OBJECT) function get calling instance as a vtkMRMLNode to be accesed in the function.

    Args:
        caller (slicer.mrmlScene): Slicer active scene.
        event (string): Flag corresponding to the triggered event.
        call_data (vtkMRMLNode): Node added to the scene.
    """

    #check if the point was added from the module and was set
    if (call_data) in self.MarkupIndexes and caller.GetNthControlPointPositionStatus(call_data) == 2 :
      world = [0, 0, 0, 0]
      caller.GetNthFiducialWorldCoordinates(call_data, world)
      self.onCustomShaderParamChanged(world, self.MarkupIndexes.get(call_data), "markup")
    
  def onEndPointAdded(self, caller, event):
    """ Callback function to get the position of the new point.
    Args:
        caller (slicer.mrmlScene): Slicer active scene.
        event (string): Flag corresponding to the triggered event.
    """
    if(self.markupButtonisChecked):
      movingMarkupIndex = caller.GetDisplayNode().GetActiveControlPoint()
      world = [0, 0, 0, 0]
      caller.GetNthFiducialWorldCoordinates(movingMarkupIndex, world)
      caller.SetNthFiducialLabel(movingMarkupIndex, self.CurrentMarkupName)
      self.onCustomShaderParamChanged(world, self.CurrentMarkupName, "markup")
      self.markupButtonisChecked = False
      self.CurrentMarkupBtn.enabled = False
      self.MarkupIndexes.update({movingMarkupIndex : self.CurrentMarkupName})

  def setPlacingMarkups(self, paramName, btn, interaction = 1, persistence = 0):
    """ Activate Slicer markups module to set one or multiple markups in the given markups fiducial list.

    Args:
        markupsFiducialNode (vtkMRMLMarkupsFiducialNode): List in which adding new markups.
        interaction (int): 0: /, 1: place, 2: view transform, 3: / ,4: Select
        persistence (int): 0: unique, 1: peristent
    """
    self.CurrentMarkupBtn = btn
    self.CurrentMarkupName = paramName
    interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
    interactionNode.SetCurrentInteractionMode(interaction)
    interactionNode.SetPlaceModePersistence(persistence)
    
  def onCustomShaderParamChanged(self, value, paramName, type_ ):
    """ Change the custom parameters in the shader.

    Args:
        value : value to be changed
        paramName (int): name of the parameter to be changed
        type_ (float or type): type of the parameter to be changed
    """
    self.customShader.setShaderParameter(paramName, value, type_)

  def createEndPoints(self):
    # retrieve end points in the scene or create the node
    allEndPoints = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsFiducialNode','EndPoints')
    if allEndPoints.GetNumberOfItems() > 0:
      # set node used before reload in the current instance
      self.endPoints = allEndPoints.GetItemAsObject(0)
      self.endPoints.RemoveAllMarkups()
    else:
      self.endPoints = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
      self.endPoints.SetName("EndPoints")
      self.endPoints.RemoveAllMarkups()
    allEndPoints = None 
  
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
    diff = np.subtract(entryPos,controllerPos)
    dist = np.linalg.norm(diff)
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
    diff = np.subtract(controllerPos,self.vrhelper.lastControllerPos)
    entryPos = self.getEntry()
    newEntryPos = np.add(entryPos,diff)
    dist = np.linalg.norm(np.subtract(entryPos,controllerPos))
    # If controller is near, unselected the markup the change color
    if dist < 30.0:
      self.endPoints.SetNthControlPointSelected(1, False)
    elif not self.movingEntry:
      self.endPoints.SetNthControlPointSelected(1, True)
    # Check if entry point is currently being modified by user
    self.vrhelper.lastControllerPos = controllerPos

  def onLeftControllerTriggerPressed(self):
    """ Callback function on trigger pressed event. If a shader with "relativePosition" parameter has been selected
        allows user to change this parameter based on future position compared to the position when pressed.
    """
    if not self.customShader:
      return
    if self.customShader.hasShaderParameter('relativePosition', float):
      # Set init position to be compared with future positions
      self.leftInitPos = self.getLeftControllerPosition()
      self.leftInitRatio = self.customShader.getShaderParameter("relativePosition", float)
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
      diff = np.subtract(target, entry)
      range = np.linalg.norm(diff)
      dir = diff / range
      # Compute current position compared to the position when the trigger has been pressed
      curPos = self.getLeftControllerPosition()
      motion = np.subtract(curPos,self.leftInitPos)
      offsetRatio = np.dot( motion, dir )/range
      # Change relative position based on the position
      newRatio = np.clip(self.leftInitRatio + offsetRatio,0.0,1.0)
      self.customShader.setShaderParameter("relativePosition", newRatio, float)
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


