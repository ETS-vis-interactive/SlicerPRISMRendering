#version 150
#ifdef GL_ES
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
precision highp sampler2D;
precision highp sampler3D;
#else
precision mediump float;
precision mediump sampler2D;
precision mediump sampler3D;
#endif
#define texelFetchBuffer texelFetch
#define texture1D texture
#define texture2D texture
#define texture3D texture
#else // GL_ES
#define highp
#define mediump
#define lowp
#if __VERSION__ == 150
#define texelFetchBuffer texelFetch
#define texture1D texture
#define texture2D texture
#define texture3D texture
#endif
#endif // GL_ES
#define varying in


/*=========================================================================

  Program:   Visualization Toolkit
  Module:    raycasterfs.glsl

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/

//////////////////////////////////////////////////////////////////////////////
///
/// Inputs
///
//////////////////////////////////////////////////////////////////////////////

/// 3D texture coordinates form vertex shader
in vec3 ip_textureCoords;
in vec3 ip_vertexPos;

//////////////////////////////////////////////////////////////////////////////
///
/// Outputs
///
//////////////////////////////////////////////////////////////////////////////

vec4 g_fragColor = vec4(0.0);

//////////////////////////////////////////////////////////////////////////////
///
/// Uniforms, attributes, and globals
///
//////////////////////////////////////////////////////////////////////////////
vec3 g_dirStep;
vec4 g_srcColor;
vec4 g_eyePosObj;
bool g_exit;
bool g_skip;
float g_currentT;
float g_terminatePointMax;

// These describe the entire ray for this scene, not just the current depth
// peeling segment. These are texture coordinates.
vec3 g_rayOrigin; // Entry point of volume or clip point
vec3 g_rayTermination; // Termination point (depth, clip, etc)

// These describe the current segment. If not peeling, they are initialized to
// the ray endpoints.
vec3 g_dataPos;
vec3 g_terminatePos;



out vec4 fragOutput0;


uniform sampler3D in_volume[1];
uniform vec4 in_volume_scale[1];
uniform vec4 in_volume_bias[1];
uniform int in_noOfComponents;
uniform int in_independentComponents;

uniform sampler2D in_noiseSampler;
#ifndef GL_ES
uniform sampler2D in_depthSampler;
#endif

// Camera position
uniform vec3 in_cameraPos;
uniform mat4 in_volumeMatrix[1];
uniform mat4 in_inverseVolumeMatrix[1];
uniform mat4 in_textureDatasetMatrix[1];
uniform mat4 in_inverseTextureDatasetMatrix[1];
uniform mat4 in_textureToEye[1];
uniform vec3 in_texMin[1];
uniform vec3 in_texMax[1];
uniform mat4 in_cellToPoint[1];
// view and model matrices
uniform mat4 in_projectionMatrix;
uniform mat4 in_inverseProjectionMatrix;
uniform mat4 in_modelViewMatrix;
uniform mat4 in_inverseModelViewMatrix;
in mat4 ip_inverseTextureDataAdjusted;

// Ray step size
uniform vec3 in_cellStep[1];
uniform vec2 in_scalarsRange[4];
uniform vec3 in_cellSpacing[1];

// Sample distance
uniform float in_sampleDistance;

// Scales
uniform vec2 in_windowLowerLeftCorner;
uniform vec2 in_inverseOriginalWindowSize;
uniform vec2 in_inverseWindowSize;
uniform vec3 in_textureExtentsMax;
uniform vec3 in_textureExtentsMin;

// Material and lighting
uniform vec3 in_diffuse[4];
uniform vec3 in_ambient[4];
uniform vec3 in_specular[4];
uniform float in_shininess[4];

// Others
uniform bool in_useJittering;
vec3 g_rayJitter = vec3(0.0);

uniform vec2 in_averageIPRange;
uniform bool in_twoSidedLighting;
uniform vec3 in_lightAmbientColor[1];
uniform vec3 in_lightDiffuseColor[1];
uniform vec3 in_lightSpecularColor[1];
vec4 g_lightPosObj;
vec3 g_ldir;
vec3 g_vdir;
vec3 g_h;


      
 const float g_opacityThreshold = 1.0 - 1.0 / 255.0;











//VTK::GradientCache::Dec

//VTK::Transfer2D::Dec

uniform sampler2D in_opacityTransferFunc_0[1];
        
float computeOpacity(vec4 scalar)        
{        
  return texture2D(in_opacityTransferFunc_0[0], vec2(scalar.w, 0)).r;        
}

// c is short for component
vec4 computeGradient(in vec3 texPos, in int c, in sampler3D volume,in int index)
{
  // Approximate Nabla(F) derivatives with central differences.
  vec3 g1; // F_front
  vec3 g2; // F_back
  vec3 xvec = vec3(in_cellStep[index].x, 0.0, 0.0);
  vec3 yvec = vec3(0.0, in_cellStep[index].y, 0.0);
  vec3 zvec = vec3(0.0, 0.0, in_cellStep[index].z);
  vec3 texPosPvec[3];
  texPosPvec[0] = texPos + xvec;
  texPosPvec[1] = texPos + yvec;
  texPosPvec[2] = texPos + zvec;
  vec3 texPosNvec[3];
  texPosNvec[0] = texPos - xvec;
  texPosNvec[1] = texPos - yvec;
  texPosNvec[2] = texPos - zvec;
  g1.x = texture3D(volume, vec3(texPosPvec[0]))[c];
  g1.y = texture3D(volume, vec3(texPosPvec[1]))[c];
  g1.z = texture3D(volume, vec3(texPosPvec[2]))[c];
  g2.x = texture3D(volume, vec3(texPosNvec[0]))[c];
  g2.y = texture3D(volume, vec3(texPosNvec[1]))[c];
  g2.z = texture3D(volume, vec3(texPosNvec[2]))[c];

  // Apply scale and bias to the fetched values.
  g1 = g1 * in_volume_scale[index][c] + in_volume_bias[index][c];
  g2 = g2 * in_volume_scale[index][c] + in_volume_bias[index][c];

  // Scale values the actual scalar range.
  float range = in_scalarsRange[c][1] - in_scalarsRange[c][0];
  g1 = in_scalarsRange[c][0] + range * g1;
  g2 = in_scalarsRange[c][0] + range * g2;

  // Central differences: (F_front - F_back) / 2h
  g2 = g1 - g2;

  float avgSpacing = (in_cellSpacing[index].x +
   in_cellSpacing[index].y + in_cellSpacing[index].z) / 3.0;
  vec3 aspect = in_cellSpacing[index] * 2.0 / avgSpacing;
  g2 /= aspect;
  float grad_mag = length(g2);

  // Handle normalizing with grad_mag == 0.0
  g2 = grad_mag > 0.0 ? normalize(g2) : vec3(0.0);

  // Since the actual range of the gradient magnitude is unknown,
  // assume it is in the range [0, 0.25 * dataRange].
  range = range != 0 ? range : 1.0;
  grad_mag = grad_mag / (0.25 * range);
  grad_mag = clamp(grad_mag, 0.0, 1.0);

  return vec4(g2.xyz, grad_mag);
}


uniform sampler2D in_gradientTransferFunc_0[1];
        
float computeGradientOpacity(vec4 grad)        
  {        
  return texture2D(in_gradientTransferFunc_0[0], vec2(grad.w, 0.0)).r;        
  }

      
vec4 computeLighting(vec4 color, int component)      
  {      
  vec4 finalColor = vec4(0.0);  // Compute gradient function only once
  vec4 gradient = computeGradient(g_dataPos, component, in_volume[0], 0);

  finalColor = vec4(color.rgb, 0.0);          
  if (gradient.w >= 0.0)          
    {          
    color.a = color.a *          
              computeGradientOpacity(gradient);          
    }      
  finalColor.a = color.a;      
  return finalColor;      
  }

uniform sampler2D in_colorTransferFunc_0[1];
          
vec4 computeColor(vec4 scalar, float opacity)          
  {          
  return computeLighting(vec4(texture2D(in_colorTransferFunc_0[0],          
                         vec2(scalar.w, 0.0)).xyz, opacity), 0);          
  }

        
vec3 computeRayDirection()        
  {        
  return normalize(ip_vertexPos.xyz - g_eyePosObj.xyz);        
  }

//VTK::Picking::Dec

//VTK::RenderToImage::Dec

//VTK::DepthPeeling::Dec

uniform float in_scale;
uniform float in_bias;

//////////////////////////////////////////////////////////////////////////////
///
/// Helper functions
///
//////////////////////////////////////////////////////////////////////////////

/**
 * Transform window coordinate to NDC.
 */
vec4 WindowToNDC(const float xCoord, const float yCoord, const float zCoord)
{
  vec4 NDCCoord = vec4(0.0, 0.0, 0.0, 1.0);

  NDCCoord.x = (xCoord - in_windowLowerLeftCorner.x) * 2.0 *
    in_inverseWindowSize.x - 1.0;
  NDCCoord.y = (yCoord - in_windowLowerLeftCorner.y) * 2.0 *
    in_inverseWindowSize.y - 1.0;
  NDCCoord.z = (2.0 * zCoord - (gl_DepthRange.near + gl_DepthRange.far)) /
    gl_DepthRange.diff;

  return NDCCoord;
}

/**
 * Transform NDC coordinate to window coordinates.
 */
vec4 NDCToWindow(const float xNDC, const float yNDC, const float zNDC)
{
  vec4 WinCoord = vec4(0.0, 0.0, 0.0, 1.0);

  WinCoord.x = (xNDC + 1.f) / (2.f * in_inverseWindowSize.x) +
    in_windowLowerLeftCorner.x;
  WinCoord.y = (yNDC + 1.f) / (2.f * in_inverseWindowSize.y) +
    in_windowLowerLeftCorner.y;
  WinCoord.z = (zNDC * gl_DepthRange.diff +
    (gl_DepthRange.near + gl_DepthRange.far)) / 2.f;

  return WinCoord;
}

/**
 * Clamps the texture coordinate vector @a pos to a new position in the set
 * { start + i * step }, where i is an integer. If @a ceiling
 * is true, the sample located further in the direction of @a step is used,
 * otherwise the sample location closer to the eye is used.
 * This function assumes both start and pos already have jittering applied.
 */
vec3 ClampToSampleLocation(vec3 start, vec3 step, vec3 pos, bool ceiling)
{
  vec3 offset = pos - start;
  float stepLength = length(step);

  // Scalar projection of offset on step:
  float dist = dot(offset, step / stepLength);
  if (dist < 0.) // Don't move before the start position:
  {
    return start;
  }

  // Number of steps
  float steps = dist / stepLength;

  // If we're reeaaaaallly close, just round -- it's likely just numerical noise
  // and the value should be considered exact.
  if (abs(mod(steps, 1.)) > 1e-5)
  {
    if (ceiling)
    {
      steps = ceil(steps);
    }
    else
    {
      steps = floor(steps);
    }
  }
  else
  {
    steps = floor(steps + 0.5);
  }

  return start + steps * step;
}

//////////////////////////////////////////////////////////////////////////////
///
/// Ray-casting
///
//////////////////////////////////////////////////////////////////////////////

/**
 * Global initialization. This method should only be called once per shader
 * invocation regardless of whether castRay() is called several times (e.g.
 * vtkDualDepthPeelingPass). Any castRay() specific initialization should be
 * placed within that function.
 */
void initializeRayCast()
{
  /// Initialize g_fragColor (output) to 0
  g_fragColor = vec4(0.0);
  g_dirStep = vec3(0.0);
  g_srcColor = vec4(0.0);
  g_exit = false;

          
  // Get the 3D texture coordinates for lookup into the in_volume dataset        
  g_rayOrigin = ip_textureCoords.xyz;        
        
  // Eye position in dataset space        
  g_eyePosObj = in_inverseVolumeMatrix[0] * vec4(in_cameraPos, 1.0);        
        
  // Getting the ray marching direction (in dataset space);        
  vec3 rayDir = computeRayDirection();        
        
  // Multiply the raymarching direction with the step size to get the        
  // sub-step size we need to take at each raymarching step        
  g_dirStep = (ip_inverseTextureDataAdjusted *        
              vec4(rayDir, 0.0)).xyz * in_sampleDistance;        
        
  // 2D Texture fragment coordinates [0,1] from fragment coordinates.        
  // The frame buffer texture has the size of the plain buffer but         
  // we use a fraction of it. The texture coordinate is less than 1 if        
  // the reduction factor is less than 1.        
  // Device coordinates are between -1 and 1. We need texture        
  // coordinates between 0 and 1. The in_depthSampler        
  // buffer has the original size buffer.        
  vec2 fragTexCoord = (gl_FragCoord.xy - in_windowLowerLeftCorner) *        
                      in_inverseWindowSize;        
        
  if (in_useJittering)        
  {        
    float jitterValue = texture2D(in_noiseSampler, gl_FragCoord.xy / textureSize(in_noiseSampler, 0)).x;        
    g_rayJitter = g_dirStep * jitterValue;        
  }        
  else        
  {        
    g_rayJitter = g_dirStep;        
  }        
  g_rayOrigin += g_rayJitter;        
        
  // Flag to deternmine if voxel should be considered for the rendering        
  g_skip = false;

  

        
  // Flag to indicate if the raymarch loop should terminate       
  bool stop = false;      
      
  g_terminatePointMax = 0.0;      
      
#ifdef GL_ES      
  vec4 l_depthValue = vec4(1.0,1.0,1.0,1.0);      
#else      
  vec4 l_depthValue = texture2D(in_depthSampler, fragTexCoord);      
#endif      
  // Depth test      
  if(gl_FragCoord.z >= l_depthValue.x)      
    {      
    discard;      
    }      
      
  // color buffer or max scalar buffer have a reduced size.      
  fragTexCoord = (gl_FragCoord.xy - in_windowLowerLeftCorner) *      
                 in_inverseOriginalWindowSize;      
      
  // Compute max number of iterations it will take before we hit      
  // the termination point      
      
  // Abscissa of the point on the depth buffer along the ray.      
  // point in texture coordinates      
  vec4 rayTermination = WindowToNDC(gl_FragCoord.x, gl_FragCoord.y, l_depthValue.x);      
      
  // From normalized device coordinates to eye coordinates.      
  // in_projectionMatrix is inversed because of way VT      
  // From eye coordinates to texture coordinates      
  rayTermination = ip_inverseTextureDataAdjusted *      
                    in_inverseVolumeMatrix[0] *      
                    in_inverseModelViewMatrix *      
                    in_inverseProjectionMatrix *      
                    rayTermination;      
  g_rayTermination = rayTermination.xyz / rayTermination.w;      
      
  // Setup the current segment:      
  g_dataPos = g_rayOrigin;      
  g_terminatePos = g_rayTermination;      
      
  g_terminatePointMax = length(g_terminatePos.xyz - g_dataPos.xyz) /      
                        length(g_dirStep);      
  g_currentT = 0.0;

  

  //VTK::RenderToImage::Init

  //VTK::DepthPass::Init
}

/**
 * March along the ray direction sampling the volume texture.  This function
 * takes a start and end point as arguments but it is up to the specific render
 * pass implementation to use these values (e.g. vtkDualDepthPeelingPass). The
 * mapper does not use these values by default, instead it uses the number of
 * steps defined by g_terminatePointMax.
 */
vec4 castRay(const float zStart, const float zEnd)
{
  //VTK::DepthPeeling::Ray::Init

  

  //VTK::DepthPeeling::Ray::PathCheck

  

  /// For all samples along the ray
  while (!g_exit)
  {
          
    g_skip = false;

    
      print("ok");
    

    

    

    //VTK::PreComputeGradients::Impl

          
    if (!g_skip)      
      {      
      vec4 scalar = texture3D(in_volume[0], g_dataPos);        
      scalar.r = scalar.r * in_volume_scale[0].r + in_volume_bias[0].r;        
      scalar = vec4(scalar.r);             
      g_srcColor = vec4(0.0);             
      g_srcColor.a = computeOpacity(scalar);             
      if (g_srcColor.a > 0.0)             
        {             
        g_srcColor = computeColor(scalar, g_srcColor.a);           
        // Opacity calculation using compositing:           
        // Here we use front to back compositing scheme whereby           
        // the current sample value is multiplied to the           
        // currently accumulated alpha and then this product           
        // is subtracted from the sample value to get the           
        // alpha from the previous steps. Next, this alpha is           
        // multiplied with the current sample colour           
        // and accumulated to the composited colour. The alpha           
        // value from the previous steps is then accumulated           
        // to the composited colour alpha.           
        g_srcColor.rgb *= g_srcColor.a;           
        g_fragColor = (1.0f - g_fragColor.a) * g_srcColor + g_fragColor;             
        }      
      }

    //VTK::RenderToImage::Impl

    //VTK::DepthPass::Impl

    /// Advance ray
    g_dataPos += g_dirStep;

          
    if(any(greaterThan(g_dataPos, in_texMax[0])) ||      
      any(lessThan(g_dataPos, in_texMin[0])))      
      {      
      break;      
      }      
      
    // Early ray termination      
    // if the currently composited colour alpha is already fully saturated      
    // we terminated the loop or if we have hit an obstacle in the      
    // direction of they ray (using depth buffer) we terminate as well.      
    if((g_fragColor.a > g_opacityThreshold) ||       
       g_currentT >= g_terminatePointMax)      
      {      
      break;      
      }      
    ++g_currentT;
  }

  

  return g_fragColor;
}

/**
 * Finalize specific modes and set output data.
 */
void finalizeRayCast()
{
  

  

  

  

  //VTK::Picking::Exit

  g_fragColor.r = g_fragColor.r * in_scale + in_bias * g_fragColor.a;
  g_fragColor.g = g_fragColor.g * in_scale + in_bias * g_fragColor.a;
  g_fragColor.b = g_fragColor.b * in_scale + in_bias * g_fragColor.a;
  fragOutput0 = g_fragColor;

  //VTK::RenderToImage::Exit

  //VTK::DepthPass::Exit
}

//////////////////////////////////////////////////////////////////////////////
///
/// Main
///
//////////////////////////////////////////////////////////////////////////////
void main()
{
      
  initializeRayCast();    
  castRay(-1.0, -1.0);    
  finalizeRayCast();
}