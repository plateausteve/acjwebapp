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
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Still in the virtual environment, change to the folder containing
``settings_local.py`` and ``settings_pa.py``.

```
cd acjapp/acjapp
```

Each of these files contains the settings required to host the webapp
a) locally (through 127.0.0.1) or b) on PythonAnywhere. In order to
host the app online, you will likely need to create your own settings
file or customize the existing PythonAnywhere file to fit your account
and MySQL database.

In order to host the site locally, create a symlink.

```
ln -s settings_local.py settings.py
```

Then, change to the directory above and use manage.py to run the server.

```
cd ..
python manage.py runserver
```