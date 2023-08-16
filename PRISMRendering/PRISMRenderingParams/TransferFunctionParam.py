from PRISMRenderingParams.Param import Param
import vtk, qt, ctk, slicer, inspect

#Class for shaders' transfer function parameters

class TransferFunctionParam(Param):

  def __init__(self, name, display_name, type, defaultValue = []):
    Param.__init__(self, name, display_name)
    self.type = type
    self.defaultValue = defaultValue
    self.value = defaultValue
    self.widget = None
    self.label = None
    self.transferFunction = None
    self.storedValue = self.value #in case it is a boolean TF, we need to update with the default value if it isn't checked anymore or the stored value if it is checked again

  def setValue(self, value, updateGUI = False):
    self.value = value
    #print("Caller : ", inspect.stack()[1][3], " Value : ", self.value)
    if updateGUI:
      self.updateGUIFromValue()

  def SetupGUI(self, widgetClass, volumeID, TFIndex):
       """Function to add transfer function widgets to the ui.

       :param parameters: Dictionnary of transfert functions. 
       :type parameters: str
       :param paramNames: Name of the transfert functions.
       :type paramNames: dictstr].
       :param volumeID: ID of the volume. 
       :type volumeID: int
       """
       if volumeID == 0:
         volumePrincipal = True
       else :
         volumePrincipal = False
         #minus one because the array of TF starts at 0
         #volumeID -=1

       # IF this is the principal volume
       if volumePrincipal :
         volumePropertyNode = widgetClass.logic.volumes[widgetClass.logic.volumeIndex].volumeRenderingDisplayNode.GetVolumePropertyNode()
         self.createTransferFunctionWidget(widgetClass, volumePropertyNode, False, volumeID)
       else : 
         # If this is a secondary volume
         transferFunctionID = volumeID * widgetClass.numberOfTFTypes
         # If the volume of the transfer function is already rendered create the widget
         if widgetClass.logic.volumes[widgetClass.logic.volumeIndex].secondaryVolumeRenderingDisplayNodes[volumeID] is not None: 
           volumePropertyNode = widgetClass.logic.volumes[widgetClass.logic.volumeIndex].secondaryVolumeRenderingDisplayNodes[volumeID].GetVolumePropertyNode()
           self.createTransferFunctionWidget(widgetClass, volumePropertyNode, True, volumeID)
         else :
           # Add the transfer functions to a list, so when the volume is rendered the widgets can be created
           if len(widgetClass.transferFunctionParams) <= transferFunctionID + TFIndex:
             widgetClass.transferFunctionParams.append(self)
             widgetClass.transferFunctionParamsName.append(self.name)
           else :
             widgetClass.transferFunctionParams[transferFunctionID + TFIndex] = self
             ## Name of the transfer function
             widgetClass.transferFunctionParamsName[transferFunctionID + TFIndex] = self.name

  def createTransferFunctionWidget(self, widgetClass, volumePropertyNode, secondTf, volumeID) :
      """Function to create a transfert fuction widget.

      :param volumePropertyNode: Volume property node to be associated to the widget. 
      :type volumePropertyNode: vtkMRMLVolumePropertyNode
      :param secondTf: If the widget is one of the secondary volumes. 
      :type secondTf: bool
      :param volumeID: ID of the volume. 
      :type volumeID: 
      """

      TFType = self.type
      ## Transfer function of the volume
      if TFType == 'color':
        self.transferFunction = volumePropertyNode.GetColor()
      elif TFType == 'scalarOpacity':
        self.transferFunction = volumePropertyNode.GetScalarOpacity()

      # Check if the widget for the nth volume already exists
      if secondTf :
        self.widget = widgetClass.secondColorTransferFunctionWidget[volumeID][TFType]

        if self.widget is not None :
          # Remove widget and label
          self.widget.setParent(None)
          widgetClass.secondColorTransferFunctionWidget[volumeID][TFType] = None
          #widget = None
          self.label = widgetClass.ui.centralWidget.findChild(qt.QLabel, widgetClass.CSName + self.transferFunction.GetClassName() + self.name + "Label")
          if self.label != None:
            self.label.setParent(None)

      # Create the widget
      self.label = qt.QLabel(self.display_name)
      self.label.setObjectName(widgetClass.CSName + self.transferFunction.GetClassName() + self.name + "Label")

      self.widget = ctk.ctkVTKScalarsToColorsWidget()
      self.widget.setObjectName(widgetClass.CSName + self.transferFunction.GetClassName() + self.name + "Widget")
      self.transferFunction.name = widgetClass.CSName + self.transferFunction.GetClassName() + self.name

      # Change the points to the ones specified in the shader
      if self.value != [] :
        colors = self.value
        nbColors = len(colors)
        self.transferFunction.RemoveAllPoints()
        for i in range(nbColors): 
          if TFType == 'color':
            self.transferFunction.AddRGBPoint(colors[i][0], colors[i][1], colors[i][2], colors[i][3], colors[i][4], colors[i][5])  
          elif TFType == 'scalarOpacity':
           self.transferFunction.AddPoint(colors[i][0], colors[i][1], colors[i][2], colors[i][3])
        self.updateGUIFromValue()
      else:
        newValues = []
        nbPoints = self.transferFunction.GetSize()
        if widgetClass.getClassName(self.transferFunction) == "vtkColorTransferFunction":
          values = [0,0,0,0,0,0]
        else :
          values = [0,0,0,0]
        if nbPoints > 0:
          for i in range(nbPoints):
            self.transferFunction.GetNodeValue(i, values)
            temp = values[:]
            newValues.append(temp)
            self.defaultValue = newValues
            self.value = self.defaultValue
      if TFType == 'color':
        self.widget.view().addColorTransferFunction(self.transferFunction)
      elif TFType == 'scalarOpacity':
        self.widget.view().addOpacityFunction(self.transferFunction)

      self.widget.view().setAxesToChartBounds()
      self.widget.setFixedHeight(100)

      if secondTf :
        widgetClass.secondColorTransferFunctionWidget[volumeID][TFType] = self.widget
     # self.updateGUIFromParameterNode(widgetClass)
      self.transferFunction.AddObserver(vtk.vtkCommand.ModifiedEvent, lambda o, e : self.updateParameterNodeFromGUI(widgetClass))
        
  def updateParameterNodeFromGUI(self, widgetClass):
    newValues = []
    parameterNode = widgetClass.logic.parameterNode
    oldModifiedState = parameterNode.StartModify()
    parameterNode.SetParameter(self.widget.name, "transferFunction")
    nbPoints = self.transferFunction.GetSize()
    if widgetClass.getClassName(self.transferFunction) == "vtkColorTransferFunction":
      values = [0,0,0,0,0,0]
    else :
      values = [0,0,0,0]
    if nbPoints > 0:
      for i in range(nbPoints):
        self.transferFunction.GetNodeValue(i, values)
        temp = values[:]
        newValues.append(temp)
        parameterNode.SetParameter(self.widget.name+str(i), ",".join("{0}".format(n) for n in values))
      # If points are deleted, remove them from the parameter node
      i+=1
      val = parameterNode.GetParameter(self.widget.name+str(i))
      while val != '':
        parameterNode.UnsetParameter(self.widget.name+str(i))
        i+=1
        val = parameterNode.GetParameter(self.widget.name+str(i))
    parameterNode.EndModify(oldModifiedState)
    self.setValue(newValues)

  def updateGUIFromParameterNode(self, widgetClass):
    parameterNode = widgetClass.logic.parameterNode
    newValues = []
    for i in range(self.transferFunction.GetSize()):
      values = parameterNode.GetParameter(self.widget.name+str(i))
      if values != "" :
        newValues.append([float(k) for k in values.split(",")])
        self.transferFunction.SetNodeValue(i, [float(k) for k in values.split(",")])
    if newValues != []:
      self.setValue(newValues)

  def updateGUIFromValue(self):
    if self.transferFunction is not None:
      colors = self.value
      nbColors = len(colors)
      self.transferFunction.RemoveAllPoints()
      for i in range(nbColors): 
        if self.type == 'color':
          self.transferFunction.AddRGBPoint(colors[i][0], colors[i][1], colors[i][2], colors[i][3], colors[i][4], colors[i][5])  
        elif self.type == 'scalarOpacity':
         self.transferFunction.AddPoint(colors[i][0], colors[i][1], colors[i][2], colors[i][3])  

  def getValue(self):
    return self.value

  def show(self):
    self.widget.show()
    self.label.show()
    self.setValue(self.storedValue, True)

  def hide(self):
    self.widget.hide()
    self.label.hide()
    self.storedValue = self.value
    self.setValue(self.defaultValue, True)