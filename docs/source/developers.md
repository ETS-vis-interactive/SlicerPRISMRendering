# Information for Developers

See [this page](https://githubcomets-vis-interactiveSlicerPRISMRenderingrendering.readthedocs.io/en/latest/code.html) for the full code documentation.

<a name="howto"></a>

## How Tos

### Create a shader 

Each of the volume rendering techniques is containted into one Python file and the GLSL code must be specified in the ```setupShader()``` method of the class.
This code must be written as a string which is transmitted to the shader carrying out the volume rendering by using the vtk shader modification classes [vtkUniforms](https://vtk.org/doc/nightly/html/classvtkUniforms.html) and [vtkShaderProperty](https://vtk.org/doc/nightly/html/classvtkShaderProperty.html). These strings replace on the fly tags in the format //VTK::SomeConcept::SomeAction in a shader template file. There is a defined list of tags that are suitable for different uses and the appropriate tag for the part of code you want to change in the shader must be specified in the Python class, as well as with the character string containing the code to replace. A more complete description of these tags can be found [here](https://kitware.github.io/vtk-js/api/Rendering_OpenGL_glsl.html). This is done in the following form:

``` python
replacement_code = """GLSL code"""
shader.AddFragmentShaderReplacement ("//VTK::SomeConcept::SomeAction", replacement_code)
```

Multiple tags can be used for one shader and they should all be specified in the ```setupShader()``` method.

The uniforms variables of the shader are defined as Python dictionnary and must be specified after the class declaration. There are 7 types of variables that can be added to the shader and they must respect this format, where \<name\> is the name used in the shader and \<display name\> is the name displayed in the UI :

#### Float

```python
shaderfParams = { '<name>' : { 'displayName' : '<display name>', 'min' : <minimum value>, 'max' : <maximum value>, 'defaultValue' : <default value>}, \
                  '<name>' : { ...}, \
                   ... }
```

#### Integer

```python
shaderiParams = { '<name>' : { 'displayName' : '<display name>', 'min' : <minimum value>, 'max' : <maximum value>, 'defaultValue' : <default value>}, \
                  '<name>' : { ...}, \
                   ... }
```

#### Point

```python
shader4fParams = { '<name>': {'displayName': '<display name>', 'defaultValue': {'x': <x value>, 'y': <y value>, 'z': <z value>, 'w': <w value>}}, \
                   '<name>' : { ...}, \
                    ... }
```
#### Boolean

```python
shaderbParams = { '<name>' : { 'displayName' : '<display name>', 'defaultValue' : <default value>, 'optionalWidgets' : [<name of optional parameter>, ...]}, \
                  '<name>' : { ...}, \
                   ... }
```

#### Range

```python
shaderrParams = { '<name>' : { 'displayName' : '<display name>', 'defaultValue' : [<minimum value>, <maximum value>]}, \
                  '<name>' : { ...}, \
                   ... }
```

#### Transfer functions

```python
shadertfParams = { '<name>' : { 'displayName' : '<display name>', 'defaultColors' : [[<First point x value>, <First point red value>, <First point green value>, <First point blue value>, <First point midpoint value>, <First point midpoint s Sharpness value> if color; <First point x value>, <First point opacity value>, <First point midpoint value>, <First point midpoint s sharpness value> if scalar opacity], ...], 'type' : '<'color' or 'scalarOpacity'>'}, \
                  '<name>' : { ...}, \
                   ... }
``` 

If the original values of the volume are to be keeped, the 'defaultColors' must be defined as : ```'defaultColors' : [] ```.
Each volume can only have one of each (color and opacity) transfer functions.
This parameter controls the two transfer functions of the principal volume.

#### Volume

```python
shadervParams = { '<name>' : { 'displayName' : '<display name>', 'defaultVolume' : <id of the volume>, 'transferFunctions' : {<transfer functions>}}, \
                  '<name>' : { ...}, \
                   ... }
```

If mutliple volumes are needed, make sure that the ids are differents. By default, you should use 1, 2, 3, ... as ids. If no transfer function are defined, the default ones of the volume will be used.


<a name="lim"></a>

## Limitations
