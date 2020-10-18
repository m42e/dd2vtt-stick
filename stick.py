#!/usr/bin/env python3
from PIL import Image
import json
import copy
import base64
import pathlib
import io
import logging
from math import floor, ceil, sqrt

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


def parse_args(args=None):
    import sys
    import argparse

    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser()

    modegroup = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument(
        "files", type=str, nargs="+", help="dd2vtt files to stitch together"
    )
    modegroup.add_argument(
        "-y", "--vertical", action="store_true", help="stitch vertical"
    )
    modegroup.add_argument(
        "-x", "--horizontal", action="store_true", help="stitch horizontal"
    )
    modegroup.add_argument("-g", "--grid", action="store_true", help="stitch in a grid")
    parser.add_argument(
        "-o", "--output", type=str, help="output filename", default="combined.dd2vtt"
    )
    parser.add_argument("-p", "--png", action="store_true", help="use png images")
    parser.add_argument(
        "-l",
        "--largest",
        action="store_true",
        help="use largest image as size, else the size of the first will be used",
    )
    return parser.parse_args(args)


def read_file(file):
    if not isinstance(file, pathlib.Path):
        file = pathlib.Path(file)

    try:
        with open(file, "r") as fin:
            data = json.load(fin)
        if data["format"] != 0.2:
            raise Exception("fileformat to new")
        return data
    except:
        _logger.exception("Failed to load file")


class Canvas(object):
    def __init__(self, files, mode, image_type="PNG", size_mode="first"):
        self.image_type = image_type
        self.files = files
        self.mode = mode
        self.size_mode = size_mode
        self.create_canvas()
        self.add_images()
        self.transform_information()
        self.finalize()

    def create_canvas(self):
        size = {"y": 0, "x": 0}
        if self.size_mode == "first":
            size["x"] = self.files[0]["resolution"]["map_size"]["x"]
            size["y"] = self.files[0]["resolution"]["map_size"]["y"]
        else:
            for file in self.files:
                size["x"] = max(size["x"], file["resolution"]["map_size"]["x"])
                size["y"] = max(size["y"], file["resolution"]["map_size"]["y"])

        grid_size = copy.copy(size)
        size["x"] = size["x"] * self.files[0]["resolution"]["pixels_per_grid"]
        size["y"] = size["y"] * self.files[0]["resolution"]["pixels_per_grid"]

        count = len(self.files)
        if self.mode == "g":
            width = ceil(sqrt(count)) * size["x"]
            vcount = 0
            hcount = count
            index = 0
            while hcount > 0:
                next_v_index = index + ceil(sqrt(count))
                while index < min(next_v_index, len(self.files)):
                    self.files[index]["pos_in_image"] = {
                        "y": vcount * size["y"],
                        "x": (index - vcount * ceil(sqrt(count))) * size["x"],
                        "height": size["y"],
                        "width": size["x"],
                    }
                    self.files[index]["pos_in_grid"] = {
                        "y": vcount * grid_size["y"],
                        "x": (index - vcount * ceil(sqrt(count))) * grid_size["x"],
                        "height": grid_size["y"],
                        "width": grid_size["x"],
                    }
                    index += 1
                hcount -= ceil(sqrt(count))
                vcount += 1
            _logger.info("Created grid with %d x %d", ceil(sqrt(count)), vcount)
            height = vcount * size["y"]
            self.gridw = ceil(sqrt(count)) * grid_size["x"]
            self.gridh = vcount * grid_size["y"]
        elif self.mode == "y":
            width = size["x"]
            height = count * size["y"]
            for f in range(len(self.files)):
                self.files[f]["pos_in_image"] = {"x": 0, "y": f * size["y"]}
            self.gridw = grid_size["x"]
            self.gridh = count * grid_size["y"]
        elif self.mode == "x":
            width = count * size["x"]
            height = size["y"]
            for f in range(len(self.files)):
                self.files[f]["pos_in_image"] = {"y": 0, "x": f * size["x"]}
            self.gridw = count * grid_size["x"]
            self.gridh = grid_size["y"]
        self.canvas = Image.new(size=(width, height), mode="RGBA")
        _logger.info("Created canvas with size of %d x %d", width, height)

    def add_images(self):
        for index, f in enumerate(self.files):
            _logger.debug(
                "Placing image %d at %dx%d",
                index,
                f["pos_in_image"]["x"],
                f["pos_in_image"]["y"],
            )
            bio = io.BytesIO(base64.b64decode(f["image"]))
            srcImg = Image.open(bio)
            self.canvas.paste(
                srcImg,
                box=(
                    f["pos_in_image"]["x"],
                    f["pos_in_image"]["y"],
                    f["pos_in_image"]["x"] + srcImg.size[0],
                    f["pos_in_image"]["y"] + srcImg.size[1],
                ),
            )
        self.canvas_io = io.BytesIO()
        self.canvas.save(self.canvas_io, self.image_type)

    def transform_information(self):
        self.information = {
            "format": 0.2,
            "resolution": {
                "map_origin": {"x": 0, "y": 0},
                "map_size": {"x": self.gridw, "y": self.gridh},
                "pixels_per_grid": self.files[0]["resolution"]["pixels_per_grid"],
            },
            "line_of_sight": [],
            "portals": [],
            "environment": self.files[0]["environment"],
            "lights": [],
        }

        for index, f in enumerate(self.files):
            for los in f["line_of_sight"]:
                for z in los:
                    z["x"] += f["pos_in_grid"]["x"]
                    z["y"] += f["pos_in_grid"]["y"]
            for port in f["portals"]:
                port["position"]["x"] += f["pos_in_grid"]["x"]
                port["position"]["y"] += f["pos_in_grid"]["y"]
                for z in port["bounds"]:
                    z["x"] += f["pos_in_grid"]["x"]
                    z["y"] += f["pos_in_grid"]["y"]
            for port in f["lights"]:
                port["position"]["x"] += f["pos_in_grid"]["x"]
                port["position"]["y"] += f["pos_in_grid"]["y"]

            self.information["line_of_sight"].extend(f["line_of_sight"])
            self.information["line_of_sight"].append(
                [
                    {"x": f["pos_in_grid"]["x"], "y": f["pos_in_grid"]["y"]},
                    {
                        "x": f["pos_in_grid"]["x"] + f["resolution"]["map_size"]["x"],
                        "y": f["pos_in_grid"]["y"],
                    },
                    {
                        "x": f["pos_in_grid"]["x"] + f["resolution"]["map_size"]["x"],
                        "y": f["pos_in_grid"]["y"] + f["resolution"]["map_size"]["y"],
                    },
                    {
                        "x": f["pos_in_grid"]["x"],
                        "y": f["pos_in_grid"]["y"] + f["resolution"]["map_size"]["y"],
                    },
                    {"x": f["pos_in_grid"]["x"], "y": f["pos_in_grid"]["y"]},
                ]
            )
            self.information["portals"].extend(f["portals"])
            self.information["lights"].extend(f["lights"])

    def finalize(self):
        self.information["image"] = base64.b64encode(self.canvas_io.getvalue()).decode(
            "utf8"
        )

    def save(self, filename="combined.dd2vtt"):
        with open(filename, "w") as fout:
            json.dump(self.information, fout)


def main():
    args = parse_args()
    files = []
    for file in args.files:
        files.append(read_file(file))

    mode = "g"
    if args.vertical:
        mode = "y"
    if args.horizontal:
        mode = "x"

    image_type = "WEBP"
    if args.png:
        image_type = "PNG"

    size_mode = "first"
    if args.largest:
        size_mode = "largest"

    c = Canvas(files, mode, image_type=image_type, size_mode=size_mode)
    c.save(args.output)


if __name__ == "__main__":
    main()
