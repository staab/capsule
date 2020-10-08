import os
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from flask import Flask, request, render_template, make_response, redirect, abort
from markdown import markdown
from mdx_gfm import GithubFlavoredMarkdownExtension

def env(k):
    return os.environ[k]


def first(xs):
    for x in xs or []:
        return x


def md(contents):
    return markdown(contents)


# Database helpers

class Db(object):
    conn = None

    @staticmethod
    def connect():
        if Db.conn:
            Db.conn.close()

        Db.conn = connect(env("DATABASE_URL"), cursor_factory=RealDictCursor)
        Db.exec("set search_path to app")

    @staticmethod
    def exec(q, args=[], cb=None):
        try:
            with Db.conn.cursor() as c:
                c.execute(q, args)
                Db.conn.commit()

                if cb:
                    return cb(c)
        except:
            Db.connect()

            raise


    @staticmethod
    def all(q, args=[]):
        return Db.exec(q, args, lambda c: c.fetchall())

    @staticmethod
    def col(q, args=[]):
        return [first(row.values()) for row in Db.all(q, args)]

    @staticmethod
    def one(q, args=[]):
        return first(Db.all(q, args))

    @staticmethod
    def val(q, args=[]):
        row = Db.one(q, args)

        if row:
            return first(row.values())


Db.connect()


# Migrate database


Db.exec("create schema if not exists app")
Db.exec("""
create table if not exists capsule (
    id serial,
    created timestamp NOT NULL,
    reveals timestamp NOT NULL,
    markdown text NOT NULL
)
""")


# App


app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/capsule/<int:id>')
def capsule_detail(id):
    capsule = Db.one("""
    select
      id, to_char(created, 'yyyy-mm-dd') as created, to_char(reveals, 'yyyy-mm-dd') as reveals,
      case when reveals < now() then markdown else null end as markdown
    from capsule
    where id = %(id)s
    """, {
        'id': id
    })

    if not capsule:
        abort(404)

    return render_template("capsule.html", capsule=capsule)


@app.route('/api/render', methods=['POST'])
def api_render():
    return make_response({"html": md(request.json["markdown"])})


@app.route('/api/capsule', methods=['POST'])
def api_capsule_post():
    id = Db.val("""
    insert into capsule (created, reveals, markdown)
    values (now(), %(reveals)s, %(markdown)s)
    returning id
    """, request.json)

    return make_response({"id": id})
