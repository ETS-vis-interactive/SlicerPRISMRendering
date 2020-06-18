from Resources.CustomShader import CustomShader

#------------------------------------------------------------------------------------
# Decluttering shader
#------------------------------------------------------------------------------------
class Decluttering(CustomShader):

  shaderfParams = {}
  shaderiParams = {}
  shader4fParams = {}
  shaderbParams = {}
  shaderrParams = {}
  shadertfParams = {}
  shadervParams = { 'bloodflow' : { 'displayName' : 'Blood Flow', 'defaultVolume' : 1, 'transferFunctions' : \
  { 'scalarColorMapping2' : { 'displayName' : 'Scalar Color Mapping second', 'defaultColors' : [[0, 0, 1, 0, 0, 0.5], [300, 1, 0, 0, 0, 0.5]], 'type' : 'color'},\
   'scalarOpacityMapping2' : { 'displayName' : 'Scalar Opacity Mapping second', 'defaultColors' : [], 'type' : 'scalarOpacity'}}}, \
     'bloodflow2' : { 'displayName' : 'Blood Flow2', 'defaultVolume' : 2, 'transferFunctions' : \
  { 'scalarColorMapping3' : { 'displayName' : 'Scalar Color Mapping third', 'defaultColors' : [[0, 0.8, 0.75, 0.8, 0, 0.5], [300, 1, 0, 0, 0, 0.5]], 'type' : 'color'},\
   'scalarOpacityMapping3' : { 'displayName' : 'Scalar Opacity Mapping third', 'defaultColors' : [], 'type' : 'scalarOpacity'}}}}
  
  def __init__(self, shaderPropertyNode):
    CustomShader.__init__(self,shaderPropertyNode)

  @classmethod
  def GetDisplayName(cls):
    return 'Decluttering'

  def setupShader(self):
    super(Decluttering,self).setupShader()
    self.shaderProperty.ClearAllFragmentShaderReplacements()
    #shaderreplacement
