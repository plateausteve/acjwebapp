# Drawing Test
Adaptive comparative judgment webap

This webapp collects comparative judgment data that can be processed
using Thurstone's Law of Comparative Judgment (CJ). Comparative
Judgment is a measurement tool that can be used to estimate an unknown
paramater attribute for a group of items from the perspective of one
or more judges. The parameter investigated with this method should be
a holistic attribute all items share to varying degrees, such as
"overall quality."

The value of collecting and crunching these data is from the
information it provides about:

* The perception of the **judge(s)**, and
* An underlying **parameter** or quality of an item, to whatever
  degree known by researchers.

# Installation

First, clone the repo and cd into the created directory.

```
git clone https://github.com/plateausteve/acjwebapp.git
cd acjwebapp
```

Then, create a virtual environment using Python 3.8 and use it to
install the required packages. Here, we use python's venv.

```
python3.8 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Secret keys

Change to the folder ``acjapp`` and create a file called ``.env``.

```
cd acjapp
touch .env
```

Then, use your preferred text editor to edit the file. You should
create two entries in the file. Django uses ``SECRET_KEY`` to run
the server, and will use ``DB_PASSWORD`` to connect to your mySQL
database once we set it up.

```
SECRET_KEY = "your secret key"
DB_PASSWORD = "your database password"
```

## Setting up mySQL

From this point, we assume that you will be hosting the site locally
on your computer. If this is not true, and you are using a hosting
service, you should set up a mySQL database as the service reccommends.

If you do not already have mySQL installed, do so. This can vary
greatly based on your operating system, so a good place to start is
[https://dev.mysql.com/doc/mysql-installation-excerpt/8.0/en/](https://dev.mysql.com/doc/mysql-installation-excerpt/8.0/en/).

Use your mySQL installation to create a new database for use with this
project. Then, create a new user for it identified by the database
password you entered in ``.env``.

```
mysql> CREATE DATABASE pairwise;
mysql> CREATE USER 'django'@'localhost' IDENTIFIED BY "your database password";
mysql> GRANT ALL PRIVILEGES ON pairwise.* TO django@localhost;
mysql> quit
```

You don't need to do any further setup on the database, as Django will
create the correct tables.

## Selecting or creating a settings file

Inside the acjapp folder, there are two settings files. They
separately contain the settings required to host the webapp a) locally
(through 127.0.0.1) or b) on PythonAnywhere. In order to host the app
online, you will likely need to create your own settings file or
customize the existing PythonAnywhere file to match your account.

In order to host the site locally, create a symlink to the local
settings file.

```
ln -s acjapp/settings_local.py acjapp/settings.py
```

With the settings symlinked, you can finally run the server using
``manage.py``.

```
cd ..
python manage.py runserver
```