#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# png_inventory.py - add to a database of PNG files for display.
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
from common_utils import *
from image_database import *


def png_inventory(verbose=False, library_path=None, database_file=None):

    conn = None
    cur = None

    # create a database connection
    conn = connect_to_local_db(database_file, verbose)
    if not conn:
        print("Database could not be opened")
        os._exit(os.EX_IOERR)
    create_tables_if_missing(conn, verbose)
    cur = conn.cursor()

    groups = get_image_group_dictionaries(cur, verbose)
    group_dirs = []
    for _, subdirs, _ in os.walk( library_path ):
        for dirname in subdirs:
            if dirname not in groups['name_to_id']:
                get_or_insert_image_group(cur, verbose, dirname)

    groups = get_image_group_dictionaries(cur, verbose)
    new_images = 0

    for group_name in groups['name_to_id']:
        print('Group: %s (%s)' % (group_name, groups['name_to_id'][group_name]))
        path = os.path.join( library_path, group_name )
        for _, _, filenames in os.walk( path ):
            for filename in filenames:
                lowered = filename.lower()
                if lowered.endswith( '.png' ) or lowered.endswith( '.bmp' ):
                    if not filename.startswith( '.' ):
                        file_pathname = os.path.join( path, filename )
                        file_modified_time = os.path.getmtime(file_pathname)
                        file_size = os.path.getsize(file_pathname)
                        one_record = {
                            'id': None,
                            'group_id': groups['name_to_id'][group_name],
                            'group_name': group_name,
                            'filename': filename,
                            'size': file_size,
                            'file_modified_time': file_modified_time,
                            'last_display': None,
                            'display_count': 0,
                            'creation_time': None,
                            'removed': False
                        }
                        inserted = insert_or_update_image(cur, verbose, one_record)
                        if inserted:
                            new_images += 1

    images = get_all_images(cur, verbose)

    print("%s images total, %s new as of this scan." % (len(images), new_images))

    finish_with_database(conn, cur)


if __name__ == "__main__":
    config = read_config()
    if config is None:
        print('Error reading your config.xml file!')
        sys.exit(2)

    args = argparse.ArgumentParser(description="Make an inventory of PNG files in the image library")
    args.add_argument("--quiet", "-q", action='store_false', dest='verbose',
                      help="reduce log output")
    args.add_argument('--path', type=str, default=config['library'], dest='library_path',
                      help='Path to library', required=False)
    args = args.parse_args()

    database_file = os.path.join(config['installpath'], 'images.db')
    png_inventory(
        verbose=args.verbose,
        library_path=args.library_path,
        database_file=database_file
    )