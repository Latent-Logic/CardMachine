#!/usr/bin/python
'''
Flask host web generator.
'''
import os
from flask import Flask, request, render_template, send_from_directory, jsonify
from single_card import make_single_card

app = Flask(__name__)
DEBUG = True


class InvalidAPIUsage(Exception):
    """Error return Exception class"""
    status_code = 400

    def __init__(self, error, details, allowed=None,
                 status_code=None, payload=None):
        Exception.__init__(self)
        self.error = error
        self.details = details
        if status_code is not None:
            self.status_code = status_code
        if allowed is not None:
            self.allowed = allowed
        self.payload = payload

    def to_dict(self):
        retval = dict(self.payload or ())
        retval['error'] = self.error
        retval['details'] = self.details
        if 'allowed' in self:
            retval['allowed'] = self.allowed
        return retval


@app.errorhandler(InvalidAPIUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/resources/<path:filename>')
def serve_resources(filename):
    return send_from_directory('TSSSF/resources/', filename)


@app.route('/TSSSF/', defaults={'path': '/'}, methods=['GET', 'POST'])
@app.route('/TSSSF/<path:path>', methods=['GET', 'POST'])
def ponyimage_glue(path):
    in_json = request.get_json()
    out_json = {}
    print in_json
    imagetype = in_json.get('imagetype', 'cropped')
    returntype = in_json.get('returntype', 'encoded_url')
    my_url = in_json.get('my_url')
    print imagetype, returntype, my_url
    pycard = in_json.get('pycard')
    if not pycard:
        raise InvalidAPIUsage("No pycard string found", in_json)
    #Second argument is filename
    filename = None
    if returntype == 'file':
        filename = "images/{}.png" % imagetype
    elif returntype != 'encoded_url':
        raise InvalidAPIUsage("This backend doesn't support this returntype",
                              returntype)
    ret_val = make_single_card(pycard, filename, imagetype, returntype,
                               None, None)
    print ret_val[:64]
    if returntype == 'file':
        out_json['image'] = request.url_root + ret_val
    elif returntype == 'encoded_url':
        out_json['image'] = ret_val
    out_json['card_str'] = pycard
    out_json['output'] = "Nothing here"
    print str(out_json)[:79]
    return jsonify(out_json)


def make_tree(path):
    """Create dict of files in path.
    Modified from https://gist.github.com/andik/e86a7007c2af97e50fbb """
    tree = dict(name=path, children=[])
    try:
        lst = os.listdir(path)
    except OSError:
        pass  # ignore errors
    else:
        for name in lst:
            fname = os.path.join(path, name)
            if os.path.isdir(fname):
                tree['children'].append(make_tree(fname))
            elif name[0] != '.':
                tree['children'].append(dict(name=fname))
    return tree


@app.route('/images/')
def list_images():
    if not os.path.isdir('images/'):
        return "Please create the images/ folder in this checkout"
    return render_template('dirtree.html', tree=make_tree('images/'),
                           url_root=request.url_root)


@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images/', filename)


@app.route('/', defaults={'filename': 'index.html'})
@app.route('/<path:filename>')
def serve_frontend_files(filename):
    return send_from_directory('TSSSF/frontend/', filename)


if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=DEBUG)
