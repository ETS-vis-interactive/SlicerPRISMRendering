import vtk, qt, ctk, slicer
from PRISMRenderingParams import *

class CustomShaderPoints():
    def __init__(self, customShader, logic):

        self.currentMarkupBtn = None

        self.pointType = ''
        self.pointName = ''
        self.pointIndexes = {}

        self.logic = logic

        self.customShader = customShader
        
        self.createPointTypes()

        self.createEndPoints()
        self.addObservers()

    def createPointTypes(self):
      self.pointTypes = []
      for p in self.customShader.param_list:
        if isinstance(p, FourFParam):
          self.pointTypes.append(p.name)

    def createEndPoints(self):
      """Create endpoints."""
      # retrieve end points in the scene or create the node
      name = "EndPoints" + self.logic.volumes[self.logic.volumeIndex].volumeNode.GetName() + self.customShader.GetDisplayName()
      name = name.replace(" ", "")
      allEndPoints = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsFiducialNode', name)
      slicer.mrmlScene.RemoveNode(allEndPoints.GetItemAsObject(0))
      self.endPoints = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
      self.endPoints.SetName(name)
      self.endPoints.GetDisplayNode().SetGlyphScale(6.0)
      self.endPoints.RemoveAllControlPoints()

      self.node_id = self.endPoints.GetID()

      allEndPoints = None

    def onCustomShaderParamChangedMarkup(self, value, paramName):
      """Change the custom parameters in the shader.

      :param value: Value to be changed 
      :type value: str
      :param paramName: Name of the parameter to be changed 
      :type paramName: Int
      :param type_: (float or int), type of the parameter to be changed
      """

      self.customShader.setShaderParameterMarkup(paramName, value)

    def setPlacingMarkups(self, paramType, paramName, btn, interaction = 1, persistence = 0):
      """Activate Slicer markups module to set one or multiple markups in the given markups fiducial list.

      :param btn: Button pushed to place the markup. 
      :type btn: QObject
      :param interaction:  
      :type interaction: Int0: /, 1: Place, 2: View transform, 3: / ,4: Select
      :param persistence:  
      :type persistence: Int0: Unique, 1: Peristent
      """
    
      self.currentMarkupBtn = btn
      self.pointType = paramType
      self.pointName = paramName

      # Getting the "EndPoints" node (always first MarkupsFiducial created)
      node = slicer.mrmlScene.GetNodeByID(self.node_id)
      # Setting the active node of markup list
      slicer.modules.markups.logic().SetActiveList(node)

      interactionNode = slicer.mrmlScene.GetNodeByID("vtkMRMLInteractionNodeSingleton")
      interactionNode.SetCurrentInteractionMode(interaction)
      interactionNode.SetPlaceModePersistence(persistence)

    def onEndPointAdded(self, caller, event):
     """Callback function to get the position of the new point.

     :param caller: Slicer.mrmlScene, Slicer active scene.
     :param event: Flag corresponding to the triggered event. 
     :type event: str
     """
     world = [0, 0, 0]
     if self.pointType in self.pointTypes:
       pointIndex = caller.GetDisplayNode().GetActiveControlPoint()
       caller.GetNthControlPointPositionWorld(pointIndex, world)
       # If the point was already defined
       if self.pointName in self.pointIndexes.keys() :
         index = self.pointIndexes[self.pointName]
         caller.SetNthControlPointPositionWorld(index, world)
         caller.RemoveNthControlPoint(pointIndex)
       else :
         self.pointIndexes[self.pointName] = pointIndex
         caller.SetNthControlPointLabel(pointIndex, self.pointType)

       self.onCustomShaderParamChangedMarkup(world, self.pointType)
       self.currentMarkupBtn.setText('Reset ' + self.pointType)

    def addObservers(self):
      endPointsname = self.customShader.GetDisplayName().replace(" ", "") + self.logic.volumes[self.logic.volumeIndex].volumeRenderingDisplayNode.GetVolumePropertyNode().GetName() + "markup"
      self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.onEndPointAdded)
      self.endPoints.name = endPointsname
      self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.pointModified)
      self.pointModifiedEventTag = self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.onEndPointsChanged)
      self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, 
      lambda c, e, name = endPointsname: self.updateParameterNodeFromGUI([c, "PointPositionDefinedEvent", name]))

    def removeObservers(self):
      self.endPoints.RemoveObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent)
      self.endPoints.RemoveObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent)

    @vtk.calldata_type(vtk.VTK_INT)
    def onEndPointsChanged(self, caller, event, call_data):
      """Callback function to get the position of the modified point.
      Note: Vtk.calldata_type(vtk.VTK_OBJECT) function get calling instance as a vtkMRMLNode to be accesed in the function.
   
      :param caller: Slicer active scene.
      :type caller: SlicermrmlScene.
      :param event: Flag corresponding to the triggered event. 
      :type event: str
      :param call_data: VtkMRMLNode, Node added to the scene.
      """
      
   
      #check if the point was added from the module and was set
      type_ = caller.GetNthControlPointLabel(call_data)
      world = [0, 0, 0]
      caller.GetNthControlPointPositionWorld(call_data, world)
      self.onCustomShaderParamChangedMarkup(world, type_)

    def updateParameterNodeFromGUI(self, value):
      parameterNode = self.logic.parameterNode
      oldModifiedState = parameterNode.StartModify()
      caller = value[0]
      event = value[1]
      index = value[2]
      name = self.endPoints.name + self.pointType
      world = [0, 0, 0]
      if event == "PointPositionDefinedEvent" :
        index = caller.GetDisplayNode().GetActiveControlPoint()
        # Initialise point
        if parameterNode.GetParameter(name) == "":
          index = caller.GetDisplayNode().GetActiveControlPoint()
          caller.SetNthControlPointAssociatedNodeID(index, name)
          caller.GetNthControlPointPositionWorld(index, world)
          parameterNode.SetParameter(name, ",".join("{0}".format(n) for n in world))
          parameterNode.SetParameter(self.endPoints.name, str(index))
          self.pointIndexes[name] = index
        # Reset point
        elif self.pointName != '' :
          name = self.pointName
          index = self.pointIndexes[name]
          caller.GetNthControlPointPositionWorld(index, world)
          parameterNode.SetParameter(name, ",".join("{0}".format(n) for n in world))
          self.pointName = ''

      if event == "PointModifiedEvent" :
        if parameterNode.GetParameter(self.endPoints.name) != "" and index <= int(parameterNode.GetParameter(self.endPoints.name)):
          pointName = caller.GetNthControlPointAssociatedNodeID(index)
          if parameterNode.GetParameter(pointName) != "":
            caller.GetNthControlPointPositionWorld(index, world)
            parameterNode.SetParameter(pointName, ",".join("{0}".format(n) for n in world))
      parameterNode.EndModify(oldModifiedState)

    @vtk.calldata_type(vtk.VTK_INT)
    def pointModified(self, caller, event, index):
      self.updateParameterNodeFromGUI([caller, "PointModifiedEvent", index])

    def updateGUIFromParameterNode(self, logic):
      # self.customShader[self.shaderIndex].customShaderPoints.removeObservers()

      parameterNode = logic.parameterNode
      if not parameterNode or parameterNode.GetParameterCount() == 0:
        return

      params = parameterNode.GetParameterNames()
      markups = []
      for p in params:
        if self.endPoints.name in p :
          markups.append(p)
      volumeName = self.volumeRenderingDisplayNode.GetVolumePropertyNode().GetName()
      for m in markups :
        values = parameterNode.GetParameter(m)
        #If point was defined
        values = [float(k) for k in values.split(",")]
        if len(values) > 1 :
          type_ = m.replace(self.endPoints.name, '')
          values.pop()
          index = self.endPoints.AddFiducialFromArray(values, type_)
          self.endPoints.SetNthFiducialAssociatedNodeID(index, m)
          CSName = self.endPoints.name.replace(volumeName+'markup'+type_, '')
          visible = self.CSName+"markup" == CSName 
          self.pointIndexes[m] = index
          world = [0, 0, 0, 0]
          self.endPoints.GetNthFiducialWorldCoordinates(index, world)
          self.onCustomShaderParamChanged(world, type_, "markup")
          self.endPoints.SetNthControlPointVisibility(index, visible)

      # self.customShader[self.shaderIndex].customShaderPoints.addObservers()
      
    def UpdateGUIFromValues(self, logic):

      params = [p for p in logic.volumes[logic.volumeIndex].customShader[logic.volumes[logic.volumeIndex].shaderIndex].param_list if isinstance(p, FourFParam)]
      for p in params :
        if 'markup' + p.name in self.pointIndexes :
        #If point was defined
          index = self.pointIndexes['markup' + p.name]
          values = p.toList()
          self.endPoints.SetNthControlPointPositionWorld(index, values[:3])