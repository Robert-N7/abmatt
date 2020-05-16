# Notes on shader offsets
| Offset | Size | Description |  
|---|---|---|
| 0x00 | 4 | Length|
| 0x04 | 4 | mdl0offset |
| 0x08 | 4 | shaderIndex |
| 0x0C | 1 | Number of stages |
| 0x0D | 3 | res |
| 0x10 | 8 | Texture Reference index enabled (ordered, 0xff for disabled)
| 0x18 | 8 | padding |
| 0x20 | 80 | 8 Structures 10 bytes each, last byte dealing with swap table. |
| 0x70 | 2 | Unknown, 0x6 1FE |
| 0x72 | 3 | Indirect Texture Reference. 8 fields 3 bits each, starting with Texture Map 0 at lsb, followed by Texture Coordinate 0. |
| 0x75 | 11 | padding |
| 0x80 | 384 | (8) Shader Stages |

## Each Shader Stage
| Offset | Size | Description |
|---|---|---|
| 0x00 | | |
| 0x08 | 2 | Constant Selection |
| 0x13 | 2 | 3lsb TexCoord/3b TexMap/1b enable/3b RasterColor|
| 0x17 | 1 | Output Color: 2msb Dest/2b Scale/1b clamb/2b op/1b bias|
| 0x18 | 2 | Color Selection A-D, 4b each starting with A at msb. |
| 0x27 | 1 | Output Alpha: 2msb Dest/2b Scale/1b clamb/2b op/1b bias|
| 0x28 | 1.5 | Alpha Selection A-D, 3b each starting with A at msb. |
| 0x29 1/2 | 0.5 | 2b TexSwapSel/2b RasterSwapSel |
| 0x37 | 3 | From msb 3, 1b UnmodifiedLOD/1b UsePrevStage/3b TWrap/3b SWrap/4b Matrix/2b Alpha/3b Bias/2b TexFormat/2b TexStage |

Byte 8-9 Constant Selection
  Constant alpha selection
    5 bits
  Constant Color Selection
    1bit in byte 8, 1nibble of byte 9
    cc1-1 = 0000
    cc7-8 = 0001
    cc3-4 = 0010
    cc5-8 = 0011
    cc1-2 = 0100
    cc3-8 = 0101
    cc1-4 = 0110
    cc1-8 = 0111
    ccrgb0 = 1100
    ccrgb1 = 1101
    ccrgb2 = 1110
    ccrgb3 = 1111
    ccrrr0 = 1 0000
    ccrrr1 = 1 0001
    ccrrr2 = 1 0010
    ccrrr3 = 1 0011
    ccggg0 = 1 0100
    ccggg1 = 1 0101
    ccggg2 = 1 0110
    ccggg3 = 1 0111
    ccbbb0 = 1 1000
    ccbbb1 = 1 1001
    ccbbb2 = 1 1010
    ccbbb3 = 1 1011
    cc_aaa0 = 1 1100
    cc_aaa1 = 1 1101
    cc_aaa2 = 1 1110
    cc_aaa3 = 1 1111

Byte 13 - 14
  bit 1 -
  bit 2 -
  bit 3 - rasterColor bit 0
  bit 4 - rasterColor bit 1
  rastercolor 000 = lightchannel 0
  rastercolor 001 = lightchannel 1
  rastercolor 101 = bumpAlpha
  rastercolor 110 = Normalized BumpAlpha
  rastercolor 111 = 0
  Byte 14
    bit 1 - rasterColor bit 2
    bit 2 - texture enabled
    3bits Texture Map
    3bits Texture Coordinate

Byte 17 Color Output
  nibble1 = destination/scale
  x1 00
  x2 01
  x4 10
  /2 11
  nibble2 = clamp(msb), operation(2b), bias (0x08 usually)

Byte 18 - 19
  nibble1 ColorSelection A
  nibble2 Selection B
  nibble3 Selection C
  nibble4 Selection D
  outputcolor 00
  outputalpha 01
  color0 10
  alpha0 11
  color1 100
  alpha1 101
  color2 110
  alpha2 111
  textureColor 1000
  textureAlpha 1001
  rasterColor 1010
  rasterAlpha 1011
  one 1100
  half 1101
  constantColorSelection 1110
  Zero 1111

Byte 27 - Alpha Output
  nibble1 = destination/scale
  nibble2 = clamp(msb), operation(2b), bias

Byte 28-29 - Alpha Selection 4 groups of 3 bits
  Alpha Selection A 3 msb
  B
  C
  D
  OutputAlpha 000
  alpha0      001
  alpha1      010
  alpha2      011
  textureAlpha 100
  rasterAlpha  101
  constAlphaSel 110
  Zero          111

Byte 29 + 0.5 Swap Selection
  bits 5-6 = texture swap selection
  bits 7-8 = raster swap selection
  swap0 = 00
  swap1 = 01
  swap2 = 10
  swap3 = 11

Byte 37-39 - Indirect Tex
  1 bit = UnmodifiedLOD
  1 bit = UsePrevStage
  3 bits = TWrap
  Byte 38
  3 bits = SWrap
  nibble = matrix
  2 bits = Alpha
  3 bits = Bias (STU 111 - None 000)
  2 bit = Tex Format
  2 lsb = Tex Stage
