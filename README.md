# DD2VTT Stick

This is a small tool to stick together `dd2vtt` files to import them into one scene.

Works with [DD Import](https://github.com/moo-man/FVTT-DD-Import)


## Usage 

If you know about Python and stuff, skip this section :)

### Get python3

Goto [https://www.python.org](https://www.python.org) and download python. Install it, too.
If you have done that you should be able to call python3 from the Commandline (for windows users: press the windows-key and R, enter "cmd" and hit Enter)
if that works you are good to go. There should be plenty of tutorials in the web how to achieve this.

### Install requirements

If python is up and running install the dependencies for this script:

```
pip install -r requirements.txt
```

If this does not print error messages you are good to go and see the next step

## Usage (for those who know about python and stuff)

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
