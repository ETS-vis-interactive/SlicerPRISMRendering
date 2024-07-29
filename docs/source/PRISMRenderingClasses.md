# PRISMRendering Classes
## PRISMRendering

**Description**: The PRISMRendering class extends the ScriptedLoadableModule class from 3D Slicer. This class represents the PRISM Rendering module.
The class is responsible for initializing the module, setting its properties (such as title, categories, dependencies, contributors), and registering sample data. It also contains metadata about the module, including help text and acknowledgment text.

## PRISMRenderingWidget

**Description**: The PRISMRenderingWidget class extends both ScriptedLoadableModuleWidget and VTKObservationMixin. This class handles the graphical user interface (GUI) for the PRISM Rendering module. It sets up the interface elements, connects user actions (like button clicks) to functions, and updates the interface based on the state of the module. The class ensures that the user can interact with the module effectively, providing a way to control and configure the rendering process.

## PRISMRenderingLogic

**Description**: This class extends ScriptedLoadableModuleLogic and encapsulates the core computational logic for the PRISM Rendering module in 3D Slicer. It is designed to be used by other Python code without requiring an instance of the user interface (Widget). The class is responsible for managing and processing volume data, applying custom shaders, and handling various rendering tasks. It also manages scene events and volume nodes to ensure that the rendering environment is properly set up and maintained.

## PRISMRenderingParams

**Description**: Shader parameter classes are specialized classes that represent different types of parameters used in PRISMRendering shaders. These classes manage the interaction between the user interface and the underlying shader logic, allowing users to customize the appearance and behavior of volume renderings.

### `Param`

 **Description**: The abstract base class for all shader parameters. Provides a common interface and basic functionality for shader parameters, ensuring consistency and enabling extensibility. It defines the basic methods and properties that all parameter classes must implement, such as setting and getting values, updating the GUI, and interfacing with the shader.

### `BoolParam`

 **Description**: Represents a boolean parameter for shaders. Manages a checkbox in the GUI, allowing users to enable or disable shader features. This class is useful for parameters that are either on or off, such as toggling the visibility of certain shader effects.


### `FloatParam`

 **Description**: Represents a float parameter for shaders. Manages a slider in the GUI, allowing users to adjust floating-point values within a specified range. This class is useful for fine-tuning shader effects that require a continuous range of values, such as adjusting brightness or intensity.

### `IntParam`

 **Description**: Represents an integer parameter for shaders. Manages a slider in the GUI, allowing users to adjust integer values within a specified range. This class is ideal for parameters that require discrete values, such as selecting a number of iterations or levels of detail.

### `FourFParam`

 **Description**: Represents a 4D vector parameter for shaders. Allows users to set four-component vector values, often used for complex shader parameters. This class is useful for parameters that require multiple values, such as position or color vectors.

### `RangeParam`

 **Description**: Represents a range parameter for shaders. Manages a range slider in the GUI, allowing users to set a minimum and maximum value for shader parameters. This class is particularly useful for parameters that define a range of values, such as thresholding or windowing operations.

### `TransferFunctionParam`

 **Description**: Represents a transfer function parameter for shaders. Manages a widget for defining transfer functions (color and opacity) used in volume rendering. This class allows users to customize the mapping of data values to visual properties, essential for visualizing complex volume data. It supports both color and opacity transfer functions, providing a flexible tool for enhancing volume renderings.

## PRISMRenderingPoints / CustomShaderPoints Class

 **Description**: Manages the interaction and placement of fiducial points in the 3D Slicer scene for custom shaders. This class is responsible for creating, updating, and managing the endpoints (fiducial points) used in custom shaders. 


## PRISMRenderingShaders

**Description**: This class manages the shaders created for PRISM rendering. More details of each shader can be found in the Tutorials section.