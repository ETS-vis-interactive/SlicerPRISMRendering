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
<!---
5. If you are currently developping the shader you can click on the "..." button in order to reload, duplicate or open the shader :
    
    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/applyCS/345.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

    * Reload the shader by clicking on the "Reload" button. This will reload all the new functionnalities added to the file containing the shader.
    * Duplicate the shader by clicking on the "Duplicate" button. This will create a duplicate class of the class containing the shader.
    * Open the shader by clicking on the "Open" button. This will open the class containing the shader in your favorite editor.
    
    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/applyCS/6.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
-->

## View the sample data of a shader
1. Select the shader of your choice in the comboBox.

2. Click the button "Switch to Shader's Sample data".
<a name="allshaders"></a>

## Implemented shaders

This section contains a detailed description on how to use each of the techniques implemented in the module, and require to perform steps 1-3 of the [precedent](#applyshader) section.

### Chroma Depth Perception

This technique brings out the depth of a volume with a smooth transition between all hues.

It is possible to :

* Adjust the range of the volume.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/range.gif" width ="100%" style="margin-left: auto;margin-right: auto; display: block;/">

* Adjust the transfer function's points.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/colors.gif" width ="100%" style="margin-left: auto;margin-right: auto; display: block;"/>

<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/chromaDepth.gif" width ="50%" style="margin-left: auto;
  margin-right: auto; display: block;"/>

### Opacity Peeling

This technique respond to the problem of occlusion of certain structures in the volume. It consists in removing the first n layers of tissue during the integration of the ray.

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

It is possible to :

* Adjust the step for the calculation of the gradient.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/outline/gradStep.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Adjust the parameters allowing to modify the gradients intensities captured by the function.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/outline/step.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

### Echo Volume 

This shader allow the user to see the depth of the volume with a lightning effect.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/EchoVolume/echoVolume.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

### Plane Intersecting

This technique allows to visualize the anatomy along the approach plane for surgery.

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
<!--
You can download the sample volume by clicking <a href="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRenderingDatabase/master/volumes/MR-head.nrrd" download>here</a>.
-->
It is possible to :

* Modify the position of the center of the sphere.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/sphereCarving/center.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Modify the radius of the sphere.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/sphereCarving/radius.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

