.. _ref_intro_migrations:

==========
Migrations
==========


:index: migrations fill_expr cast_expr

EdgeDB’s baked-in migration system lets you painlessly evolve your schema
throughout the development process.

1. Write an initial schema
--------------------------

By convention, your EdgeDB schema is defined inside one or more ``.esdl``
files that live in a directory called ``dbschema`` in the root directory of
your codebase.

.. code-block::

  .
  ├── dbschema
  │   ├── default.esdl          # schema file (written by you)
  │   └── migrations            # migration files (typically generated by CLI)
  │       └── 00001.edgeql
  │       └── ...
  └── edgedb.toml

The schema itself is written using EdgeDB's schema definition language.

.. code-block:: sdl

  type User {
    required property name -> str;
  }

  type Post {
    required property title -> str;
    required link author -> User;
  }


It's common to keep your entire schema in a single file, typically called
``default.esdl``. However it's also possible to split it across a number of
``.esdl`` files.

To spin up a new instance and populate it with an initial schema, execute the
following commands in a fresh directory.

.. code-block:: bash

  $ edgedb project init
  Do you want to initialize a new project? [Y/n]
  > Y
  <additional prompts>
  $ edgedb migration create
  Created dbschema/migrations/00001.edgeql (id: <hash>)
  $ edgedb migrate
  Applied dbschema/migrations/00001.edgeql (id: <hash>)

2. Edit your schema files
-------------------------

As your application evolves, directly edit your schema files to reflect your
desired data model.

.. code-block:: sdl-diff

    type User {
      required property name -> str;
    }

    type BlogPost {
      property title -> str;
      required link author -> User;
    }

  + type Comment {
  +   required property content -> str;
  + }

3. Generate a migration
-----------------------

To generate a migration that reflects these changes, run ``edgedb migration
create``.

.. code-block:: bash

  $ edgedb migration create


The CLI reads your schema file and sends it to the active EdgeDB instance. The
instance compares the file's contents to its current schema state and
determines a migration plan.  **The migration plan is generated by the
database itself.**

This plan is then presented to you interactively; each detected schema change
will be individually presented to you for approval. For each prompt, you have
a variety of commands at your disposal. Type ``y`` to approve, ``n`` to
reject, ``q`` to cancel the migration, or ``?`` for a breakdown of some more
advanced options.

.. code-block:: bash

  $ edgedb migration create
  Did you create object type 'default::Comment'? [y,n,l,c,b,s,q,?]
  > y
  Created dbschema/migrations/00002.edgeql (id: <hash>)

4. Apply the migration
----------------------

We've generated a migration file, but we haven't yet applied it against our
database! The following command will apply all unapplied migration files:

.. code-block:: bash

  $ edgedb migrate
  Applied m1virjowa... (00002.edgeql)

That's it! You've created and applied your first EdgeDB migration. Your
instance is now using the latest schema.



Data migrations
---------------

Depending on how the schema was changed, you may be prompted to provide an
EdgeQL expression to map the contents of your database to the new schema. To
see this happen, let's make the ``title`` property ``required``.

.. code-block:: sdl-diff

    type User {
      required property name -> str;
    }

    type BlogPost {
  -   property title -> str;
  +   required property title -> str;
      required link author -> User;
    }

Then we'll create another migration.

.. code-block:: bash

  $ edgedb migration create
  Did you make property 'title' of object type
  'default::BlogPost' required? [y,n,l,c,b,s,q,?]
  > y
  Please specify an expression to populate existing objects in order to make
  property 'title' of object type 'default::Post' required:
  fill_expr>

Because ``title`` is currently optional, the database may contain blog posts
without a ``title`` property. The expression you provide will be
used to *assign a title* to any post that doesn't have one. We'll just provide
a simple default title: ``'Untitled'``.

.. code-block::

  fill_expr> 'Untitled'
  Created dbschema/migrations/00002.edgeql, id:
  m1yt3gbstvyfzy2rhqt5335ld6br2amw7ywqu2bvjiqsacbcdxzyya

Nice! It accepted our answer and created a new migration file
``00002.edgeql``. Let's see what the newly created ``00002.edgeql`` file
contains.

.. code-block:: edgeql

  CREATE MIGRATION m1yt3gbstvyfzy2rhqt5335ld6br2amw7ywqu2bvjiqsacbcdxzyya
    ONTO m1cvx47vntfoy24evwrdli7o5unarx2c5t3i2rfspd2qosi6d6iahq
  {
    ALTER TYPE default::Post {
        ALTER PROPERTY title {
            SET REQUIRED USING ('Untitled');
        };
    };
  };

We have a ``CREATE MIGRATION`` block containing an ``ALTER TYPE`` statement to
make ``Post.title`` ``required``. We can see that our fill expression
(``'Untitled'``) is included directly in the migration file.

Note that we could have provide an *arbitrary EdgeQL expression*! The
following EdgeQL features are often useful:

.. list-table::

  * - ``assert_exists``
    - This is an "escape hatch" function that tells EdgeDB to assume the input
      has *at least* one element.

      .. code-block::

        fill_expr> assert_exists(.title)

      If you provide a ``fill_expr`` like the one above, you must separately
      ensure that all movies have a title before executing the migration;
      otherwise it will fail.

  * - ``assert_single``
    - This tells EdgeDB to assume the input has *at most* one element. This
      will throw an error if the argument is a set containing more than one
      element. This is useful is you are changing a property from ``multi`` to
      ``single``.

      .. code-block::

        fill_expr> assert_single(.sheep)

  * - type casts
    - Useful when converting a property to a different type.

      .. code-block::

        cast_expr> <bigint>.xp



Further reading
^^^^^^^^^^^^^^^

For guides on advanced migration workflows, refer to the following guides.

- :ref:`Making a property required <ref_migration_names>`
- :ref:`Adding backlinks <ref_migration_backlink>`
- :ref:`Changing the type of a property <ref_migration_proptype>`
- :ref:`Changing a property to a link <ref_migration_proptolink>`
- :ref:`Adding a required link <ref_migration_reqlink>`

For more information on how migrations work in EdgeDB, check out the :ref:`CLI
reference <ref_cli_edgedb_migration>` or the `Beta 1 blog post
</blog/edgedb-1-0-beta-1-sirius#built-in-database-migrations-in-use>`_, which
describes the design of the migration system.