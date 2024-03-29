# ANoobs Brres Material Tool (ABMatt)
This tool is used to convert and edit *Brres* files in *Mario Kart Wii*. 

## Installation
Compiled [releases](https://github.com/Robert-N7/abmatt/releases) are available for Linux and Windows.

Or, install as python package:
```
pip install git+https://github.com/Robert-N7/abmatt.git
```

## Dependencies
ABMatt uses [Wiimm's Image Tool](https://szs.wiimm.de/download.html) which must be installed on your system path.


## Modes
ABMatt has Gui and command-line capabilities.
* The Gui interface provides easy drag and drop interfacing.
* Text-based commands can be issued from the command line, interactive shell, or from file.

## Converting Capabilities
ABMatt supports converting to and from:
* Wavefront OBJ
* Collada DAE

When replacing an existing model, materials with matching names will take on the properties of the previous material.

## GUI Features
Materials can be dragged to replace existing materials.
The material is copied and pasted, which includes shader and animation data.
![Main Window](images/main_window.PNG)

## Command Line Usage
ABMatt supports a command line (see [FileFormat](##FileFormat)) followed by options.
```
abmatt [command_line][flags]
```
| Flag |Expanded| Description |
|---|---|---|
| -a | --auto-fix | Set the autofix level (0 to turn off fixes). |
| -b | --brres | Brres file selection. |
| -d | --destination | The file path to be written to. Multiple destinations are not supported. |
| -f | --file | File with ABMatt commands to be processed as specified in file format. |
| -h | --help | Displays a help message about program usage. |
| -i | --interactive | Interactive shell mode. |
| -l | --loudness | Sets the verbosity level. (0-5)
| -o | --overwrite | Overwrite existing files.  |
|   | --moonview | Treat the Brres as Moonview course, adjusting material names. |

### Command Line Examples
This command would open *course_model.brres* in overwrite mode and run the commands stored in *my_commands.txt*
```
abmatt -b course_model.brres -o -f my_commands.txt
```
This next command would enable xlu for all materials starting with the prefix xlu.
```
abmatt -b course_model.brres -o -n xlu.* -k xlu -v true
```

### Examples
Example command_line:
```
convert course_model.obj                    # Converts obj to brres 
set xlu:true for xlu.* in model course      # Sets all materials in course starting with xlu to transparent
set scale:(1,1) for *                       # Sets the scale for all layers to 1,1
info layer:ef_arrowGradS                    # Prints information about the layer 'ef_arrowGradS'
add tex0:ef_arrowGradS.png format:ia8       # Adds the image 'ef_arrowGradS.png' as a tex0 in ia8 format
```

## Copy/Paste
* Group copying matches selected items on their names.
* Single copying pastes over all selected without matching names.
* Names are not changed when pasting.
* Copying a material will copy all settings related to the material, including layers, shaders, and animations.

An example of pasting material data using a wildcard:
```
copy material for * in course_model.brres
paste material for * in new_model.brres
```  
An example of pasting a single material:
```
copy material for ef_dushBoard in course_model.brres
paste material for my_ramp in my_course.brres
```

## File Format
ABMatt supports reading in commands from files or in interactive mode which have a specified extended BNF format.
Parameters are delimited by spaces except where a ':' or ',' is specified. Case is insensitive for commands, keys, and values.
```
line = begin_preset | command_line;
begin_preset = '[' <preset_name> ']' EOL; 

command_line =  cmd-prefix ['for' selection] EOL;
cmd-prefix = set | info | add | remove | select | preset | save | copy | paste | convert | load;
set   = 'set' type setting;
info  = 'info' type [key | 'keys'];
add   = 'add' type;
remove = 'remove' type;
select = 'select' selection;
preset = 'preset' preset_name;
save = 'save' [filename] ['as' destination] ['overwrite']
copy = 'copy' type;
paste = 'paste' type;
convert = 'convert' filename ['to' destination] ['include' poly-list] ['exclude' poly-list] [convert-flags]
load = 'load' command-file

convert-flags = ['patch'] ['no-colors'] ['no-normals'] ['single-bone'] ['no-uvs']
poly-list = [polygon-name[,polygon-name]*]
selection = name ['in' container]
container = ['brres' filename] ['model' name];
type = 'material' | 'layer' [':' id] | 'shader' | 'stage' [':' id]
    | 'srt0' | 'srt0layer' [':' id] | 'pat0'
    | 'mdl0' [':' id] | 'tex0' [':' id] | 'brres';

setting =  key ':' value; NOTE: No spaces allowed in key:value pairs
key = material-key | layer-key | shader-key | stage-key
    | srt0-key | srt0-layer-key | pat0-key | tex0-key; 
value = material-value | layer-value | shader-value | stage-value
    |  srt0-value | srt0-layer-value | pat0-value | tex0-value; 
```

### Selection Explanation
In the selection process, 
* Selection narrows the search to the file(s) and model(s) if specified.
* Next, the \<name\> parameter matches against material names using direct and regex matching creating the current selection.
* Commands operate on the selection until specifying a new selection.

### Material Keys
```
material-key = 'layercount' | 'xlu' | 'ref0' | 'ref1' |
 'comp0' | 'comp1' | 'comparebeforetexture' | 'blend' |
 'blendsrc' | 'blendlogic' | 'blenddest' | 'constantalpha' |
 'cullmode' | 'shadercolor' | 'lightchannel' |
 'lightset' | 'fogset' | 'matrixmode' | 'enabledepthtest' |
 'enabledepthupdate' | 'depthfunction' | 'drawpriority';

blend-factor  = 'zero' | 'one' | 'sourcecolor' | 'inversesourcecolor'
    | 'sourcealpha' | 'inversesourcealpha' | 'destinationalpha' | 'inversedestinationalpha';
blend-logic   = 'clear' | 'and' | 'reverseand' | 'copy' | 'inverseand' | 'nooperation' | 'exclusiveor' 
    | 'or' | 'notor' | 'equivalent' | 'inverse' | 'reverseor' | 'inversecopy' | 'inverseor' | 'notand' | 'set';
cull-mode     = 'all' | 'inside' | 'outside' | 'none';
const-alpha   = 'enable' | 'disable' | number;
matrix-mode   = 'maya' | 'xsi' | '3dsmax';
comparison    = 'never' | 'less' | 'equal' | 'lessorequal' |  
    'greater' | 'notequal' | 'greaterorequal' | 'always';
shader-color = ['constant'] n ':' color;
light-channel = lc-flag | lc-color | lc-control;
lc-flag = ('material' | 'ambient' | 'raster')('color' | 'alpha') 'enable:' ('true' | 'false');
lc-color = ('material' | 'ambient') ['color'] ':' color;
lc-control = ('color' | 'alpha') 'control' 
    ('material' | 'ambient' | 'enable' | 'attenuation' | 'diffuse') ':' value
color = red ',' green ',' blue ',' alpha
```
### Layer Keys
```
layer-key = 'scale' | 'rotation' | 'translation' | 'scn0cameraref' |
  'scn0lightref' | 'mapmode' | 'uwrap' | 'vwrap' |    
  'minfilter' | 'magfilter' | 'lodbias' | 'anisotrophy' |
  'clampbias' | 'texelinterpolate' | 'projection' | 'inputform' |
  'type' | 'coordinates' | 'embosssource' | 'embosslight' |
  'normalize' | 'indirectmatrix';

wrap-mode     = 'clamp' | 'repeat' | 'mirror';
minFilter     = 'nearest' | 'linear' | 'nearest_mipmap_nearest' |
'linear_mipmap_nearest' | 'nearest_mipmap_linear' | 'linear_mipmap_linear';
map-mode      = 'texcoord' | 'envcamera' | 'projection' | 'envlight'  
| 'envspec';
projection    = 'st' | 'stq';
inputform     = 'ab11' | 'abc1';
type          = 'regular' | 'embossmap' | 'color0' | 'color1';
coordinates   = 'geometry' | 'normals' | 'colors' | 'binfileormalst' |    
'binfileormalsb' | 'texcoord0' | 'texcoord1' | 'texcoord2' | 'texcoord3'  | 'texcoord4' | 'texcoord5' | 'texcoord6' | 'texcoord7';

```
### Shader Keys
```
shader-key = 'stagecount' | 'indirectmap' [<n>] | 'indirectcoord' [<n>] | 'indirectmap' [<n>];
```
### Stage Keys
```
stage-key = 'enabled' | 'mapid' | 'coordinateid' | 'textureswapselection' |
   'rastercolor' | 'rasterswapselection' | 'colorconstantselection' |
   'colora' | 'colorb' | 'colorc' | 'colord' | 'colorbias' |
   'coloroperation' | 'colorclamp' | 'colorscale' | 'colordestination' |
   'alphaconstantselection' | 'alphaa' | 'alphab' | 'alphac' | 'alphad' |
   'alphabias' | 'alphaoperation' | 'alphaclamp' | 'alphascale' | 'alphadestination' | 
   'indirectstage' | 'indirectformat' | 'indirectalpha' | 'indirectbias' | 
   'indirectmatrixselection' | 'indirectswrap' | 'indirecttwrap' | 'indirectuseprevstage' | 'indirectunmodifiedlod';

RASTER_COLORS = 'lightchannel0' | 'lightchannel1' | 'bumpalpha' | 'normalizedbumpalpha' | 'zero';
COLOR_CONSTANTS = '1_1' | '7_8' | '3_4' | '5_8' | '1_2' | '3_8' | '1_4' | '1_8' |
                   'color0_rgb' | 'color1_rgb' | 'color2_rgb' | 'color3_rgb' |
                   'color0_rrr' | 'color1_rrr' | 'color2_rrr' | 'color3_rrr' |
                   'color0_ggg' | 'color1_ggg' | 'color2_ggg' | 'color3_ggg' |
                   'color0_bbb' | 'color1_bbb' | 'color2_bbb' | 'color3_bbb' |
                   'color0_aaa' | 'color1_aaa' | 'color2_aaa' | 'color3_aaa';
COLOR_SELS = 'outputcolor' | 'outputalpha' | 'color0' | 'alpha0' | 'color1' |
              'alpha1' | 'color2' | 'alpha2' | 'texturecolor' | 'texturealpha' |
              'rastercolor' | 'rasteralpha' | 'one' | 'half' |
              'colorselection' | 'zero';
BIAS = 'zero' | 'addhalf' | 'subhalf';
OPER = 'add' | 'subtract';
SCALE = 'multiplyby1' | 'multiplyby2' | 'multiplyby4' | 'divideby2' | number;
COLOR_DEST = 'outputcolor' | 'color0' | 'color1' | 'color2';

ALPHA_CONSTANTS = '1_1' | '7_8' | '3_4' | '5_8' | '1_2' | '3_8' | '1_4' | '1_8' |
                   'color0_red' | 'color1_red' | 'color2_red' | 'color3_red' |
                   'color0_green' | 'color1_green' | 'color2_green' | 'color3_green' |
                   'color0_blue' | 'color1_blue' | 'color2_blue' | 'color3_blue' |
                   'color0_alpha' | 'color1_alpha' | 'color2_alpha' | 'color3_alpha';
ALPHA_SELS = 'outputalpha' | 'alpha0' | 'alpha1' | 'alpha2' | 'texturealpha' |
              'rasteralpha' | 'alphaselection' | 'zero';
ALPHA_DEST = 'outputalpha' | 'alpha0' | 'alpha1' | 'alpha2';

TEX_FORMAT = 'f_8_bit_offsets' | 'f_5_bit_offsets' | 'f_4_bit_offsets' | 'f_3_bit_offsets';
IND_BIAS = 'none' | 's' | 't' | 'st' | 'u' | 'su' | 'tu' | 'stu';
IND_ALPHA = 'off' | 's' | 't' | 'u';
IND_MATRIX = 'nomatrix' | 'matrix0' | 'matrix1' | 'matrix2' | 'matrixs0' |
              'matrixs1' | 'matrixs2' | 'matrixt0' | 'matrixt1' | 'matrixt2';
WRAP = 'nowrap' | 'wrap256' | 'wrap128' | 'wrap64' | 'wrap16' | 'wrap0'; 
```

### SRT0 Keys
```
srt0-keys = 'framecount' | 'loop' | 'layerenable'
srt0-layer-enable = id ':' ('true' | 'false') 
```
### SRT0 Layer Keys
```
srt0-layer-keys = 'xscale' | 'yscale' | 'rot' | 'xtranslation' | 'ytranslation';
srt0-layer-values = 'disabled' | key-frame-list;
key-frame-list = key-frame-index ':' value {',' key-frame ':' value};
```

### PAT0 Keys
```
pat0-keys = 'framecount' | 'loop' | 'keyframe';
pat0-keyframe = key-frame-list;
```

### TEX0 Keys
```
tex0-keys = 'dimensions' | 'format' | 'mipmamcount' | 'name';
tex0-dimension = width ',' height;
tex0-format = 'cmpr' | 'c14x2' | 'c8' | 'c4' | 'rgba32' | 'rgb5a3' | 'rgb565' 
            | 'ia8' | 'ia4' | 'i8' | 'i4';
```
## Convert Examples
Convert `course_model.brres` to a Dae file
```
convert course_model.brres to course_model.dae
```

Convert `course_model.dae` to a Brres file, excluding polygons `road` and `boost`, and renaming materials to satisfy 
Moonview Highway conditions:
```
convert course_model.dae to course_model.brres exclude road,boost --moonview
```

Convert `course_model.dae` patching over _only_ the `road` and `boost` polygons while keeping the existing model intact.
```
convert course_model.dae to course_model.brres include road,boost --patch
```

### Presets and Command Files
Presets are a way of grouping commands together. They can be defined in `presets.txt` or in command files.
Presets begin with `[<preset_name>]` and include all commands until another preset is encountered or end of file. 
An empty preset `[]` can be used to stop preset parsing (and begin command parsing).
```
[my_preset]
set material xlu:True
set layer scale:(1,1)
set layer mapmode:linear_mipmap_linear
```
To call the preset:
`preset my_preset for my_material_name`

The `load` command can be used to load additional commands and presets. 
As with all recursive things, be careful not to create an infinite loop!

## Additional Configuration
[An example configuration](etc/abmatt/config.conf)

# Contributing
Contributions are welcome! Feel free to submit a pull request.


## Known Limitations and Bugs
* Windows installer sometimes hangs in the background until the process is terminated.
* Non-standard files in Brres are not supported.