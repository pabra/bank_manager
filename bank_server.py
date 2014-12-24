#!/usr/bin/env python
import os
import bottle

app = application = bottle.Bottle()

@app.route('/static/<filename>')
def serve_static(filename):
    root = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
    return bottle.static_file(filename, root=root)

@app.route('/')
@bottle.view('index')
def show_index():
    return

if '__main__' == __name__:
    #bottle.debug(True)
    bottle.run(app=app,
               host='127.0.0.1',
               port=3001,
               reloader=True,
               debug=True)
