from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Sphere carving shader
#------------------------------------------------------------------------------------
class SphereCarvingShader(CustomShader):

  shaderParams = { 'radius' : { 'displayName' : 'Radius', 'min' : 0.0, 'max' : 100.0, 'defaultValue' : 50.0 }, \
                   'x' :  {'displayName' : 'X', 'min' : -100.0, 'max' : 100.0, 'defaultValue' : 0.0 }, \
                   'y' :  {'displayName' : 'Y', 'min' : -100.0, 'max' : 100.0, 'defaultValue' : 0.0 }, \
                   'z' :  {'displayName' : 'Z', 'min' : -100.0, 'max' : 100.0, 'defaultValue' : 0.0 } 
  }

  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Sphere Carving'

  def setupShader(self):
    super(SphereCarvingShader,self).setupShader()
    self.shaderUniforms.SetUniformf("x",  self.paramValues['x'])
    self.shaderUniforms.SetUniformf("y",  self.paramValues['y'])
    self.shaderUniforms.SetUniformf("z",  self.paramValues['z'])

    self.shaderUniforms.SetUniformf("radius", self.paramValues['radius'])
    replacement = """
      vec3 center = vec3(x, y, z);
      vec4 texCoordRAS = in_volumeMatrix[0] * in_textureDatasetMatrix[0]  * vec4(g_dataPos, 1.);
      g_skip = length(texCoordRAS.xyz - center) < radius;
    """
    # (bool) Skip computation of current iteration step if true
    self.shaderProperty.AddFragmentShaderReplacement("//VTK::Cropping::Impl", True, replacement, False)

  def setPathEnds(self,entry,target):
    self.shaderUniforms.SetUniform3f("center", entry)