import vtk, qt, ctk, slicer
from PRISMRenderingParams import *

class CustomShaderPoints():
    def __init__(self, CustomShader):

        self.currentMarkupBtn = None

        self.pointType = ''
        self.pointName = ''
        self.pointIndexes = {}

        self.customShader = CustomShader
        
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
      name = "EndPoints" + self.customShader.GetDisplayName()
      name = name.replace(" ", "")
      # print(name)
      allEndPoints = slicer.mrmlScene.GetNodesByClassByName('vtkMRMLMarkupsFiducialNode', name)
      if allEndPoints.GetNumberOfItems() > 0:
        # set node used before reload in the current instance
        ## All endpoints in the scene
        self.endPoints = allEndPoints.GetItemAsObject(0)
        self.endPoints.RemoveAllControlPoints()
        self.endPoints.GetDisplayNode().SetGlyphScale(6.0)
      else:
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
      self.pointModifiedEventTag = self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointModifiedEvent, self.onEndPointsChanged)
      self.endPoints.AddObserver(slicer.vtkMRMLMarkupsFiducialNode.PointPositionDefinedEvent, self.onEndPointAdded)

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
      pointName = caller.GetNthControlPointAssociatedNodeID(call_data)
      if pointName in self.pointIndexes.keys() and self.pointIndexes[pointName] == call_data :
        world = [0, 0, 0]
        caller.GetNthControlPointPositionWorld(call_data, world)
        self.onCustomShaderParamChangedMarkup(world, type_)