#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# png_to_bmp.py - covert a PNG to a 6-color BMP.
# No resizing or color processing is done here.
# It is assumed the PNG has already been processed to look acceptable
# when reduced to 6 colors, or is already in 6 colors, and is the right size.
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

import argparse, os, re, sys
from PIL import Image
from common_utils import *


def png_to_bmp(verbose=False, input_file=None, output_file=None):
    # Open the input image
    img = Image.open(input_file)

    # Convert to greyscale
    #img.convert('L')

    # Reduce the number of colors to 6
    # The image should already be prepared with the required 6 color palette,
    # but this forces it for compression purposes.
    img = img.quantize(colors=6, method=Image.FASTOCTREE)
    
    # Save the image as BMP
    img.save(output_file, format='BMP')


if __name__ == "__main__":
    args = argparse.ArgumentParser(description="Convert a PNG to a BMP")
    args.add_argument("--quiet", "-q", action='store_false', dest='verbose',
                      help="reduce log output")
    args.add_argument('--in', type=argparse.FileType('rb'), default=sys.stdin, dest='input_file',
                      help='Input PNG file', required=True)
    args.add_argument('--out', type=argparse.FileType('wb'), default=sys.stdout, dest='output_file',
                      help='Output BMP file', required=True)
    args = args.parse_args()

    set_up_logger()

    png_to_bmp(
        verbose=args.verbose,
        input_file=args.input_file,
        output_file=args.output_file
    )
