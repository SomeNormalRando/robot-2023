# TowerMaintainer web interface
```
EV3 [python-ev3dev]
|
|---[Bluetooth socket]---|
                         |
server [flask] <---------|
|
|---[flask-socketio]-----------|
                               |
web interface [html/jinja] <---|
```

### run development server
```
flask --app server run
```

with debug mode on:
```
flask --app server run --debug
```

note: make sure the terminal is in this folder's virtual environment (in VS Code there should be a `.venv` before the current file path)