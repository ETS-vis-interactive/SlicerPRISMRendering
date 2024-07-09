import vtk, slicer
from PRISMRenderingShaders import *

class PRISMRenderingVolume():

    def __init__(self, logic, volumeNode):
        
        self.logic = logic

        self.volumeNode = volumeNode 

        self.volumeRenderingDisplayNode = None

        self.colorTransferFunction = vtk.vtkColorTransferFunction()

        self.opacityTransferFunction = vtk.vtkPiecewiseFunction()

        self.shaderIndex = 0
        
        ## Type of the current custom shader
        self.customShaderType = None
        
        self.customShader = []

        self.setCustomShaderType('None')
        
        #To retrieve the shader's UI while coming back to the volume
        self.comboBoxIndex = 0

    def renderVolume(self):
        """Use Slicer Volume Rendering module to initialize and setup rendering of the given volume node.
        
        :param self.volumeNode: Volume node to be rendered. 
        :type self.volumeNode: VtkMRMLself.volumeNode
        :param multipleVolumes: If the rendered volume is a secondary volume. 
        :type multipleVolumes: Bool
        """
        logic = slicer.modules.volumerendering.logic()

        self.setupCustomShader()

        #if multiple volumes is enabled and number of volumes > 1, , turn off second rendering

        # Check if node selected has a renderer
        displayNode = logic.GetFirstVolumeRenderingDisplayNode(self.volumeNode)
        if displayNode:
          displayNode.SetNodeReferenceID("shaderProperty", self.shaderPropertyNode.GetID())
          roi = displayNode.GetMarkupsROINode()
          if roi is None:
            logic.CreateROINode(displayNode)
            logic.FitROIToVolume(displayNode)


          self.volumeRenderingDisplayNode = displayNode
        # Slicer default command to create renderer and add node to scene
        else:
          displayNode = logic.CreateDefaultVolumeRenderingNodes(self.volumeNode)
          slicer.mrmlScene.AddNode(displayNode)
          logic.CreateROINode(displayNode)
          logic.FitROIToVolume(displayNode)
          
          self.volumeNode.AddAndObserveDisplayNodeID(displayNode.GetID())

          displayNode.SetNodeReferenceID("shaderProperty", self.customShader[self.shaderIndex].shaderPropertyNode.GetID())

          logic.FitROIToVolume(displayNode)

        # Add a color preset based on volume range
        self.updateVolumeColorMapping(displayNode)

        # Prevent volume to be moved in VR
        self.volumeNode.SetSelectable(False)
        self.volumeNode.GetImageData()
        # Display given volume
        displayNode.SetVisibility(True)

        # Set value as class parameter to be accesed in other functions
        self.volumeRenderingDisplayNode = displayNode
        volumePropertyNode = displayNode.GetVolumePropertyNode()
        self.colorTransferFunction = volumePropertyNode.GetColor() 
        self.opacityTransferFunction = volumePropertyNode.GetScalarOpacity() 
        volumeName = volumePropertyNode.GetName()
        self.colorTransferFunction.name = volumeName+"Original" + self.colorTransferFunction.GetClassName() 
        self.opacityTransferFunction.name = volumeName+"Original" + self.opacityTransferFunction.GetClassName()

    def updateVolumeColorMapping(self, displayNode, volumePropertyNode = None):
      """Given a volume, compute a default color mapping to render volume in the given display node.
        If a volume property node is given to the function, uses it as color mapping.

      :param self.volumeNode: Volume node to be rendered.
      :type self.volumeNode: vtkMRMLself.volumeNode
      :param displayNode: Default rendering display node. (CPU RayCast, GPU RayCast, Multi-Volume)
      :type displayNode: vtkMRMLVolumeRenderingDisplayNode
      :param volumePropertyNode: Volume propery node that carries the color mapping wanted. 
      :type volumePropertyNode: VtkMRMLVolumePropertyNode
      """

      if not displayNode:
        return
      if volumePropertyNode:
        displayNode.GetVolumePropertyNode().Copy(volumePropertyNode)
      else:
        logic = slicer.modules.volumerendering.logic()
        # Select a color preset based on volume range
        scalarRange = self.volumeNode.GetImageData().GetScalarRange()
        if scalarRange[1]-scalarRange[0] < 1500:
          # small dynamic range, probably MRI
          displayNode.GetVolumePropertyNode().Copy(logic.GetPresetByName('MR-Default'))
        else:
          # larger dynamic range, probably CT
          displayNode.GetVolumePropertyNode().Copy(logic.GetPresetByName('CT-Chest-Contrast-Enhanced'))
        # Turn off shading
        displayNode.GetVolumePropertyNode().GetVolumeProperty().SetShade(False)

    def setupCustomShader(self):
      """Get or create shader property node and initialize custom shader.

      :param self.volumeNode: Current volume.
      :type self.volumeNode: vtkMRMLScalarself.volumeNode
      """
      CSExists = self.checkIfCSExists()
      if CSExists == -1:
        shaderPropertyName = "ShaderProperty" + self.volumeNode.GetName()
        CustomShader.GetAllShaderClassNames()
        if self.volumeRenderingDisplayNode is None :
          ## Property node of the current shader
          self.shaderPropertyNode = slicer.vtkMRMLShaderPropertyNode()
          self.shaderPropertyNode.SetName(shaderPropertyName)
          slicer.mrmlScene.AddNode(self.shaderPropertyNode)
        else :
          self.shaderPropertyNode = self.volumeRenderingDisplayNode.GetShaderPropertyNode()
        if self.customShader != [] :
          self.customShader[self.shaderIndex].resetVolumeProperty()
        self.customShader.append(CustomShader.InstanciateCustomShader(self.customShaderType, self.shaderPropertyNode, self.volumeNode, self.logic))
        self.shaderIndex = len(self.customShader)-1
        try :
          self.customShader[self.shaderIndex].customShaderPoints.updateGUIFromParameterNode(self)
        except :
          pass
        
      else :
        self.customShader[self.shaderIndex].resetVolumeProperty()
        self.shaderIndex = CSExists
        self.customShader[self.shaderIndex].shaderPropertyNode = self.shaderPropertyNode
        self.customShader[self.shaderIndex].volumeNode = self.volumeNode

    def setCustomShaderType(self, shaderTypeName):
      """Set given shader type as current active shader.

      :param shaderTypeName: Name corresponding to the type of rendering needed.
      :type shaderTypeName: str

      :param self.volumeNode: Current volume.
      :type self.volumeNode: vtkMRMLScalarself.volumeNode
      """

      self.customShaderType = shaderTypeName
      self.setupCustomShader()

    def getCustomShaderType(self):
        return self.customShader

    def onCustomShaderParamChanged(self, value, Param ):
      """Change the custom parameters in the shader.

      :param value: Value to be changed 
      :type value: str
      :param paramName: Name of the parameter to be changed 
      :type paramName: Int
      :param type_: (float or int), type of the parameter to be changed
      """
      
      self.customShader[self.shaderIndex].setShaderParameter(Param, value)

    def checkIfCSExists(self) :
      """Check if a custom shader exists.

      :param CSName: Name of the current custom shader. 
      :type CSName: str
      """
      for i, CS in enumerate(self.customShader) :
        if CS.GetDisplayName() == self.customShaderType :
          return i
      return -1