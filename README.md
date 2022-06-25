# Drawing Test
Adaptive comparative judgment web app

What's this?

This web app collects comparative judgment data that can be analyzed with Thurstone's Law of Comparative Judgment (CJ). Comparative Judgment is a measurement tool for estimating an unknown paramater attribute for a group of items from the perspective of one or more judges. The parameter investigated with this method should be a holistic attribute all items share to varying degrees.

The value of collecting and crunching these data comes from the resulting information about:

    The perception of the judge(s), and
    An estimated measure of a parameter, quality, or characteristic of the items being compared.

Terms

    Set is the collection of items being compared.
    Script is the term used in early research literature for an item being compared.
    Estimate is the estimated parameter value of item after comparison.
    Judge is the person doing pairwise comparisons.
    Person ID is the anonymous ID code that links an item to the person who created it.

Making comparisons

Users who are judges have been assigned one or more sets of anonymous scripts. Select a set from the Compare menu, where two scripts will be presented side-by-side. Using your own criteria, decide whether the left or right is more ______. (The page will prompt you with the comparison term for that set.) Make sure to view all pages of each PDF file before making a judgement.

Keep making comparisons until you reach the limit when you'll no longer be presented with pairs from that set. As you progress, you will be show pairs that are more and more similar. Use the criteria you've developed for your decisions, but don't overthink your decisions or worry about making the wrong decisions. There will be plenty of them to account for ambiguity.
Checking your comparisons

Select a set from the Comparisons menu to see a table of all comparisons you've made so far. Clicking on the script ID code will let you inspect each one.
Checking your results

Select a set from the My Results menu to see dynamically computed statistics based on the comparisons you've made. The purpose of this table is to show your progress as you make comparisons. The reliability and validity of these rankings and statistics are not sufficient for educational decisionmaking.
Viewing combined ranks and scores

Select a set from the Stats menu to see how ranks and scores are estimated combining the comparisons of up to three judges. When the similarity of the rank order of scripts by three judges reaches acceptable levels, the scores will be finalized.

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
mysql> CREATE USER 'django'@'localhost' IDENTIFIED BY "your database password (from before)";
mysql> GRANT ALL PRIVILEGES ON pairwise.* TO django@localhost;
mysql> quit
```

Edit the DATABASES section of ``acjapp/acjap/settings.py`` in order to reflect the username you use.

Now, you should be able to migrate the database and run your server.

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

In order to edit the database create a superuser and log into the admin 
page of the site.

```
python manage.py createsuperuser 
```
