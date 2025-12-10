#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# prepare_image.py - covert an image a 6-color dithered PNG of the right size.
# Garrett Birkel
# Version 0.1
#
# LICENSE
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the author be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#
# Copyright (c) 2025 Garrett Birkel

import argparse, os, re, sys, logging
from PIL import Image
from common_utils import *


def prepare_image(verbose=False, input_file=None, output_file=None):

    TARGET_X = 1600
    TARGET_Y = 1200
    target_ratio = TARGET_X / TARGET_Y

    logger = logging.getLogger("epaper_frame")

    # Open the input image
    img = Image.open(input_file).convert("RGB")

    ratio = img.width / img.height
    logger.info("Input image size: %i x %i, ratio %.2f.  Target ratio is %.2f." % (img.width, img.height, ratio, target_ratio))

    if ratio < target_ratio:
        img = img.resize((TARGET_X, int(TARGET_X / ratio)), Image.LANCZOS)
        logger.debug("Resized image to %i x %i." % (img.width, img.height))

        # crop excess height
        top_crop = int((img.height - TARGET_Y) / 2)
        img = img.crop((0, top_crop, img.width, top_crop + TARGET_Y))
        logger.debug("Cropped image to %i x %i." % (img.width, img.height))

    else:
        img = img.resize((int(TARGET_Y * ratio), TARGET_Y), Image.LANCZOS)
        logger.debug("Resized image to %i x %i." % (img.width, img.height))

        # crop excess width
        left_crop = int((img.width - TARGET_X) / 2)
        img = img.crop((left_crop, 0, left_crop + TARGET_X, img.height))
        logger.debug("Cropped image to %i x %i." % (img.width, img.height))

    # Define a 6-color palette (black, white, red, green, blue, yellow)
    flat_palette = [0,0,0, 255,255,255, 255,0,0, 0,255,0, 0,0,255, 255,255,0]

    palette_img = Image.new("P", (1, 1))
    palette_img.putpalette(flat_palette, rawmode='RGB')

    logger.debug("Dithering to fixed 6-color palette")
    # Convert image to use the palette with Floyd–Steinberg dithering
    dithered = img.quantize(
        palette=palette_img,
        dither=Image.FLOYDSTEINBERG
    )
    # Save the image as PNG
    logger.debug("Saving prepared image")
    dithered.save(output_file, format='PNG')


if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Prepare a PNG version of an image suitable for display")
    args.add_argument("--quiet", "-q", action='store_false', dest='verbose',
                      help="reduce log output")
    args.add_argument('--in', type=argparse.FileType('rb'), default=sys.stdin, dest='input_file',
                      help='Input image file', required=True)
    args.add_argument('--out', type=argparse.FileType('wb'), default=sys.stdout, dest='output_file',
                      help='Output PNG file', required=True)
    args = args.parse_args()

    set_up_logger()

    prepare_image(
        verbose=args.verbose,
        input_file=args.input_file,
        output_file=args.output_file
    )
