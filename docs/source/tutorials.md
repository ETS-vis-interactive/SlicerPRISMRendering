# Tutorials

<a name="rendering"></a>

## Rendering a volume

1. Open the "Data" section. 

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/render/1.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
2. Select your volume in the comboBox.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/render/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>    
3. Open the "View Setup" section.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/render/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
4. Apply the volume rendering to your volume by clicking on the "Volume Rendering" checkBox.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/render/4.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

<a name="applyshader"></a>

## Applying a shader to a volume

1. [Render the volume](#rendering).
2. Open the "Custom Shader" section.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/applyCS/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
3. Select the shader of your choice in the comboBox.

4. Adjust the different parameters. A detailed description on how to use each shader is located [here](#allshaders).

5. If you are currently developping the shader you can click on the "..." button in order to reload, duplicate or open the shader :
    
    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/applyCS/345.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

    * Reload the shader by clicking on the "Reload" button. This will reload all the new functionnalities added to the file containing the shader.
    * Duplicate the shader by clicking on the "Duplicate" button. This will create a duplicate class of the class containing the shader.
    * Open the shader by clicking on the "Open" button. This will open the class containing the shader in your favorite editor.
    
    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/applyCS/6.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>


<a name="allshaders"></a>

## Implemented shaders

This section contains a detailed description on how to use each of the techniques implemented in the module, and require to perform steps 1-3 of the [precedent](#applyshader) section.

### Chroma Depth Perception

This technique brings out the depth of a volume with a smooth transition between all hues.

You can download the sample volume by clicking <a href="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRenderingDatabase/master/volumes/1.mnc" download>here</a>.

It is possible to :

* Adjust the range of the volume.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/range.gif" width ="100%" style="margin-left: auto;margin-right: auto; display: block;/">

* Adjust the transfer function's points.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/colors.gif" width ="100%" style="margin-left: auto;margin-right: auto; display: block;"/>

<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/chromaDepth.gif" width ="50%" style="margin-left: auto;
  margin-right: auto; display: block;"/>

### Opacity Peeling

This technique respond to the problem of occlusion of certain structures in the volume. It consists in removing the first n layers of tissue during the integration of the ray.

You can download the sample volume by clicking <a href="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRenderingDatabase/master/volumes/MR-head.nrrd" download>here</a>.

It is possible to :

* Adjust the lower value of the threshold.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/opacityPeeling/low_thresh.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Adjust the upper value of the threshold.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/opacityPeeling/high_thresh.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Adjust the wanted layer.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/opacityPeeling/wantedLayer.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Enable/disable the use of a sphere to peel the volume and specify the center of the sphere.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/opacityPeeling/sphere.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Modify the radius of the sphere.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/opacityPeeling/sphere_radius.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

### Outline

This shader highlights the borders of the volume and is particularly useful for visualizing complex structures such as the blood vessels of the brain. Indeed, the accentuation of the edges of the vessels makes it possible to improve the perception of the depths by ordering the order of depth of overlapping vessels.

You can download the sample volume by clicking <a href="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRenderingDatabase/master/volumes/1.mnc" download>here</a>.

It is possible to :

* Adjust the step for the calculation of the gradient.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/outline/gradStep.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Adjust the parameters allowing to modify the gradients intensities captured by the function.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/outline/step.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

### Plane Intersecting

This technique allows to visualize the anatomy along the approach plane for surgery.

You can download the sample volume by clicking <a href="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRenderingDatabase/master/docs//MR-head.nrrd" download>here</a>.

It is possible to :

* Initialize the two points.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/planeIntersecting/entry_target.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Adjust the relative position of the plane between the two points.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/planeIntersecting/relative.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Modify the position of the two points.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/planeIntersecting/modify_points.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Enable/disable the use of a third plane.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/planeIntersecting/thirdPlane.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

### Sphere carving

This shader makes it possible to cut out spherical parts of the volume interactively, which can obstruct structures of interest with similar intensities.

You can download the sample volume by clicking <a href="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRenderingDatabase/master/volumes/MR-head.nrrd" download>here</a>.

It is possible to :

* Modify the position of the center of the sphere.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/sphereCarving/center.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Modify the radius of the sphere.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/sphereCarving/radius.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

## Modifying the ROI of a volume

1. [Render the volume](#rendering).
2. Enable the cropping of the volume with the ROI by clicking on the "Enable Cropping" checkBox.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyROI/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>    
3. Display the ROI of the volume by clicking on the "Display ROI" checkBox.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyROI/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
4. You can scale and rotate the ROI :

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyROI/45.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

    * Scale the ROI :
        1. Enable the scalling of the ROI by clicking on the "Enable Rotation" checkBox.
        2. Select one of the handle of the ROI and move it towards the center or the outside of the volume to scale the ROI.

        <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyROI/scale.gif" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>    
    * Rotate the ROI :
        1. Enable the rotation of the ROI by clicking on the "Enable Rotation" checkBox.
        2. Select one of the side of the ROI and move it in any direction to rotate the ROI.

        <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyROI/rotate.gif" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

## Creating a new shader

1. Open the "Modify or Create Custom Shader" section.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/createCS/1.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;" />
2. In the comboBox, select "Create new Custom Shader".

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/createCS/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
3. Type the name of the shader that will be used as a class name.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/createCS/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
4. Type the display name of the shader that will be used in the UI.
5. Click the "Create" button.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/createCS/45.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
6. You can either :
    * Click on the "Edit" button and modify the python class manually.
    * Use the [ Add Code ](#addcode) and [ Add Parameter ](#addparam) tabs to modify the python class with the UI : 

        <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/createCS/6.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

## Modifying an existing shader

1. Open "Modify or Create Custom Shader" section.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyCS/1.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
2. In the comboBox, select the shader to modify.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyCS/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
3. Use the [ Add Code ](#addcode) and [ Add Parameter ](#addparam) tabs to modify the python class UI : 

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyCS/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

<a name="addparam"></a>

## Adding a parameter to a shader from the UI

1. In the comboBox, select the type of the parameter to add to the shader. 

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addParam/1.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
2. Type the name of the parameter that will be used inside the shader.  

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addParam/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
3. Type the display name of the parameter that will be used in the UI.  

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addParam/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
4. Modify the values according to the parameter.  
5. Click the "Add Parameter" button.    

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addParam/45.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
6. Repeat steps 1-5 for each wanted parameter.

<a name="addcode"></a>

## Adding code to a shader from the UI

1. In the first comboBox, select the tag type of the code to be added to the shader.  

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addCode/1.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
2. In the second comboBox, select the tag of the code to be added to the shader.  

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addCode/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
3. To add the code you can either :  

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addCode/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>   

    * Enter the code in the text area and click on the "Modify" button.
    * Click on the "Open File" button to enter the code directly in the python file.
4. Repeat steps 1-3 for each wanted code replacement.

<a name="panels"></a>
