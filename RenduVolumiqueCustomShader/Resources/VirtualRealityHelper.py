import slicer, qt, vtk, numpy

class VirtualRealityHelper():
  def __init__(self, volumeRenderingDisplayNode):
    assert hasattr(slicer.modules, "virtualreality"), 'VirtualRealityHelper: Slicer VR module is not installed'
    self.vr = slicer.modules.virtualreality
    self.volumeRenderingDisplayNode = None
    if volumeRenderingDisplayNode:
      self.volumeRenderingDisplayNode = volumeRenderingDisplayNode
    self.setVRActive()

  def setVRActive(self):
    """ Function to connect VR hardware to current scene and set up VR scene properties as needed.
    """
    self.vr.logic().SetVirtualRealityConnected(True) # Connect to hardware
    self.vr.logic().SetVirtualRealityActive(True) # Project scene in the headset
    self.vr.widgetRepresentation().setControllerTransformsUpdate(True) # Expose controller transform in Slicer
    self.vr.widgetRepresentation().setHMDTransformUpdate(True) # Expose HMD transform in Slicer

    self.vr.viewWidget().EnableGrabObjects(False) # Disable grabing objects
    self.vr.viewWidget().SetGestureButtonToGrip() # Set scene manipulation to grip buttons
    self.vr.viewWidget().EnableDolly3D(False) # Disable Dolly (moving in the 3D scene)
    # Create callbacks on button events
    self.vr.viewWidget().LeftControllerTrackpadPressed.connect(self.onLeftControllerTrackpadPressed)
    self.vr.viewWidget().LeftControllerTrackpadReleased.connect(self.onLeftControllerTrackpadReleased)
    self.vr.viewWidget().RightControllerTrackpadPressed.connect(self.onRightControllerTrackpadPressed)

    # Change Slicer VR Scene background for a better visualization
    self.setVRBackgroundColors()

    # Delayed to function for objects and observers who needs objects created after some time,
    # such as controller transforms
    qt.QTimer.singleShot(0, lambda: self.initDelayedVRParameters())      

    # If not already done, allow volume rendering to be displayed in VR view
    if self.volumeRenderingDisplayNode:
      self.volumeRenderingDisplayNode.AddViewNodeID("vtkMRMLVirtualRealityViewNodeActive")

  def initDelayedVRParameters(self):
    """ Add observers and init positions, this must be performed after the controllers have been activated in the VR scene.
    """
    self.lastControllerPos = self.getRightControllerPosition()
    self.createVRControllerLaser()
    self.createHelpControlsDisplay()

  def setVRBackgroundColors(self, color1=[0.1,0.1,0.2],color2=[0.3,0.3,0.4]):
    """ Change Slicer VR scene background color.

    Args:
        color1 (array[int]): bottom color of background fade.
        color2 (array[int]): top color of background fade.
    """
    self.vr.logic().GetVirtualRealityViewNode().SetBackgroundColor(color1)
    self.vr.logic().GetVirtualRealityViewNode().SetBackgroundColor2(color2)

  def bringWorldToVRControllers(self):
    """ Set World coordinates on controller current position.
    """
    vrViewWidget = self.vr.viewWidget()
    if vrViewWidget is None:
      return None
    vrViewWidget.BringWorldToControllers()

  def getRightTransformNode(self):
    """ Generic getter for right controller transform node.

    Returns:
          vtkMRMLLinearTransformNode: Right Controller transform node.
    """
    rightTransform = slicer.mrmlScene.GetNodesByName('VirtualReality.RightController').GetItemAsObject(0)
    return rightTransform

  def getRightControllerPosition(self):
    """ Generic getter for right controller position in world coordinates.

    Returns:
          tuple(double): Right Controller 3d coordinates.
    """
    rightTransform = self.getRightTransformNode()
    mat = vtk.vtkMatrix4x4()
    # Extract translation values of the matrix corresponding to the position in the world
    rightTransform.GetMatrixTransformToWorld(mat)
    return ( mat.GetElement(0,3), mat.GetElement(1,3), mat.GetElement(2,3) )


  def getLeftTransformNode(self):
    """ Generic getter for left controller transform node.

    Returns:
          vtkMRMLLinearTransformNode: Left Controller transform node.
    """
    leftTransform = slicer.mrmlScene.GetNodesByName('VirtualReality.LeftController').GetItemAsObject(0)
    return leftTransform

  def getLeftControllerPosition(self):
    """ Generic getter for left controller position in world coordinates.

    Returns:
          tuple(double): Left Controller 3d coordinates.
    """    
    leftTransform = self.getLeftTransformNode()
    mat = vtk.vtkMatrix4x4()
    leftTransform.GetMatrixTransformToWorld(mat)
    return ( mat.GetElement(0,3), mat.GetElement(1,3), mat.GetElement(2,3) )

  def onLeftControllerTrackpadPressed(self,x,y):
    """ Callback function when the trackpad on the left controller has been pressed.
        It displays a laser when the trackpad button is hold.
    """
    # Display the laser geometry
    self.laserModelDisplay.VisibilityOn()
    # Scale laser radius based on VR magnification
    magnification = self.vr.logic().GetVirtualRealityViewNode().GetMagnification()
    self.laserTubeFilter.SetRadius(2.0 / magnification)
    self.laserTubeFilter.Update()

  def onLeftControllerTrackpadReleased(self,x,y):
    """ Callback function when the trackpad on the left controller has been released.
        Hides the laser.
    """    
    self.laserModelDisplay.VisibilityOff()

  def onRightControllerTrackpadPressed(self,x,y):
    """ Callback function when the trackpad on the right controller has been pressed.
        Bring the center of the scene at controller position.
    """    
    self.bringWorldToVRControllers()

  def createVRControllerLaser(self):
    """ Function to create a geometry similar to a pointer laser.
    """
    self.laserPoints = vtk.vtkPoints()
    self.laserPoints.SetNumberOfPoints(2)
    self.laserPoints.SetPoint(0, (2,-5.5,2))
    self.laserPoints.SetPoint(1, (350,-1000,-1500))

    lines = vtk.vtkCellArray()
    lines.InsertNextCell(2)
    lines.InsertCellPoint(0)
    lines.InsertCellPoint(1)
    path = vtk.vtkPolyData()
    path.SetPoints(self.laserPoints)
    path.SetLines(lines)

    # Create a tube from a segment
    self.laserTubeFilter = vtk.vtkTubeFilter()
    self.laserTubeFilter.SetInputData(path)
    self.laserTubeFilter.SetRadius(2.0)
    self.laserTubeFilter.SetNumberOfSides(20)
    self.laserTubeFilter.CappingOn()
    self.laserTubeFilter.Update()

    # Create model node
    pathModel = slicer.vtkMRMLModelNode()
    # pathModel.HideFromEditorsOn()
    pathModel.SetSelectable(False)
    pathModel.SetScene(slicer.mrmlScene)
    pathModel.SetName("Laser")
    pathModel.SetPolyDataConnection(self.laserTubeFilter.GetOutputPort())

    # Create model display node to be accesed when using a controller button
    self.laserModelDisplay = slicer.vtkMRMLModelDisplayNode()
    self.laserModelDisplay.SetColor(1,0,0) # red
    self.laserModelDisplay.SetScene(slicer.mrmlScene)
    self.laserModelDisplay.SetVisibility2D(True)
    self.laserModelDisplay.VisibilityOff()
    slicer.mrmlScene.AddNode(self.laserModelDisplay)
    pathModel.SetAndObserveDisplayNodeID(self.laserModelDisplay.GetID())

    # Add node to scene
    slicer.mrmlScene.AddNode(pathModel)

    # Display laser only in the VR view
    self.laserModelDisplay.AddViewNodeID("vtkMRMLVirtualRealityViewNodeActive")

  def createHelpControlsDisplay(self):
    # Left controls display
    self.leftControlsDisplayMarkups = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
    self.leftControlsDisplayMarkups.SetName("LeftControls")
    self.leftControlsDisplayMarkups.HideFromEditorsOn()
    self.leftControlsDisplayMarkups.AddFiducialFromArray((15,-10,95))
    self.leftControlsDisplayMarkups.SetNthFiducialLabel(0, "Grab objects")
    self.leftControlsDisplayMarkups.AddFiducialFromArray((0,0,50))
    self.leftControlsDisplayMarkups.SetNthFiducialLabel(1, "Laser")
    self.leftControlsDisplayMarkups.GetDisplayNode().SetSelectedColor(0,2/3,1)
    self.leftControlsDisplayMarkups.GetDisplayNode().SetTextScale(6.0)
    self.leftControlsDisplayMarkups.GetDisplayNode().AddViewNodeID("vtkMRMLVirtualRealityViewNodeActive")
    self.leftControlsDisplayMarkups.GetDisplayNode().SetVisibility(False)
    self.leftControlsDisplayMarkups.SetAndObserveTransformNodeID(self.getLeftTransformNode().GetID())

    self.rightControlsDisplayMarkups = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsFiducialNode')
    self.rightControlsDisplayMarkups.SetName("RightControls")
    self.rightControlsDisplayMarkups.HideFromEditorsOn()
    self.rightControlsDisplayMarkups.AddFiducialFromArray((-15,-10,95))
    self.rightControlsDisplayMarkups.SetNthFiducialLabel(0, "Grab objects")
    self.rightControlsDisplayMarkups.AddFiducialFromArray((0,0,50))
    self.rightControlsDisplayMarkups.SetNthFiducialLabel(1, "Bring objects to controller")
    self.rightControlsDisplayMarkups.AddFiducialFromArray((-5,-30,47))
    self.rightControlsDisplayMarkups.SetNthFiducialLabel(2, "Move Entry point")
    self.rightControlsDisplayMarkups.GetDisplayNode().SetSelectedColor(0,2/3,1)
    self.rightControlsDisplayMarkups.GetDisplayNode().SetTextScale(6.0)
    self.rightControlsDisplayMarkups.GetDisplayNode().AddViewNodeID("vtkMRMLVirtualRealityViewNodeActive")
    self.rightControlsDisplayMarkups.GetDisplayNode().SetVisibility(False)
    self.rightControlsDisplayMarkups.SetAndObserveTransformNodeID(self.getRightTransformNode().GetID())


  def setControlsMarkupsPositions(self, side):
    magnification = slicer.modules.virtualreality.logic().GetVirtualRealityViewNode().GetMagnification()
    # Update geometry and display
    if side == "Left":
      self.leftControlsDisplayMarkups.SetNthControlPointPositionFromArray(0, numpy.array((12,-10, 95)) / magnification) # Grab objects
      self.leftControlsDisplayMarkups.SetNthControlPointPositionFromArray(1, numpy.array((0, 0, 50)) / magnification)
      self.leftControlsDisplayMarkups.GetDisplayNode().SetGlyphScale(10.0 / magnification)
    if side == "Right":
      self.rightControlsDisplayMarkups.SetNthControlPointPositionFromArray(0, numpy.array((-12,-10, 95)) / magnification) # Grab objects
      self.rightControlsDisplayMarkups.SetNthControlPointPositionFromArray(1, numpy.array((0,0,50)) / magnification)
      self.rightControlsDisplayMarkups.SetNthControlPointPositionFromArray(2, numpy.array((-5, -30, 47)) / magnification)
      self.rightControlsDisplayMarkups.GetDisplayNode().SetGlyphScale(10.0 / magnification)

  def updateLaserPosition(self):
    if not self.laserModelDisplay.GetVisibility():
      return
    # Get current controller position to set up laser starting point
    controllerPosition = self.getLeftControllerPosition()
    self.laserPoints.SetPoint(0, controllerPosition)
    # Compute the position of a point far from the controller position and 
    # creating a coherent direction for the laser, based on controller current pose
    leftTransform = self.getLeftTransformNode()
    mat = vtk.vtkMatrix4x4()
    leftTransform.GetMatrixTransformToWorld(mat)
    point = mat.MultiplyPoint((350,-1000,-1500,1))
    # Update geometry and display
    self.laserPoints.SetPoint(1, point[:3])
    self.laserPoints.Modified()

  def showVRControls(self):
    self.rightControlsDisplayMarkups.GetDisplayNode().SetVisibility(True)
    self.leftControlsDisplayMarkups.GetDisplayNode().SetVisibility(True)

  def hideVRControls(self):
    self.rightControlsDisplayMarkups.GetDisplayNode().SetVisibility(False)
    self.leftControlsDisplayMarkups.GetDisplayNode().SetVisibility(False)