#!/usr/bin/python
'''
Flask host web generator.
'''
import os
from flask import Flask, request, render_template, send_from_directory, jsonify
from single_card import make_single_card, make_single_card_write_all_types

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
    if returntype == 'files':
        ret_val = make_single_card_write_all_types(pycard, "images/")
    elif returntype == 'encoded_url':
        ret_val = make_single_card(pycard, filename, imagetype, returntype,
                                   None, None)
    else:
        raise InvalidAPIUsage("This backend doesn't support this returntype",
                              returntype)
    print ret_val[:64]
    if returntype == 'files':
        out_json['image'] = request.url_root + ret_val
    elif returntype == 'encoded_url':
        out_json['image'] = ret_val
    out_json['card_str'] = pycard
    out_json['output'] = "Nothing here"
    print str(out_json)[:79]
    return jsonify(out_json)


def list_files(path):
    """Create dict of files in path."""
    path = os.path.normpath(path)
    path_len = None
    flist = list()
    for root, _, files in os.walk(path):
        if path_len is None:
            path_len = len(root) + 1  # Account for the '/'
            flist.extend([fname for fname in files
                          if not fname.startswith('.')])
        else:
            flist.extend([os.path.join(root[path_len:], fname) for fname
                          in files if not fname.startswith('.')])
    return flist


@app.route('/images/')
def list_images():
    folder = 'images/'
    if not os.path.isdir(folder):
        return "Please create the %s folder in this checkout" % folder
    file_list = list_files(folder)
    if request.args.get('format') == 'json':
        return jsonify({'base_url': request.base_url, 'files': file_list})
    return render_template('dirtree.html', dirname=folder, flist=file_list,
                           base_url=request.base_url)


@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images/', filename)


@app.route('/', defaults={'filename': 'index.html'})
@app.route('/<path:filename>')
def serve_frontend_files(filename):
    return send_from_directory('TSSSF/frontend/', filename)


if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=DEBUG)
