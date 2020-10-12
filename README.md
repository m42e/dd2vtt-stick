# DD2VTT Stick

This is a small tool to stick together `dd2vtt` files to import them into one scene.

Works with [DD Import](https://github.com/moo-man/FVTT-DD-Import)

## Usage

```
usage: stick.py [-h] (-y | -x | -g) [-o OUTPUT] files [files ...]

positional arguments:
  files                 dd2vtt files to stitch together

optional arguments:
  -h, --help            show this help message and exit
  -y, --vertical        stitch vertical
  -x, --horizontal      stitch horizontal
  -g, --grid            stitch in a grid
  -o OUTPUT, --output OUTPUT
                        output filename
```

### Example

```bash
./stick.py -g church1.dd2vtt church2.dd2vtt church3.dd2vtt church4.dd2vtt
```
