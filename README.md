# ANoobs Brres Material Tool (ABMatt)
This command line tool is for editing materials in _Brres_ files in _Mario Kart Wii_. 

## Installation
You can download one of the tagged releases, or install with python.
```
git clone https://github.com/Robert-N7/abmatt
cd abmatt
python setup.py install
```
You may need to run with root priveleges.

## Modes
ABMatt can be used 
* for quick command line edits, 
* running commands from file, and/or 
* running commands in interactive *shell* mode.

## Editing Capabilities
ABMatt supports editing the following types:
* materials
* layers
* shaders
* stages


## Command Line Usage
```
./abmatt.py -f <file> [-d <destination> -o -c <commandfile> -k <key> -v <value> -t <type> -n <name> -m <model> -i -s]
```
| Flag |Expanded| Description |
|---|---|---|
| -c | --commandfile | File with ABMatT commands to be processed as specified in file format. |
| -d | --destination | The file name to be written to. Mutliple destinations are not supported. |
| -f | --file | The brres file name to be read from |
| -h | --help | Displays a help message about program usage. |
| -i | --info | Information flag that generates additional informational output. |
| -k | --key | Setting key to be updated. See [File Format](## File Format) for keys. |
| -m | --model | The name of the model to search in. |
| -n | --name | Material or layer name or regular expression to be found. |
| -o | --overwrite | Overwrite existing files. The default is to not overwrite the input file or any other file unless this flag is used. |
| -s | --shell | Interactive shell mode. |
| -t | --type | Type (material, layer, shader, stage) |
| -v | --value | Setting value to be paired with a key. |

### Command Line Examples
This command would open *course_model.brres* in overwrite mode and run the commands stored in *my_commands.txt*
```
./abmatt.py -f course_model.brres -o -c my_commands.txt
```
This next command would enable xlu for all materials starting with the prefix xlu.
```
./abmatt.py -f course_model.brres -o -n xlu.* -k xlu -v true
```

## File Format
ABMatT supports reading in commands from files or in interactive mode which have a specified extended BNF format.
Parameters are delimited by spaces except where a ':' or ',' is specified. Case is insensitive for commands, keys, and values.
```
line = begin_preset | command;
begin_preset = '[' <preset_name> ']' EOL; 

command = (set | info | add | remove | select | preset) ['for' selection] EOL;
set   = 'set' type setting;
info  = 'info' type [key];
add   = 'add' type;
remove = 'remove' type;
select = 'select' selection;    Note: does not support 'for' selection clause
preset = 'preset' preset_name;

selection = name ['in' container]
container = ['file' filename] ['model' name];
type = 'material' | 'layer' [':' id] | 'shader' | 'stage' [':' id];

setting =  key ':' value; NOTE: No spaces allowed in key:value pairs
key = material-key | layer-key | shader-key | stage-key; 
value = material-value | layer-value | shader-value | stage-value | 'true' | 'false' | number-list;
number-list = number {,number}; 
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
shader-key = 'stagecount', 'texturerefcount' | 'indirectmap' [<n>] | 'indirectcoord' [<n>];
```
### Stage Keys
```
stage-key = 'enabled' | 'mapid' | 'coordinateid' | 'textureswapselection' |
   'rastercolor' | 'rasterswapselection' | 'colorconstantselection' |
   'colora' | 'colorb' | 'colorc' | 'colord' | 'colorbias' |
   'coloroperation' | 'colorclamp' | 'colorscale' | 'colordestination' |
   'alphaconstantselection' | 'alphaa' | 'alphab' | 'alphac' | 'alphad' |
   'alphabias' | 'alphaoperation' | 'alphaclamp' | 'alphascale' | 'alphadestination' | 'indirectstage' | 'indirectformat' | 'indirectalpha' | 'indirectbias' | 'indirectmatrix' | 'indirectswrap' | 'indirecttwrap' | 'indirectuseprevstage' | 'indirectunmodifiedlod';

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

### Example File Commands
Example file commands:
```
set xlu:true for xlu.* in model course      # Sets all materials in course starting with xlu to transparent
set scale:(1,1) for *                 # Sets the scale for all layers to 1,1
info layer:ef_arrowGradS        # Prints information about the layer 'ef_arrowGradS'
```

### Presets
Presets are a way of grouping commands together. They can be defined in `presets.txt` or in command files.
Presets begin with `[<preset_name>]` and include all commands until another preset is encountered or end of file. 
An empty preset `[]` can be used to stop preset parsing. An example preset is given named 'my_preset'.
```
[my_preset]
set material xlu:True
set layer scale:(1,1)
set layer mapmode:linear_mipmap_linear
```
Calling the preset:
`preset my_preset for my_material_name`