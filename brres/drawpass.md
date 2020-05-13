# Draw lists
The draw lists also have influence over Harry Potter effect.
## Command Code 0x04
Contrary to wiki, the first two bytes are the material index, and then the object index. In Brawlbox the unknown 6th byte is the draw priority (The list of draw entries is sorted in ascending order by this number. It's used for xlu materials, seems particularly important for blended mats with depthUpdate disabled. This forces them to be drawn last?) On koopa cape, the waterfall has priority 1, the lake priority 2.

## Subsections
Known lists are NodeTree, DrawOpa, and DrawXlu.
* NodeTree Typically 20001 (bones)
* DrawOpa list of 0x04 commands for opaque materials
* DrawXlu list of 0x04 commands for transparent materials.
Since changing a material to transparent should move the entry in the draw list... it should be redrawn on saving (however sizing should be the same)
