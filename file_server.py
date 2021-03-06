ffrom flask import Flask, make_response, request, session, render_template, send_file, Response, redirect
from flask.views import MethodView
from werkzeug import secure_filename
from datetime import datetime
from requests import get
from xml.dom import minidom
import urllib2
import humanize
import os
import re
import stat
import json
import mimetypes

app = Flask(__name__, static_url_path='/assets', static_folder='assets')
root = os.path.expanduser('')

'''
ignored = ['.bzr', '$RECYCLE.BIN', '.DAV', '.DS_Store', '.git', '.hg', '.htaccess', '.htpasswd', '.Spotlight-V100', '.svn', '__MACOSX', 'ehthumbs.db', 'robots.txt', 'Thumbs.db', 'thumbs.tps']
datatypes = {'audio': 'm4a,mp3,oga,ogg,webma,wav', 'archive': '7z,zip,rar,gz,tar', 'image': 'gif,ico,jpe,jpeg,jpg,png,svg,webp', 'pdf': 'pdf', 'quicktime': '3g2,3gp,3gp2,3gpp,mov,qt', 'source': 'atom,bat,bash,c,cmd,coffee,css,hml,js,json,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml,plist', 'text': 'txt', 'video': 'mp4,m4v,ogv,webm', 'website': 'htm,html,mhtm,mhtml,xhtm,xhtml'}
icontypes = {'fa-music': 'm4a,mp3,oga,ogg,webma,wav', 'fa-archive': '7z,zip,rar,gz,tar', 'fa-picture-o': 'gif,ico,jpe,jpeg,jpg,png,svg,webp', 'fa-file-text': 'pdf', 'fa-film': '3g2,3gp,3gp2,3gpp,mov,qt', 'fa-code': 'atom,plist,bat,bash,c,cmd,coffee,css,hml,js,json,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml', 'fa-file-text-o': 'txt', 'fa-film': 'mp4,m4v,ogv,webm', 'fa-globe': 'htm,html,mhtm,mhtml,xhtm,xhtml'}
'''

'''
@app.template_filter('size_fmt')
def size_fmt(size):
    return humanize.naturalsize(size)

@app.template_filter('time_fmt')
def time_desc(timestamp):
    mdate = datetime.fromtimestamp(timestamp)
    str = mdate.strftime('%Y-%m-%d %H:%M:%S')
    return str

@app.template_filter('data_fmt')
def data_fmt(filename):
    t = 'unknown'
    for type, exts in datatypes.items():
        if filename.split('.')[-1] in exts:
            t = type
    return t

@app.template_filter('icon_fmt')
def icon_fmt(filename):
    i = 'fa-file-o'
    for icon, exts in icontypes.items():
        if filename.split('.')[-1] in exts:
            i = icon
    return i

@app.template_filter('humanize')
def time_humanize(timestamp):
    mdate = datetime.utcfromtimestamp(timestamp)
    return humanize.naturaltime(mdate)
'''

def get_type(mode):
    if stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        type = 'dir'
    else:
        type = 'file'
    return type

def partial_response(path, start, end=None):
    file_size = os.path.getsize(path)

    if end is None:
        end = file_size - start - 1
    end = min(end, file_size - 1)
    length = end - start + 1

    with open(path, 'rb') as fd:
        fd.seek(start)
        bytes = fd.read(length)
    assert len(bytes) == length

    response = Response(
        bytes,
        206,
        mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True,
    )
    response.headers.add(
        'Content-Range', 'bytes {0}-{1}/{2}'.format(
            start, end, file_size,
        ),
    )
    response.headers.add(
        'Accept-Ranges', 'bytes'
    )
    return response

def get_range(request):
    range = request.headers.get('Range')
    m = re.match('bytes=(?P<start>\d+)-(?P<end>\d+)?', range)
    if m:
        start = m.group('start')
        end = m.group('end')
        start = int(start)
        if end is not None:
            end = int(end)
        return start, end
    else:
        return 0, None

#test_list = ['artifact1.tar.gz', 'test/artifact2.tar.gz', 'test/artifact3.tar.gz', 'test/folder/artifact4.tar.gz','test/folder/artifact5.tar.gz', 'test/folder/folder2/artifact6.tar.gz', 'test/folder/folder3/artifact7.tar.gz'] #

storage_name = "ifilimonau"
container_name = "test"

xml_url = 'https://%s.blob.core.windows.net/%s?restype=container&comp=list' % (storage_name, container_name)
download_link = 'https://%s.blob.core.windows.net/%s/%s' % (storage_name, container_name, file)

def xml_bring_names(link):
    artifact_list = []
    xmldoc = minidom.parse(urllib2.urlopen(link))
    itemlist = xmldoc.getElementsByTagName('Name')

    max_count = len(itemlist)
    current_count = 0
    for current_count in range(max_count):
        file = str(itemlist[current_count].childNodes[0].nodeValue)
#        print(file)
        artifact_list.append(file)
    return artifact_list


def get_all_folders(somelist): #  get list of all folders, based on xml
    dirlist = []
    for elem in somelist:
        folder = os.path.dirname(elem) + "/"
        dirlist.append(folder)
    unique = list(set(dirlist))
    # set(dirlist) - for removing duplicates from a sequence
    # list() takes sequence types and converts them to lists

    updated = ["" if elem == "/" else elem for elem in unique]
    return updated

# ['test/folder22/', 'test/folder/', 'test/directory/', '', 'test/folder21/', 'test/folder2/', 'test/']

def get_files_list(filelist, dir=''): #  get all files and folders from $dir
    file_list = []
    dir_list = []
    my_regex = re.compile(r"%s(\w+\/)" % (dir + "/"))

    dir_corrected = dir + "/"

    for elem in filelist:
        if dir_corrected in elem or dir_corrected == "/":
#        if dir == elem.rpartition('/')[0]:  # !!!!!!!!!!!!!!!
#            print("i'm here")
            if os.path.dirname(elem) == dir:
                file_list.append(os.path.basename(elem))
            else:
                if dir == "":
                    elem = "/" + elem
                result = my_regex.match(elem)
                dir_list.append(result.group(1))

    dir_list = list(set(dir_list))

    for x in dir_list:
        file_list.append(x)
    return file_list


def dir_or_file(somestring):
    if somestring[-1] == "/":
        return "dir"
    else:
        return "file"


class PathView(MethodView):
    def get(self, p=''):
        hide_dotfile = request.args.get('hide-dotfile', request.cookies.get('hide-dotfile', 'no'))

        path = os.path.join(root, p)
        files = xml_bring_names(xml_url)

        if path in get_all_folders(files):
            print(get_all_folders(files))
            contents = []
            for filename in get_files_list(files, path[:-1]):
#                print(get_files_list(files, path[:-1]))
                info = {}
                info['type'] = dir_or_file(filename)
                if info['type'] == "dir":
                    info['name'] = filename[:-1]
                else:
                    info['name'] = filename
#                print(info)
                contents.append(info)
            page = render_template('index.html', path=p, contents=contents, hide_dotfile=hide_dotfile)
            result = make_response(page, 200)
            result.set_cookie('hide-dotfile', hide_dotfile, max_age=16070400)
        elif path in files:
            download_link = 'https://%s.blob.core.windows.net/%s/%s' % (storage_name, container_name, path)
            result = redirect(download_link, 301)
        else:
            result = make_response('Not found', 404)
        return result


    def post(self, p=''):
        path = os.path.join(root, p)
        info = {}
        if os.path.isdir(path):
            files = request.files.getlist('files[]')
            for file in files:
                try:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(path, filename))
                except Exception as e:
                    info['status'] = 'error'
                    info['msg'] = str(e)
                else:
                    info['status'] = 'success'
                    info['msg'] = 'File Saved'
        else:
            info['status'] = 'error'
            info['msg'] = 'Invalid Operation'
        res = make_response(json.JSONEncoder().encode(info), 200)
        res.headers.add('Content-type', 'application/json')
        return res

path_view = PathView.as_view('path_view')
app.add_url_rule('/', view_func=path_view)
app.add_url_rule('/<path:p>', view_func=path_view)

if __name__ == "__main__":
    #app.run('0.0.0.0', 8000, threaded=True, debug=False)
    app.run() # run in http://127.0.0.1:5000 (see this message from konsole) if run through "python file_server.py"
