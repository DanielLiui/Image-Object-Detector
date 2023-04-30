
from flask import Flask, render_template, url_for, redirect, request, jsonify
from werkzeug.utils import secure_filename
import io, os, shutil, zipfile
from google.cloud import vision

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "C:/Users/danie/OneDrive/Documents/Home/Flask/API test/resources/object-detection-website-9d1b0e0a3494.json"
app = Flask(__name__)
UPLOAD_FOLDER = 'static/user_imgs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
img_detects = [];  table_imgs = []
selImg_i = -1


#functz
def print_imgDetects():
    global img_detects

    print("img_detects: ")
    for img in img_detects:
        print(str(img) + "\n")


def print_imgDetect(img):
    print("img_name: " + img["img_name"])
    print("img_path: " + img["img_path"])
    print("Detections: ")

    for obj in img["detections"]:
        print("name: " + obj.name + " | score: " + str(obj.score))

    print("")


def detect_objs(img_path):
    client = vision.ImageAnnotatorClient()

    with open(img_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    objects = client.object_localization(image=image).localized_object_annotations

    '''
    for obj in objects:
        print('\n{} (confidence: {})'.format(obj.name, obj.score))
        print('Normalized bounding polygon vertices: ')
        for vertex in obj.bounding_poly.normalized_vertices:
            print(' - ({}, {})'.format(vertex.x, vertex.y))
    '''
    return objects

            
def get_tableImgs2(det_obj):
    global img_detects
    table_imgs = []

    if det_obj == "":  #leave contains & acc = ""
        for img in img_detects:
            table_img = {}
            table_img["img_name"] = img["img_name"]
            table_img["contains"] = ""
            table_img["acc"] = ""
            table_imgs.append(table_img)

    else:
        pass

    print("Returning table_imgs: " + str(table_imgs))
    return table_imgs


def get_tableImgs(det_obj):
    global img_detects, table_imgs
    table_imgs.clear()

    if det_obj == "":  #leave contains & acc = ""
        for img in img_detects:
            table_img = {}
            table_img["img_name"] = img["img_name"]
            table_img["contains"] = "";  table_img["acc"] = ""
            table_imgs.append(table_img)


    else:
        for img in img_detects:
            contains = False;  table_img = {}
            table_img["img_name"] = img["img_name"]

            for obj in img["detections"]:
                if obj.name.lower() == det_obj.lower():
                    contains = True;  table_img["contains"] = "Y"
                    table_img["acc"] = str(round(obj.score * 100)) + '%'
                    print(table_img["img_name"] + " contains " + obj.name)
                    break

            if contains == False:
                table_img["contains"] = "N";  table_img["acc"] = ""
                print(table_img["img_name"] + " doesn't contain " + obj.name)

            table_imgs.append(table_img)

    print("\nReturning table_imgs: ")
    for table_img in table_imgs:
        print(str(table_imgs))
    return table_imgs


#routes
@app.route("/")
def fresh_pg():
    global img_detects, table_imgs, selImg_i

    for fname in os.listdir("static/user_imgs/"):
        os.remove("static/user_imgs/" + fname)

    img_detects.clear();  table_imgs.clear();  selImg_i = -1
    return redirect("/home")


@app.route("/home")  #curr state
def home():
    global img_detects, table_imgs, sel_img_i

    if selImg_i < -1 or selImg_i >= len(img_detects):
        return "Invalid selected img index"

    print("selImg_i = " + str(selImg_i))
    if selImg_i == -1:
        return render_template("index.html", table_imgs=table_imgs, img_sel=False, detections=[])

    else: 
        img_det = img_detects[selImg_i];  print("selImg_i: " + str(selImg_i))
                                
        return render_template("index.html", table_imgs=table_imgs, img_sel=True, 
        sel_img_link=img_det["img_name"], detections=img_det["detections"])  #regardless if empty or not


@app.route("/instructions")
def instructions():
    return render_template("instructions.html")  #code 


@app.route("/clear")  
def clear():
    return redirect("/")


@app.route("/index/sel_img/<int:new_selImg_i>")
def select(new_selImg_i):
    global selImg_i;  selImg_i = new_selImg_i
    return redirect("/home")


@app.route("/detect", methods=["POST"])
def detect():
    global img_detects, table_imgs
    det_obj = request.form["det_obj"]
    table_imgs = get_tableImgs(det_obj)

    return redirect("/home")



@app.route("/upload", methods=["GET", "POST"]) #review, impl get_tableImgs()
def upload():
    global img_detects, table_imgs, selImg_i
    detections = {}

    if request.method == "GET": return redirect("/home")

    f = request.files['file']
    if not f: return redirect("/home")
    f.filename = f.filename.replace(" ", "_")

    if f.filename.endswith('.zip') == False:  #single img
        fpath = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(f.filename))  
        f.save(fpath);  print("Saving img to path: " + fpath)
        img_detect = {}
        img_detect["img_name"] = f.filename; 
        img_detect["img_path"] = fpath
        img_detect["detections"] = detect_objs(fpath)
        img_detects.append(img_detect)
        print("Adding img_detect: ", end="");  print_imgDetect(img_detect)

    else:  #zip                                      
        with zipfile.ZipFile(f, 'r') as zip_ref:
            zip_ref.extractall("static/upload_folders")

        #copy to user_imgs
        dot_i = f.filename.index('.');  zip_dir = f.filename[:dot_i]
        src = "static/upload_folders/" + zip_dir + "/"
        dest = "static/user_imgs/"

        for fname in os.listdir(src):
            shutil.copy(src + fname, dest + fname)
            img_detect = {}
            img_detect["img_name"] = fname
            img_detect["img_path"] = "static/user_imgs/" + fname
            img_detect["detections"] = detect_objs(img_detect["img_path"]) 
            img_detects.append(img_detect)
            print("Adding img_detect: ", end="");  print_imgDetect(img_detect)
           
        shutil.rmtree(src)
        fnames = os.listdir(dest);  print("fnames: " + str(fnames))


    selImg_i = len(img_detects)-1
    last_img = img_detects[selImg_i]
    table_imgs = get_tableImgs("")
    return render_template("index.html", table_imgs=table_imgs, img_sel=True,  
    sel_img_link=last_img["img_name"], detections=last_img["detections"])

'''
if __name__ == "__main__":
    print("Visit: ")
    print("http://127.0.0.1:8000/")
    print("http://127.0.0.1:8000/test2")
    #app.run(port=8001, debug=True)
    app.run(host='0.0.0.0', port=8080)
'''

