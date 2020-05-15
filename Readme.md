# ANoobs Brres Material Tool (ABMatT)
This command line tool is for editing materials in _Brres_ files in _Mario Kart Wii_. Python is required to run it.
## Command Line Options
Todo: Some text here
## File Format
ABMatT supports reading in external commands from files which have a specified extended BNF format.
```
command   = 'Set' space key ':' value  [space 'for' space name] [space 'in' space container] EOL;
key   = 'xlu' | 'transparent' | 'ref0' | 'ref1' |
  'comp0' | 'comp1' | 'comparebeforetexture' | 'blend' |
  'blendsrc' | 'blendlogic' | 'blenddest' | 'constantalpha' |
  'cullmode' | 'shader' | 'shadercolor' | 'lightchannel' |
  'lightset' | 'fogset' | 'matrixmode' | 'enabledepthtest' |
  'enabledepthupdate' | 'depthfunction' | 'drawpriority' |
  'scale' | 'rotation' | 'translation' | 'scn0cameraref' |
  'scn0lightref' | 'mapmode' | 'uwrap' | 'vwrap' |    
  'minfilter' | 'magfilter' | 'lodbias' | 'anisotrophy' |
  'clampbias' | 'texelinterpolate' | 'projection' | 'inputform' |
  'type' | 'coordinates' | 'embosssource' | 'embosslight' |
  'normalize';
value     = 'true' | 'false' | number-list | cull-mode | light-channel | const-alpha | matrix-mode | blend-logic | blend-factor | wrap-mode | minfilter | map-mode | projection | inputform | type | coordinates;
  number-list   = number {, number};
  cull-mode     = 'all' | 'inside' | 'outside' | 'none';
  light-channel = 'vertex' | 'ambient';
  const-alpha   = 'enable' | 'disable' | number;
  matrix-mode   = 'maya' | 'xsi' | '3dsmax';
  comparison    = 'never' | 'less' | 'equal' | 'lessorequal' |  
    'greater' | 'notequal' | 'greaterorequal' | 'always';
  blend-logic   = 'clear' | 'and' | 'reverseand' | 'copy' |
    'inverseand' | 'nooperation' | 'exclusiveor' | 'or' | 'notor' | 'equivalent' | 'inverse' | 'reverseor' | 'inversecopy' | 'inverseor' | 'notand' | 'set';
  blend-factor  = 'zero' | 'one' | 'sourcecolor' | 'inversesourcecolor'
    | 'sourcealpha' | 'inversesourcealpha' | 'destinationalpha' | 'inversedestinationalpha';
  wrap-mode     = 'clamp' | 'repeat' | 'mirror';
  minFilter     = 'nearest' | 'linear' | 'nearest_mipmap_nearest' |
    'linear_mipmap_nearest' | 'nearest_mipmap_linear' | 'linear_mipmap_linear';
  map-mode      = 'texcoord' | 'envcamera' | 'projection' | 'envlight'  
    | 'envspec';
  projection    = 'st' | 'stq';
  inputform     = 'ab11' | 'abc1';
  type          = 'regular' | 'embossmap' | 'color0' | 'color1';
  coordinates   = 'geometry' | 'normals' | 'colors' | 'binormalst' |    
    'binormalsb' | 'texcoord0' | 'texcoord1' | 'texcoord2' | 'texcoord3'  | 'texcoord4' | 'texcoord5' | 'texcoord6' | 'texcoord7';

container = ['file' space filename] ['model' space name] ['material' space name];
name      = string | regex {',' space string | regex};
space     = ? US-ASCII character 32 ?;
EOL       = [\r] \n | EOF;
```
