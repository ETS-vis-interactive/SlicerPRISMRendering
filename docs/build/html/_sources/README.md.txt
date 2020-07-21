# SlicerPRISMRenderingRendering General Documentation

1. [ Introduction and Acknowledgements. ](#intro)
2. [ Module Description. ](#desc)
4. [ Tutorials. ](#tutos)
5. [ Panels and their use. ](#panels)
6. [ Similar Modules. ](#similar)
7. [ References. ](#ref)
8. [ Information for Developers. ](#info)

	* [ How Tos. ](#howto)
	* [ Limitations. ](#lim)

<a name="intro"></a>

## Introduction and Acknowledgements
**Title**: SlicerPRISMRendering

**Author(s)/Contributor(s)**: Simon Drouin, Professor at École de technologie supérieure (ÉTS), Montréal, Tiphaine RICHARD, Student Intern at ÉTS.

**License**: slicer4

**Acknowledgements**: 

**Contact**: Tiphaine RICHARD, tiphainejh@gmail.com

<a name="desc"></a>

## Module Description

This module is an implementation of the PRISM customizable volume rendering framework in 3D Slicer. Its purpose is to help easily creating and applying various rendering techniques to a volume.

Slicer version 4.11.0 is needed to use this module.


<a name="tutos"></a>
  
## Tutorials

<a name="rendering"></a>

### Rendering a volume

1. Open the "Data" section. 

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/render/1.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
2. Select your volume in the comboBox.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/render/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>    
3. Open the "View Setup" section.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/render/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
4. Apply the volume rendering to your volume by clicking on the "Volume Rendering" checkBox.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/render/4.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

<a name="applyshader"></a>
### Applying a shader to a volume

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

### Implemented shaders

This section contains a detailed description on how to use each of the techniques implemented in the module, and require to perform steps 1-3 of the [precedent](#applyshader) section.

#### Chroma Depth Perception

<details><summary> Chroma Depth Perception </summary>

<br>
This technique brings out the depth of a volume with a smooth transition between all hues.
It is possible to :

* Adjust the range of the volume.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/range.gif" width ="100%" style="margin-left: auto;margin-right: auto; display: block;/">

* Adjust the colors.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/colors.gif" width ="100%" style="margin-left: auto;margin-right: auto; display: block;"/>

<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/chromaDepth/chromaDepth.gif" width ="50%" style="margin-left: auto;
  margin-right: auto; display: block;"/>
</details>

<br>

#### Opacity Peeling

<details><summary> Opacity Peeling </summary>

<br>
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
</details>

<br>

#### Outline

<details><summary> Opacity Peeling </summary>

<br>
This shader highlights the borders of the volume and is particularly useful for visualizing complex structures such as the blood vessels of the brain. Indeed, the accentuation of the edges of the vessels makes it possible to improve the perception of the depths by ordering the order of depth of overlapping vessels.

It is possible to :

* Adjust the step for the calculation of the gradient.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/outline/gradStep.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Adjust the parameters allowing to modify the gradients intensities captured by the function.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/outline/step.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>
</details>

<br>

#### Plane Intersecting

<details><summary> Opacity Peeling </summary>

<br>
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
</details>

<br>

#### Sphere carving

<details><summary> Opacity Peeling </summary>

<br>
This shader makes it possible to cut out spherical parts of the volume interactively, which can obstruct structures of interest with similar intensities.

It is possible to :

* Modify the position of the center of the sphere.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/sphereCarving/center.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>

* Modify the radius of the sphere.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/allShaders/sphereCarving/radius.gif" width ="100%" style="margin-left: auto; margin-right: auto; display: block;"/>
</details>

<br>

### Modifying the ROI of a volume

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

### Creating a new shader

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

### Modifying an existing shader

1. Open "Modify or Create Custom Shader" section.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyCS/1.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
2. In the comboBox, select the shader to modify.

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyCS/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
3. Use the [ Add Code ](#addcode) and [ Add Parameter ](#addparam) tabs to modify the python class UI : 

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/modifyCS/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>

<a name="addparam"></a>

### Adding a parameter to a shader from the UI

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

### Adding code to a shader from the UI

1. In the first comboBox, select the tag type of the code to be added to the shader.  

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addCode/1.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
2. In the second comboBox, select the tag of the code to be added to the shader.  

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addCode/2.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>
3. To add the code you can either :  

    <img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/tutorials/addCode/3.png" width ="60%" style="margin-left: auto; margin-right: auto; display: block;"/>   

    * Enter the code in the text area and click on the "Modify" button.
    * Click on the "Open File" button to enter the code directly in the python file.
4. Repeat steps 1-3 for each wanted code replacement.
</details>

<br>

<a name="panels"></a>

## Panels and their use

<table style="table-layout: fixed; width:100%; border: 1px grey; border-collapse: collapse;">
<tr>
<td style=" width:50%">
<ul><li><b>Data</b> : Contains the volume required for SlicerPRISMRendering. </li>
<ul><li><b>Image Volume</b> : Select the current volume to render. </li></ul>
</ul>
</td>
<td>
<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/Data.png" alt="Data" width ="100%" title="Data"/>
</td>
</tr>
<tr>
<td style="width:50%">
<ul> 
<li> <b>View Setup</b> : Contains the controls for rendering the volume as well as controls for the cropping box (ROI) of the volume. </li>
<ul>
<li><b>Volume Rendering</b> : Enable/Disable rendering the volume.</li>
<li><b>Enable Cropping</b> : Enable/Disable cropping the volume.</li>
<li><b>Display ROI</b> : Enable/Disable displaying the ROI of the volume.</li>
<li><b>Enable Scaling</b> : Enable/Disable scaling the ROI of the volume.</li>
<li><b>Enable Rotation</b> : Enable/Disable rotating the ROI of the volume.</li>
</ul>
</ul>
</td>
<td align="center" style="width:50%">
<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/ViewSetup.png" alt="ViewSetup" width ="100%" title="ViewSetup"/>
</td>
</tr>
<tr>
<td style="width:50%">
<ul> 
<li><b>Custom Shader</b> : Controls of the shader.</li>
<ul>
<li><b>Custom Shader</b> : Name of the shader to be applied during the rendering.</li>
<li><b>Reload</b> : Reload the current shader.</li>
<li><b>Open</b> : Open the current shader source code.</li>
<li><b>Duplicate</b> : Duplicate the current shader source code.</li>
</ul>
</ul>
</td>
<td align="center" style="width:50%">
<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/CustomShader.png" alt="CustomShader" width ="100%" title="CustomShader"/>
</td>
</tr>
<tr>
<td rowspan=3 style="width:50%">
<ul> 
<li><b>Modify or Create Custom Shader</b> : Create or Modify a custom shader and add parameters.</li>
<ul>
<li><b>Shader</b> : Name of the shader to modify or <i>Create new Custom Shader</i> to create a new one.</li>
<li><b>Class Name</b> : Name of the class that will be created.</li>
<li><b>Display Name</b> : Name of the shader that will be displayed in the UI.</li>
<li><b>Create</b> : Create the class.</li>
<li><b>Add Code</b> : Add a code that will replace a specific shader tag in the shader.</li>
<ul>
<li><b>Tag Type</b> : Type of the tag to be remplaced in the shader.</li>
<li><b>Shader Tag</b>: Tag to be remplaced in the shader.</li>
<li><b>Shader Code</b> : Code to replace the specified tag in the shader. Can be added directly in the </li>file by clicking <i>Open File</i>.
<li><b>Open File</b> : Open the class containing the shader.</li>
<li><b>Modify</b> : Apply the modifications the the class.</li>
</ul>
<li><b>Add Param</b> : Add specified parameters to the class that will be used in the shader.</li>
<ul>
<li><b>Type</b> : Type of the parameter.</li>
<li><b>Name</b> : Name of the parameter that will be used in the shader.</li>
<li><b>Display Name</b> : Name of the parameter that will be displayed in the UI.</li>
<li><b>Add Parameter</b> : Add the parameter in the class.</li>
</ul>
</ul>
</ul>
</td>
<td align="center" style="width:50%">
<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/MCCustomShader.png" alt="MCCustomShader" width ="100%" title="MCCustomShader"/>
</td>
</tr>
<tr>
<td align="center" style="width:50%">
<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/MCCustomShaderCode.png" alt="MCCustomShaderCode" width ="100%" title="MCCustomShaderCode"/>
</td>
</tr>
<tr>
<td align="center" style=" width:50%">
<img src="https://raw.githubusercontent.com/ETS-vis-interactive/SlicerPRISMRendering/master/docs/source/images/MCCustomShaderParam.png" alt="MCCustomShaderParam" width ="100%" title="MCCustomShaderParam"/>
</td>
</tr>
</table>

<a name="similar"></a>

## Similar Modules

[VolumeRendering](https://www.slicer.org/wiki/Documentation/4.10/Modules/VolumeRendering)

<a name="ref"></a>

## References

[PRISM: An open source framework for the interactive design of GPU volume rendering shaders](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0193636).

<a name="info"></a>

## Information for Developers

See [this page](https://githubcomets-vis-interactiveSlicerPRISMRenderingrendering.readthedocs.io/en/latest/code.html) for the full code documentation.

<a name="howto"></a>

### How Tos

#### Create a shader 

Each of the volume rendering techniques is containted into one Python file and the GLSL code must be specified in the ```setupShader()``` method of the class.
This code must be written as a string which is transmitted to the shader carrying out the volume rendering by using the vtk shader modification classes [vtkUniforms](https://vtk.org/doc/nightly/html/classvtkUniforms.html) and [vtkShaderProperty](https://vtk.org/doc/nightly/html/classvtkShaderProperty.html). These strings replace on the fly tags in the format //VTK::SomeConcept::SomeAction in a shader template file. There is a defined list of tags that are suitable for different uses and the appropriate tag for the part of code you want to change in the shader must be specified in the Python class, as well as with the character string containing the code to replace. A more complete description of these tags can be found [here](https://kitware.github.io/vtk-js/api/Rendering_OpenGL_glsl.html). This is done in the following form:

``` python
replacement_code = """GLSL code"""
shader.AddFragmentShaderReplacement ("//VTK::SomeConcept::SomeAction", replacement_code)
```

Multiple tags can be used for one shader and they should all be specified in the ```setupShader()``` method.

All of the uniforms variables of the shader must be specified after the class declaration. There are 7 types of variables that can be added to the shader and they must respect this format, where \<name\> is the name used in the shader and \<display name\> is the name displayed in the UI :

##### Float

```python
shaderfParams = { '<name>' : { 'displayName' : '<display name>', 'min' : <minimum value>, 'max' : <maximum value>, 'defaultValue' : <default value>}, \
                  '<name>' : { ...}, \
                   ... }
```

##### Integer

```python
shaderiParams = { '<name>' : { 'displayName' : '<display name>', 'min' : <minimum value>, 'max' : <maximum value>, 'defaultValue' : <default value>}, \
                  '<name>' : { ...}, \
                   ... }
```

##### Point

```python
shader4fParams = { '<name>': {'displayName': '<display name>', 'defaultValue': {'x': <x value>, 'y': <y value>, 'z': <z value>, 'w': <w value>}}, \
                   '<name>' : { ...}, \
                    ... }
```
##### Boolean

```python
shaderbParams = { '<name>' : { 'displayName' : '<display name>', 'defaultValue' : <default value>, 'optionalWidgets' : [<name of optional parameter>, ...]}, \
                  '<name>' : { ...}, \
                   ... }
```

##### Range

```python
shaderrParams = { '<name>' : { 'displayName' : '<display name>', 'defaultValue' : [<minimum value>, <maximum value>]}, \
                  '<name>' : { ...}, \
                   ... }
```

##### Transfer functions

```python
shadertfParams = { '<name>' : { 'displayName' : '<display name>', 'defaultColors' : [[<First point x value>, <First point red value>, <First point green value>, <First point blue value>, <First point midpoint value>, <First point midpoint s Sharpness value> if color; <First point x value>, <First point opacity value>, <First point midpoint value>, <First point midpoint s sharpness value> if scalar opacity], ...], 'type' : '<'color' or 'scalarOpacity'>'}, \
                  '<name>' : { ...}, \
                   ... }
``` 

If the original values of the volume are to be keeped, the 'defaultColors' must be defined as : ```'defaultColors' : [] ```.
Each volume can only have one of each (color and opacity) transfer functions.
This parameter controls the two transfer functions of the principal volume.

##### Volume

```python
shadervParams = { '<name>' : { 'displayName' : '<display name>', 'defaultVolume' : <id of the volume>, 'transferFunctions' : {<transfer functions>}}, \
                  '<name>' : { ...}, \
                   ... }
```

If mutliple volumes are needed, make sure that the ids are differents. By default, you should use 1, 2, 3, ... as ids. If no transfer function are defined, the default ones of the volume will be used.


<a name="lim"></a>

### Limitations
