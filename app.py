import os
import stat
import subprocess
import shutil
import tempfile
import json
import hashlib
from flask import Flask
from flask import request

# Constants
app = Flask(__name__)
input_path = 'images' # Input images
output_path = 'output' # Output images
volume_path = '/workdir' 
expected_extension = ".img"

@app.route('/')
def empty():
    images = []
    for file in os.listdir(os.path.join(volume_path,input_path)):
        if file.endswith(expected_extension):
            images.append(file)
    return json.dumps({"images": images})

def get_image_filename(image, params, output_prefix = '', output_postfix = ''):
    return output_prefix + hashlib.sha224((image + 
        json.dumps(params)).encode('utf8')).hexdigest() + output_postfix

def touch(path):
    with open(path, 'a'):
        os.utime(path, None)

def debug(msg):
    print(msg)

@app.route('/<path:imagefile>')
def generate(imagefile):
    imagepath = os.path.join(volume_path,input_path,imagefile)
    imagename_without_extension, imagename_extension = os.path.splitext(imagepath)
    
    # Json output
    result = {}
    debug("Starting image generation for " + imagepath)

    if(not os.path.exists(imagepath)) or not imagename_extension == expected_extension:
        result['error'] = "Image ("+imagepath+") not found"
        return json.dumps(result)

    args = {"OPENWISP_URL":"url", "OPENWISP_UUID":"uuid", "OPENWISP_KEY":"key", }
    try:
        args = request.args
    except:
        pass

    # Check if the image was generated in the past
    imagename_new = get_image_filename(imagefile, args, 
        os.path.basename(imagename_without_extension) + "-", expected_extension)

    if not os.path.exists(os.path.join(volume_path,output_path,imagename_new)):
        mountingpoint = tempfile.mkdtemp()
        
        # Duplicate the imagefile to temp and mount
        newimage = tempfile.mkstemp(suffix=expected_extension)[1]

        debug("Creating clone " + newimage)
        shutil.copyfile(imagepath,newimage)

        offset = 0
        try:
            with open(imagename_without_extension+'.offset', 'r') as m:
                offset=m.read().replace('\n', '')
        except:
            pass
        
        print ("Mounting image " + newimage + " (offset:"+offset+") to " + mountingpoint + " ...")
        proc_mount = subprocess.Popen(['mount', '-o','loop,offset='+offset,newimage,mountingpoint])
        proc_mount.wait()
        print ("... done.")
        
        # Do the modifications
        debug("Modifying image")
        touch(os.path.join(mountingpoint,"modified")) # Just a dumb flag

        update_image(imagename_without_extension,mountingpoint, args)

        # Close image
        print ("Unmounting image " + mountingpoint + " ...")
        proc_umount = subprocess.Popen(['umount',mountingpoint])
        proc_umount.wait()
        print ("... done.")

        # Move image to destination
        imagepath_new = os.path.join(volume_path,output_path,imagename_new)
        shutil.move(newimage,imagepath_new)
        os.chmod(imagepath_new, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

        # TODO: Clean old images

    # Output
    result['output_path'] = output_path
    result['output_file'] = imagename_new
    print ("Done: " + imagename_new)

    return json.dumps(result)

def update_image(source_image, destination_path, template_parameters):
    """
    Updates a mounted image.

    Parameters
    ----------
    source_image : str
        Path to the image
    destination_path : str
        Path to the destination (mount point)
    template_parameters : dict
        Dictionary with the template variables to be replaced in the .template files from the source

    Returns
    -------
    int
        Total number of injected files

    """
    print("Updating image:" + source_image)

    files_injected = 0
    template_ext = ".template"

    #imagename_without_extension, imagename_extension = os.path.splitext(source_imagename)

    for path, directories, files in os.walk(source_image):
        for f in files:

            destination_filename = f

            destination_relative_path = os.path.join(destination_path,path.split(source_image,2)[1].lstrip('/\\'))
            print("* Source path: '" + path + "' filename: '" + f + "' ---> " + os.path.join(destination_relative_path,destination_filename))
            # print("path" + path)
            # print("source_image: " + source_image)
            # print("destination_path: " + destination_path)
            # print("destination_relative_path: " + destination_relative_path)
            # print("destination_filename: " + destination_filename)

            source_path_filename = os.path.join(path, f)
            destination_path_and_filename = os.path.join(destination_relative_path,destination_filename)

            # Prepare destination directory tree
            tmp_path = os.path.join(destination_path,destination_relative_path)
            os.makedirs(tmp_path, exist_ok=True)

            if(f.endswith(template_ext)):
                print ('Processing .template: %s' % os.path.join(path, destination_filename))

                # Read in the file
                with open(source_path_filename, 'r') as file :
                    filedata = file.read()

                    try:
                        output = str(filedata) % template_parameters
                    except:
                        output = filedata

                    # Write the file out again
                    with open(os.path.join(destination_path,destination_relative_path,f[:-len(template_ext)]), 'w') as file:
                        file.write(output)
                        files_injected += 1

            else:
                print ('Copying: %s' % source_path_filename)
                shutil.copy(source_path_filename,destination_path_and_filename)
                files_injected += 1

    return files_injected

#generate("newimage.img")

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')