import os
import subprocess
import shutil
import tempfile
import json
from flask import Flask
from flask import request

app = Flask(__name__)
volume_path = '/tmp' # Path for the images, set by the docker volume

@app.route('/')
def empty():
    return 'Hi there'
    
def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def debug(msg):
    print(msg)

@app.route('/<path:imagefile>')
def generate(imagefile):
    imagepath = os.path.join(volume_path,imagefile)
    debug("Starting image generation for " + imagepath)

    result = {}
    result['error'] = "Generation failed"

    if(not os.path.exists(imagepath)):
        result['error'] = "Image ("+imagepath+") not found"
        return json.dumps(result)

    #url = request.args.get('OPENWISP_URL', '')
    #uuid = request.args.get('OPENWISP_UUID', '')
    #key = request.args.get('OPENWISP_KEY', '')

    mountingpoint = tempfile.mkdtemp()
    
    # duplicate the imagefile to temp and mount
    newimage = tempfile.mkstemp(suffix='.img')[1]

    debug("Creating clone " + newimage)
    shutil.copyfile(imagepath,newimage)

    debug("Mounting image")
    #subprocess.call(['sudo', 'mount', '-o loop,offset=1048576',newimage,mountingpoint])
    p1 = subprocess.Popen(['mount', '-o','loop,offset=1048576',newimage,mountingpoint])
    p1.wait()
    
    # do the modifications
    # TODO: put all the modifications in a configuration file
    debug("Modifying image")
    touch(os.path.join(mountingpoint,"hello_there"))

    # close image
    debug("Unmounting image")
    #subprocess.call(['sudo', 'umount',mountingpoint])
    subprocess.call(['umount',mountingpoint])

    # move image to destination
    # TODO: find new name
    newimagename = "generated.img"
    shutil.move(newimage,os.path.join(volume_path,newimagename))

    result['error'] = ""
    result['image'] = newimagename
    return json.dumps(result)

#generate("newimage.img")

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')