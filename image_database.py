#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# image_database.py - functions for managing a collection of image files.
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

from datetime import *
import calendar
import sqlite3
from sqlite3 import Error


def connect_to_local_db(db_file, verbose):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :param verbose: whether we are verbose logging
    :return: Connection object or None
    """
    conn = None
    if verbose:
        print('Opening local database: %s' % db_file)
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn


def create_tables_if_missing(conn, verbose):
    """ create needed database tables if missing
    :param conn: database connection
    :param verbose: whether we are verbose logging
    """
    if verbose:
        print('Creating tables if needed')

    conn.execute("""
        CREATE TABLE IF NOT EXISTS status (
            last_sync REAL,
            last_display REAL
        )""")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS image_groups (
            id INTEGER PRIMARY KEY NOT NULL,
            name TEXT NOT NULL UNIQUE
        )""")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY NOT NULL,
            group_id INTEGER NOT NULL,
            filename TEXT,
            size REAL NOT NULL,
            file_modified_time REAL NOT NULL,
            last_display REAL,
            display_count INTEGER NOT NULL DEFAULT 0,
            creation_time REAL NOT NULL,
            removed BOOLEAN NOT NULL DEFAULT FALSE
        )""")

    conn.execute("""
        CREATE INDEX IF NOT EXISTS images_group_id
            ON "images" (group_id);
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS images_last_display
            ON "images" (last_display);
        """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS images_display_count
            ON "images" (display_count);
        """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS image_display_history (
            id INTEGER PRIMARY KEY NOT NULL,
            image_id INTEGER NOT NULL,
            display_time REAL,
            charging BOOLEAN NOT NULL,
            charge_level INTEGER
        )""")

    conn.execute("""
        CREATE INDEX IF NOT EXISTS image_display_history_display_time
            ON "image_display_history" (display_time);
        """)


def get_status_or_defaults(cur, last_sync, last_display):
    """ get values from the current status record, or create a new one if missing
    :param cur: database cursor
    :param last_sync: default last_sync value
    :param last_display: default last_display value
    """
    cur.execute("SELECT last_sync, last_display FROM status")
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO status (last_sync, last_display) VALUES (?, ?)", (last_sync, last_display))
    else:
        last_sync = row[0]
        last_display = row[1]
    status = {"last_sync": last_sync, "last_display": last_display}
    return status


def set_status(cur, status):
    """ set values in the current status record
    :param cur: database cursor
    :param status: sync status record
    """
    cur.execute("UPDATE status SET last_sync = ?, last_display = ?", (status['last_sync'], status['last_display']))


def get_or_insert_image_group(cur, verbose, name):
    """ fetch or insert the record for an image group
    :param cur: database cursor
    :param verbose: whether we are verbose logging
    :param name: group name
    """
    data = {'name': name}
    cur.execute("SELECT id FROM image_groups WHERE name = :name", data)
    row = cur.fetchone()
    if not row:
        if verbose:
            print('Adding new image group with name: %s' % (name))
        cur.execute("""
            INSERT INTO image_groups ( name ) VALUES ( :name )""", data)
        cur.execute("SELECT id FROM image_groups WHERE name = :name", data)
        row = cur.fetchone()
    record = {
        "id": row[0],
        "name": name
    }
    return record


def insert_or_update_image(cur, verbose, image):
    """ insert a new image or update any preexisting one with a matching group id and name
    :param cur: database cursor
    :param verbose: whether we are verbose logging
    :param image: image record
    :return: True if the image id did not already exist
    """

    if image['id'] == None:
        cur.execute("SELECT id FROM images WHERE group_id = :group_id AND filename = :filename", image)
    else:
        cur.execute("SELECT id FROM images WHERE id = :id", image)

    row = cur.fetchone()
    if not row:
        if verbose:
            print('Adding new image %s/%s' % (image['group_name'], image['filename']))
        image['creation_time'] = calendar.timegm(datetime.now(UTC).utctimetuple())
        cur.execute("""
            INSERT INTO images (
                id,
                group_id,
                filename,
                size,
                file_modified_time,

                last_display, display_count,
                creation_time,
                removed
            ) VALUES (
                :id,
                :group_id,
                :filename,
                :size,
                :file_modified_time,

                NULL, 0,
                :creation_time,
                FALSE
            )""", image)
        return True
    else:
        image['id'] = row[0]
        if verbose:
            print('Updating existing image %s/%s' % (image['group_name'], image['filename']))
        cur.execute("""
            UPDATE images SET
                filename = :filename,
                size = :size,

                last_display = :last_display,
                display_count = :display_count,
                file_modified_time = :file_modified_time,
                removed = :removed

            WHERE id = :id""", image)
        return False


def get_image_group_dictionaries(cur, verbose):
    """ get all the image groups and build dictonaries
    for mapping id to name and name to id.
    :param cur: database cursor
    :param verbose: whether we are verbose logging
    :return: An object containing two dictionaries
    """
    if verbose:
        print('Fetching all image groups from database')
    cur.execute("""SELECT id, name FROM image_groups""")
    rows = cur.fetchall()
    id_to_name = {}
    name_to_id = {}
    for row in rows:
        id_to_name[row[0]] = row[1]
        name_to_id[row[1]] = row[0]
    results = {}
    results['id_to_name'] = id_to_name
    results['name_to_id'] = name_to_id
    return results


def get_all_images(cur, verbose):
    """ get all images in the database
    :param cur: database cursor
    :param verbose: whether we are verbose logging
    :return: An array of objects
    """
    image_groups = get_image_group_dictionaries(cur, verbose)
    if verbose:
        print('Fetching all images from database')
    cur.execute("""
        SELECT
            id,
            group_id,
            filename,
            size,
            file_modified_time,
            last_display,
            display_count,
            creation_time,
            removed
        FROM images ORDER BY display_count ASC""")
    rows = cur.fetchall()
    records = []
    for row in rows:
        record = {
            "id": row[0],
            "group_id": row[1],
            "group_name": image_groups['id_to_name'][row[1]],
            "filename": row[2],
            "size": row[3],
            "file_modified_time": row[4],
            "last_display": row[5],
            "display_count": row[6],
            "creation_time": row[7],
            "removed": row[8],
        }
        records.append(record)
    return records


def report_image_as_displayed(cur, verbose, image_id, charging, charge_level):
    """ update the record for an image showing that it was the one most recently displayed,
    and make a history entry for the event as well.
    :param cur: database cursor
    :param verbose: whether we are verbose logging
    :param image_id: id of image
    """
    current_date = calendar.timegm(datetime.now(UTC).utctimetuple())
    data = {
        "id": image_id,
        "last_display": current_date
    }
    cur.execute("UPDATE images SET last_display = :last_display, display_count = display_count+1 WHERE id = :id", data)
    cur.execute("""INSERT INTO image_display_history
        (image_id, display_time, charging, charge_level)
        VALUES (?, ?, ?, ?)""", (image_id, current_date, charging, charge_level))


def finish_with_database(conn, cur):
    """ commit and close the cursor and database
    :param conn: database connection
    :param cur: database cursor
    """
    cur.close()
    conn.commit()
    conn.close()