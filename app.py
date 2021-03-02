import pyrebase
import re
from flask import *
#firestore
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import storage
import os
from werkzeug.utils import secure_filename

cred=credentials.Certificate(r"C:\Users\91798\PycharmProjects\firebase\test1-32373-firebase-adminsdk-ii7lw-2d9db38b47.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'test1-32373.appspot.com'
})

bucket = storage.bucket()
db = firestore.client()
#firestore end
config ={
    #Add your firebase configuration 
}

firebase=pyrebase.initialize_app(config)

auth=firebase.auth()

arrayRemove = firebase_admin.firestore.ArrayRemove



app=Flask(__name__)

app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'

@app.route("/")
def home():
    users_ref = db.collection(u'userdata')
    docs = users_ref.stream()
    k={}
    likes=[]
    dislikes=[]
    for doc in docs:
        z=[]
        s = str(doc.id).split("@")
        x=s[0]
        y=doc.to_dict()['post']
        likes=doc.to_dict()['like']
        dislikes=doc.to_dict()['dislike']
        likedby=doc.to_dict()['likedby']
        #t = str(doc.to_dict()).split(":")
        #y=t[1][:-1]
        z.append(y)
        z.append(likes)
        z.append(dislikes)
        z.append(likedby)
        k[x]=z
    return render_template("new.html",session=session,data=k)

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["pass"]
        confirmpassword=request.form["cpass"]
        if password!=confirmpassword:
            flash("Password and Confirm password does not match","danger")
            return redirect(url_for("register"))
        elif len(password) < 8:
            flash("Make sure your password is at lest 8 letters","danger")
            return redirect(url_for("register"))
        elif re.search('[0-9]', password) is None:
            flash("Make sure your password has a number in it","danger")
            return redirect(url_for("register"))
        elif re.search('[A-Z]', password) is None:
            flash("Make sure your password has a capital letter in it","danger")
            return redirect(url_for("register"))
        try :
            user=auth.create_user_with_email_and_password(email,password)
            auth.send_email_verification(user['idToken'])
            z=auth.get_account_info(user['idToken']).get("users")
            veri=z[0].get("emailVerified")
            flash("Your account has been created. Please verify on gmail to login","success")
            return redirect(url_for("login"))
        except:
            flash("Email already exists","danger")
            return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method == "POST" and "uemail" not in session:
        email = request.form["email"]
        password = request.form["pass"]
        try :
            user = auth.sign_in_with_email_and_password(email,password)
            if auth.get_account_info(user['idToken']).get("users")[0].get("emailVerified")==True:
                session["uemail"] = email
                return redirect(url_for("account"))
            else :
                return redirect(url_for("login"))
        except Exception as e:
            flash("Either user is not registered or password is incorrect")
    elif "uemail" in session:
        return redirect(url_for("account"))
    return render_template("login.html")

@app.route("/user")
def account():
    if "uemail" in session:
        data=session["uemail"]
        if os.path.isfile("static\\"+data.split("@")[0]+".jpg")==False:
            imagefile = url_for('static', filename="default1.jpg")
        else :
            imagefile=url_for('static',filename=data.split("@")[0]+".jpg")
        return render_template("account.html",data=data,imagefile=imagefile)
    else:
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("uemail",None)
    return redirect(url_for("login"))

@app.route("/recovery",methods=['GET','POST'])
def recover():
    if request.method=="POST":
        email = request.form["recoveremail"]
        auth.send_password_reset_email(email)
        flash("Password reset mail send to your mail","success")
        return redirect(url_for("login"))

@app.route("/userpost",methods=["GET","POST"])
def userpost():
    if request.method=="POST":
        data=session["uemail"]
        post=request.form["upost"]
        doc_ref = db.collection(u'userdata').document(data)
        doc_ref.set({
            u'post': post,
            u'like': 0,
            u'dislike' : 0,
            u'likedby': [] ,
            u'dislikedby':[]
        })
    return redirect("user")

@app.route("/like",methods=['GET','POST'])
def like():
    if request.method=="POST":
        email=request.form.get("user")
        btn=request.form.get("opinion")
        mail=email+"@gmail.com"
        if btn == "liked" and session["uemail"] not in db.collection(u'userdata').document(mail).get().to_dict()["likedby"] :
                e=mail
                if db.collection(u'userdata').document(e).get().to_dict()["dislike"] >0:
                    doc_ref = db.collection(u'userdata').document(e)
                    doc_ref.update({
                        u'dislike': firestore.Increment(-1)

                    })
                doc_ref = db.collection(u'userdata').document(e)
                doc_ref.update({
                    u'like': firestore.Increment(1)

                })
                doc_ref.update({u'likedby': firestore.ArrayUnion([session["uemail"]])})
        elif btn=="disliked" and session["uemail"] not in db.collection(u'userdata').document(mail).get().to_dict()["dislikedby"]:
                e=mail
                if db.collection(u'userdata').document(e).get().to_dict()["like"] >0:
                    doc_ref = db.collection(u'userdata').document(e)
                    doc_ref.update({
                        u'like': firestore.Increment(-1)

                    })
                    doc_ref = db.collection(u'userdata').document(e)
                    doc_ref.update({
                        u'likedby': [],
                    })
                doc_ref = db.collection(u'userdata').document(e)
                doc_ref.update({
                    u'dislike': firestore.Increment(1)
                })
                doc_ref.update({u'dislikedby': firestore.ArrayUnion([session["uemail"]])})
        else :
            flash("You already liked or disliked earlier","success")
    return redirect(url_for("home"))

app.config['UPLOAD_FOLDER'] = r"C:\Users\91798\PycharmProjects\firebase\static"

@app.route("/profile",methods=['GET','POST'])
def profile():
    if request.method=="POST":
        data=session["uemail"]
        file = request.files['filename']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], data.split("@")[0] +"."+ filename.split(".")[1]))
        image = bucket.blob(session["uemail"])
        filename = secure_filename(file.filename)
        imagePath = r"C:\\Users\\91798\\PycharmProjects\\firebase\\static" + "\\" + data.split("@")[0] +"."+ filename.split(".")[1]
        # imageBlob = bucket.blob("i.jpg")
        image.upload_from_filename(imagePath)
        imagefile = url_for('static',filename=filename)
        os.remove('static/'+data.split("@")[0]+".jpg")
        image.download_to_filename("static\\"+data.split("@")[0]+".jpg")
        return render_template("account.html",data=session["uemail"],imagefile=imagefile)
    return redirect(url_for('userpost'))

if __name__=="__main__":
    app.run(debug=True)