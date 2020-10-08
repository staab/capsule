import os, bleach
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from flask import Flask, request, render_template, make_response, redirect, abort
from markdown import Markdown
from mdx_gfm import GithubFlavoredMarkdownExtension

def env(k):
    return os.environ[k]


def first(xs):
    for x in xs or []:
        return x

def merge(a, b):
    result = {}

    for k, v in a.items():
        result[k] = v

    for k, v in b.items():
        result[k] = v

    return result


md = Markdown(extensions=[GithubFlavoredMarkdownExtension()])

def md_to_html(contents):
    return md.convert(bleach.clean(contents, tags=[]))


# Database helpers

class Db(object):
    conn = None

    @staticmethod
    def connect():
        if Db.conn:
            Db.conn.close()

        Db.conn = connect(env("DATABASE_URL"), cursor_factory=RealDictCursor)

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


Db.exec("""
create table if not exists capsule (
    id serial,
    created timestamp NOT NULL,
    reveals timestamp NOT NULL,
    markdown text NOT NULL,
    html text NOT NULL
)
""")


# App


app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/capsules')
def capsule_list():
    capsules = Db.all("""
    select
      id, to_char(created, 'yyyy-mm-dd') as created, to_char(reveals, 'yyyy-mm-dd') as reveals,
      case when reveals < now() then html else null end as html
    from capsule
    order by created desc
    limit %(limit)s
    offset %(offset)s
    """, {
        'limit': request.args.get('limit', 100),
        'offset': request.args.get('offset', 0),
    })

    return render_template("capsules.html", capsules=capsules)


@app.route('/capsules/<int:id>')
def capsule_detail(id):
    capsule = Db.one("""
    select
      id, to_char(created, 'yyyy-mm-dd') as created, to_char(reveals, 'yyyy-mm-dd') as reveals,
      case when reveals < now() then html else null end as html
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
    return make_response({"html": md_to_html(request.json["markdown"])})


@app.route('/api/capsule', methods=['POST'])
def api_capsule_post():
    id = Db.val("""
    insert into capsule (created, reveals, markdown, html)
    values (now(), %(reveals)s, %(markdown)s, %(html)s)
    returning id
    """, merge(request.json, {
        'html': md_to_html(request.json['markdown']),
    }))

    return make_response({"id": id})
