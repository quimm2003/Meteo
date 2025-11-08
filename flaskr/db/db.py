"""Module to create and handle a database connection."""
# Created: vie jul 12 10:58:13 2024 (+0200)
# Last-Updated: mié sep 25 09:22:20 2024 (+0200)
# Filename: db.py
# Author: Joaquin Moncanut <quimm2003@gmail.com>
import click

from flask import current_app, g

import psycopg2


def get_db():
    if 'db' not in g:
        g.db = psycopg2.connect(host=current_app.config['DB_HOST'], database=current_app.config['DATABASE'], user=current_app.config['DB_USER'], password=current_app.config['DB_PASSWORD'])

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with db.cursor() as cur:
        with current_app.open_resource('db/schema.sql') as f:
            cur.execute(f.read())

        cur.commit()

@click.command('init-db')
def init_db_command():
    """
    Clear the existing data and create new tables.

    Use command: flask --app flaskr/app init-db to initialize database. It will delete all existent data and tables
    """
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
