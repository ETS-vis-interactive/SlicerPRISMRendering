from PRISMRenderingShaders.CustomShader import CustomShader

"""SphereCarvingShader Class containing the code for the Sphere Carving shader.

:param CustomShader:  Parent class containing the function to access the parameters of the shader. 
:type CustomShader: class.
""" 
class SphereCarvingShader(CustomShader):

  shaderfParams = { 'radius' : { 'displayName' : 'Radius', 'min' : 0.0, 'max' : 100.0, 'defaultValue' : 50.0 }}  
  shader4fParams = {'center': {'displayName': 'Center', 'defaultValue': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 0.0}}}
  def __init__(self, shaderPropertyNode, volumeNode = None):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Sphere Carving'

  def setupShader(self):
    super(SphereCarvingShader,self).setupShader()

    self.shaderUniforms.SetUniformf("radius", self.paramfValues['radius'])
    replacement = """
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      g_skip = length(texCoordRAS.xyz - center.xyz) < radius;
    """
    # (bool) Skip computation of current iteration step if true
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)
    #shaderreplacement