from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from functools import wraps
import os
from werkzeug.utils import secure_filename

SliderPath = "/static/images/SliderImages/"


# import functions
from SessionControl import Login_Required
from BotControl import is_Human
from allowed import allowed_file
# Flask App
app = Flask(__name__, static_url_path="/static", static_folder="static")


# Secret Key for Message Flashing
app.secret_key = "TosyaMensucat"

# reCAPTCHA PublicKey
pubkey = "Google ReCAPTCHA Public Key"

# Flask and MySQL Configuration
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "tmdb"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config["UPLOAD_FOLDER"] = "/Users/oozka/Desktop/Flask_Panel/static/images/SliderImages"

mysql = MySQL(app)

# Home Page TR
@app.route("/", methods = ["GET", "POST"])
def index():
    VisitorIp = request.remote_addr

    # Create a Cursor
    cursor = mysql.connection.cursor()

    # Create query of visitor
    query = "INSERT into visitor(visitor_ip) VALUES(%s)"

    cursor.execute(query,(VisitorIp,))
    mysql.connection.commit() #apply changes
    cursor.close() # Close cursor

    SliderCursor = mysql.connection.cursor()
    SliderQuery = "SELECT * from slider"

    SliderCursor.execute(SliderQuery)
    images = SliderCursor.fetchall()

    SliderCursor.close()

    return render_template("index.html", language = "tr", title = "Anasayfa", images = images, path = SliderPath)

@app.route("/Iletisim", methods = ["GET", "POST"])
def Contact():
    
    # Create Contact Cursor
    ContactCursor = mysql.connection.cursor()
    
    # Create Contact Query
    contact_query = "SELECT * FROM contact WHERE contact_id = %s"

    ContactCursor.execute(contact_query,(1,))

    ContactVar = ContactCursor.fetchone()

    # Close ContactCursor
    ContactCursor.close()


    if request.method == "POST":

        # Variables
        name = request.form["name"]
        phone = request.form["phone"]
        mail = request.form["mail"]
        msg = request.form["msg"]
        captcha_response = request.form["g-recaptcha-response"]

        # Create a Cursor
        cursor = mysql.connection.cursor()

        # Create Query
        query = "INSERT into messages(messages_sender_name, messages_phone, messages_mail, messages_message,messages_isread) VALUES(%s, %s, %s, %s, %s)"

        if is_Human(captcha_response):
            cursor.execute(query, (name, phone, mail, msg, 0))
            mysql.connection.commit()
            cursor.close()

            flash("Mesajınız Başarı ile Gönderilmiştir", "success")
            return redirect(url_for("Contact"))
        else:
            flash("reCaptcha Hatası", "danger")
            return redirect(url_for("Contact"))

    return render_template("Contact.html", title = "İletişim", pubkey = pubkey, contact = ContactVar)

# About Page
@app.route("/Hakkımızda", methods = ["GET", "POST"])
def About():

    # Create a cursor
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM about WHERE about_id = %s"

    cursor.execute(query, (1,))

    about = cursor.fetchone()
    cursor.close()

    return render_template("AboutPage.html", title = "Hakkımızda", about = about)

# Vision Page
@app.route("/Vizyonumuz", methods = ["GET", "POST"])
def Vision():

    # Create a cursor
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM vision WHERE vision_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    return render_template("Vision.html", title = "Vizyonumuz", data = data)

# Mission Page
@app.route("/Misyonumuz", methods = ["GET", "POST"])
def Mission():

    # Create a cursor
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM mission WHERE mission_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    return render_template("Mission.html", title = "Misyonumuz", data = data)

# -------------------- Admin Control Panel ---------------------

# Login Page
@app.route("/panel", methods =["GET", "POST"])
def PanelLogin():

    # If User Enters
    if request.method == "POST":

        # Take User Input Variables
        username = request.form["UserName"]
        password = request.form["password"]
        captcha_response = request.form["g-recaptcha-response"]

        # Create Cursor
        cursor = mysql.connection.cursor()

        # Query for UserName
        query = "SELECT * From users WHERE users_user_name = %s"
        
        # Run UserName Query
        result = cursor.execute(query,(username,))

        # reCAPTCHA CONTROL
        if is_Human(captcha_response):
            # If username exist
            if result > 0:
                user = cursor.fetchone()
                Real_Password = user["users_password"]

                # Enter Successfully
                if password == Real_Password:
                    flash("Başarı ile giriş yaptınız!", "success")

                    # Change Session
                    session["logged_in"] = True
                    session["username"] = username
                    cursor.close()

                    # Redirect Panel Home Page
                    return redirect(url_for("PanelHome"))

                # If password wrong
                else:
                    flash("Kullanıcı adı veya parola yanlış!", "danger")
                    return redirect(url_for("PanelLogin"))
            
            # if username wrong
            else:
                flash("Kullanıcı adı veya parola yanlış!", "danger")
                return redirect(url_for("PanelLogin"))
        else:
            flash("reCaptcha Hatası", "danger")
            return redirect(url_for("PanelLogin"))

    # Normal Panel Login Page
    return render_template("PanelLogin.html", title = "Panel Giriş", pubkey = pubkey)

# Panel Home Page
@app.route("/panel/Home")
@Login_Required
def PanelHome():
    
    # Create cursor
    cursor = mysql.connection.cursor()

    # Create q query
    query = "SELECT * FROM visitor"

    VisitorCount = cursor.execute(query)

    return render_template("PanelHome.html", title = "Panel Anasayfa", nav = "Home", VisitorCount = VisitorCount)

# Slider Images 
@app.route("/panel/SliderImagesSettings", methods = ["GET", "POST"])
@Login_Required
def Slider():

    cursor = mysql.connection.cursor()
    query = "SELECT * from slider"

    result = cursor.execute(query)

    if result == 0:
        flash("Henüz Resim Eklenmedi", "danger")

    images = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        file = request.files['file']

        if file.filename == '':
            flash("Dosya Seçilmedi!", "danger")
            return redirect(url_for("Slider"))
        
        if file and allowed_file(file.filename):

            # Create File Cursor
            FileCursor = mysql.connection.cursor()
            # Create File Query
            FileQuery = "INSERT into slider(slider_filename) VALUES(%s)"

            FileCursor.execute(FileQuery, (file.filename,))
            mysql.connection.commit()
            FileCursor.close()

            name = secure_filename(file.filename)
            # Save File
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], name))
            flash("Resim Başarı ile Kaydedildi", "success")
            
            return redirect(url_for("Slider"))

    return render_template("PanelSlider.html", title = "Slider Ayarları", nav = "Site Anasayfa", images = images)

# Vision Page
@app.route("/panel/SitePages/VisionPageSettings", methods = ["GET", "POST"])
@Login_Required
def VisionPageSettings():

    # Create a Cursor
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM vision WHERE vision_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":

        new = request.form["text"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE vision SET vision_text = %s WHERE vision_id = %s"

        UpdateCursor.execute(UpdateQuery, (new, 1))
        mysql.connection.commit()
        UpdateCursor.close()

        flash("Yazı Başarı ile Güncellendi", "success")
        return redirect(url_for("VisionPageSettings"))

    return render_template("PanelVision.html", title = "Vizyonumuz Sayfası Ayarları", nav = "Site Sayfaları", data = data)

# Mission Page
@app.route("/panel/SitePages/MissionPageSettings", methods = ["GET", "POST"])
@Login_Required
def MissionPageSettings():

    # Create a Cursor
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM mission WHERE mission_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":

        new = request.form["text"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE mission SET mission_text = %s WHERE mission_id = %s"

        UpdateCursor.execute(UpdateQuery, (new, 1))
        mysql.connection.commit()
        UpdateCursor.close()

        flash("Yazı Başarı ile Güncellendi", "success")
        return redirect(url_for("MissionPageSettings"))
    return render_template("PanelMission.html", title = "Misyonumuz Sayfası Ayarları", nav = "Site Sayfaları", data = data)

# Product Page
@app.route("/panel/SitePages/ProductPageSettings", methods = ["GET", "POST"])
@Login_Required
def ProductPageSettings():
    return render_template("PanelProduct.html", title = "Ürünlerimiz Sayfası Ayarları", nav = "Site Sayfaları")

# Panel Contact Page
@app.route("/panel/SitePages/PanelContactSettings", methods = ["GET", "POST"])
@Login_Required
def PanelContactSettings():

    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()


    return render_template("PanelContact.html", title = "İletişim Sayfası Ayarları", nav = "Site Sayfaları", data = data)

# Change Mail Page
@app.route("/panel/SitePages/PanelContactSettings/ChangeMail", methods = ["GET", "POST"])
@Login_Required
def ChangeMail():
    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        mail = request.form["NewMail"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE contact SET contact_mail = %s WHERE contact_id = %s"

        UpdateCursor.execute(UpdateQuery, (mail, 1))

        mysql.connection.commit()
        UpdateCursor.close()

        flash("E-posta Başarı ile Güncellendi!", "success")
        return redirect(url_for("PanelContactSettings"))

    return render_template("ChangeMail.html", title = "E-posta Değişim", nav = "Site Sayfaları", data = data)

# Change Phone Page
@app.route("/panel/SitePages/PanelContactSettings/ChangePhone", methods = ["GET", "POST"])
@Login_Required
def ChangePhone():
    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        phone = request.form["NewPhone"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE contact SET contact_phone = %s WHERE contact_id = %s"

        UpdateCursor.execute(UpdateQuery, (phone, 1))

        mysql.connection.commit()
        UpdateCursor.close()

        flash("Telefon Başarı ile Güncellendi!", "success")
        return redirect(url_for("PanelContactSettings"))

    return render_template("ChangePhone.html", title = "Telefon Değişim", nav = "Site Sayfaları", data = data)

# Change Address Page
@app.route("/panel/SitePages/PanelContactSettings/ChangeAddress", methods = ["GET", "POST"])
@Login_Required
def ChangeAddress():
    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        address = request.form["NewAddress"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE contact SET contact_address = %s WHERE contact_id = %s"

        UpdateCursor.execute(UpdateQuery, (address, 1))

        mysql.connection.commit()
        UpdateCursor.close()

        flash("Adres Başarı ile Güncellendi!", "success")
        return redirect(url_for("PanelContactSettings"))

    return render_template("ChangeAddress.html", title = "Adres Değişim", nav = "Site Sayfaları", data = data)

# Change iframe url Page
@app.route("/panel/SitePages/PanelContactSettings/ChangeMaps", methods = ["GET", "POST"])
@Login_Required
def ChangeMap():
    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        address = request.form["NewMap"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE contact SET contact_iframe = %s WHERE contact_id = %s"

        UpdateCursor.execute(UpdateQuery, (address, 1))

        mysql.connection.commit()
        UpdateCursor.close()

        flash("URL Başarı ile Güncellendi!", "success")
        return redirect(url_for("PanelContactSettings"))

    return render_template("ChangeMaps.html", title = "Harita URL Değişim", nav = "Site Sayfaları", data = data)

# Change facebook url Page
@app.route("/panel/SitePages/PanelContactSettings/ChangeFacebookLink", methods = ["GET", "POST"])
@Login_Required
def ChangeFace():
    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        facebook = request.form["NewFacebook"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE contact SET contact_facebook = %s WHERE contact_id = %s"

        UpdateCursor.execute(UpdateQuery, (facebook, 1))

        mysql.connection.commit()
        UpdateCursor.close()

        flash("URL Başarı ile Güncellendi!", "success")
        return redirect(url_for("PanelContactSettings"))

    return render_template("ChangeFacebook.html", title = "Facebook URL Değişim", nav = "Site Sayfaları", data = data)

# Change twitter url Page
@app.route("/panel/SitePages/PanelContactSettings/ChangeTwitterLink", methods = ["GET", "POST"])
@Login_Required
def ChangeTwitter():
    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        twitter = request.form["NewTwitter"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE contact SET contact_twitter = %s WHERE contact_id = %s"

        UpdateCursor.execute(UpdateQuery, (twitter, 1))

        mysql.connection.commit()
        UpdateCursor.close()

        flash("URL Başarı ile Güncellendi!", "success")
        return redirect(url_for("PanelContactSettings"))

    return render_template("ChangeTwitter.html", title = "Twitter URL Değişim", nav = "Site Sayfaları", data = data)

# Change instagram url Page
@app.route("/panel/SitePages/PanelContactSettings/ChangeInstagramLink", methods = ["GET", "POST"])
@Login_Required
def ChangeInsta():
    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        insta = request.form["NewInsta"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE contact SET contact_instagram = %s WHERE contact_id = %s"

        UpdateCursor.execute(UpdateQuery, (insta, 1))

        mysql.connection.commit()
        UpdateCursor.close()

        flash("URL Başarı ile Güncellendi!", "success")
        return redirect(url_for("PanelContactSettings"))

    return render_template("ChangeInstagram.html", title = "Instagram URL Değişim", nav = "Site Sayfaları", data = data)

# Change Linkedin url Page
@app.route("/panel/SitePages/PanelContactSettings/ChangeLinkedinLink", methods = ["GET", "POST"])
@Login_Required
def ChangeLinkedIn():
    # Create Cursor 
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM contact WHERE contact_id = %s"

    cursor.execute(query, (1,))

    data = cursor.fetchone()
    cursor.close()

    if request.method == "POST":
        link = request.form["NewLink"]

        UpdateCursor = mysql.connection.cursor()
        UpdateQuery = "UPDATE contact SET contact_linkedin = %s WHERE contact_id = %s"

        UpdateCursor.execute(UpdateQuery, (link, 1))

        mysql.connection.commit()
        UpdateCursor.close()

        flash("URL Başarı ile Güncellendi!", "success")
        return redirect(url_for("PanelContactSettings"))

    return render_template("ChangeLinkedin.html", title = "Linked-In URL Değişim", nav = "Site Sayfaları", data = data)

# Panel Messages
@app.route("/panel/Messages")
@Login_Required
def Messages():

    # Create cursor
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * FROM messages"
    result = cursor.execute(query)

    if result == 0:
        flash("Mesaj Kutunuz Boş", "succes")

    
    messages = cursor.fetchall()

    return render_template("PanelMessages.html", title = "Site Mesajları", nav = "Messages", messages = messages)

# Message Show
@app.route("/panel/Messages/Show/<string:messages_id>", methods = ["GET", "POST"])
@Login_Required
def ShowMessage(messages_id):


    # Create a Cursor
    cursor = mysql.connection.cursor()

    # Create a query
    query = "SELECT * From messages where messages_id = %s"
    cursor.execute(query,(messages_id,))
    data = cursor.fetchone()
    cursor.close()

    if data["messages_isread"] == 0:
        
        # Create Update Cursor
        UpdateCursor = mysql.connection.cursor()
        # Update Query
        UpdateQuery = "UPDATE messages SET messages_isread = '1' WHERE messages_id = %s"

        UpdateCursor.execute(UpdateQuery,(messages_id,))
        mysql.connection.commit() #apply changes
        UpdateCursor.close()


    return render_template("PanelShowMessages.html", title = "Site Mesajı", message = data, nav = "Messages")

# Delete Message
@app.route("/panel/Messages/DelMessage/<string:messages_id>", methods = ["GET", "POST"])
@Login_Required
def DeleteMessage(messages_id):
    
    # Create a Cursor
    cursor = mysql.connection.cursor()

    # Create a Query
    query = "DELETE FROM messages WHERE messages_id = %s"

    cursor.execute(query, (messages_id,))
    mysql.connection.commit() #apply changes
    cursor.close()

    flash("Mesajınız Başarı İle Silinmiştir", "success")
    return redirect(url_for("Messages"))

# Settings Page
@app.route("/panel/Settings", methods = ["GET", "POST"])
@Login_Required
def Settings():

    # Create Cursor
    cursor = mysql.connection.cursor()
    
    # Query
    query = "SELECT * from users WHERE users_user_name = %s"
    cursor.execute(query,(session['username'],))
    
    # Get user's variables
    user = cursor.fetchone()
    cursor.close()

    return render_template("PanelSettings.html", title = "Kullanıcı Ayarları", user = user, nav = "Settings")

# Change Name Page 
@app.route("/panel/Settings/ChangeName", methods = ["GET", "POST"])
@Login_Required
def ChangeName():
    # Create Cursor
    cursor = mysql.connection.cursor()
    
    # Query
    query = "SELECT * from users WHERE users_user_name = %s"
    cursor.execute(query,(session['username'],))
    
    # Get user's variables
    user = cursor.fetchone()
    cursor.close()

    # If the form get post
    if request.method == "POST":
        # Create Update Cursor
        UpdateCursor = mysql.connection.cursor()

        # Create Update Query
        UpdateQuery = "UPDATE users SET users_name = %s WHERE users_user_name = %s"

        NewName = request.form["NewName"]
        UpdateCursor.execute(UpdateQuery, (NewName, session["username"]))
        mysql.connection.commit()
        UpdateCursor.close()
        flash("Kullanıcı Adı ve Soyadı Başarı ile Güncellendi!", "success")
        
        # Redirect Panel Home Page
        return redirect(url_for("PanelHome"))

    return render_template("ChangeName.html", title = "Kullanıcı Adı Soyadı Değişim Formu", nav = "Settings", user = user)

# Change UserName Page 
@app.route("/panel/Settings/ChangeUserName", methods = ["GET", "POST"])
@Login_Required
def ChangeUserName():
    # Create Cursor
    cursor = mysql.connection.cursor()
    
    # Query
    query = "SELECT * from users WHERE users_user_name = %s"
    cursor.execute(query,(session['username'],))
    
    # Get user's variables
    user = cursor.fetchone()
    cursor.close()

    # If the form get post
    if request.method == "POST":
        # Create Update Cursor
        UpdateCursor = mysql.connection.cursor()

        # Create Update Query
        UpdateQuery = "UPDATE users SET users_user_name = %s WHERE users_user_name = %s"

        NewUserName = request.form["NewUserName"]
        UpdateCursor.execute(UpdateQuery, (NewUserName, session["username"]))
        mysql.connection.commit()

        # Update Session
        session["username"] = NewUserName

        UpdateCursor.close()
        flash("Kullanıcı Adı Başarı ile Güncellendi!", "success")
        
        # Redirect Panel Home Page
        return redirect(url_for("PanelHome"))

    return render_template("ChangeUserName.html", title= "Kullanıcı Adı Değişim Formu", nav = "Settings", user = user)

# Change Password Page 
@app.route("/panel/Settings/ChangePassword", methods = ["GET", "POST"])
@Login_Required
def ChangePassword():

    # Create Cursor
    cursor = mysql.connection.cursor()
    
    # Query
    query = "SELECT * from users WHERE users_user_name = %s"
    cursor.execute(query,(session['username'],))
    
    # Get user's variables
    user = cursor.fetchone()
    cursor.close()

    # If the form get post
    if request.method == "POST":
        # Create Update Cursor
        UpdateCursor = mysql.connection.cursor()

        # Create Update Query
        UpdateQuery = "UPDATE users SET users_password = %s WHERE users_user_name = %s"

        # Passwords
        Old = request.form["OldPassword"]
        New = request.form["NewPassword"]
        Confirm = request.form["ConfirmPassword"]

        if user["users_password"] == Old:
            if New == Confirm:
                UpdateCursor.execute(UpdateQuery, (New, session["username"]))
                mysql.connection.commit()
                UpdateCursor.close()
                flash("Parolanız Başarı ile Güncellendi!", "success")
                return redirect(url_for("PanelHome"))
            
            # If passwords do not matched
            else:
                flash("Parolalar Uyuşmuyor!", "danger")
                return redirect(url_for("ChangePassword"))
        
        # If old password is wrong
        else:
            flash("Eski Parolanız Hatalı!", "danger")
            return redirect(url_for("ChangePassword"))
    
    # Default
    return render_template("ChangePassword.html", title= "Kullanıcı Adı Değişim Formu", nav = "Settings", user = user)

# Logout Function
@app.route("/panel/Logout")
def Logout():
    # Clear Session
    session.clear()
    flash("Başarıyla çıkış yaptınız!", "success")
    return redirect(url_for("PanelLogin"))

# -------------------- Admin Control Panel End ----------------------------------

# Start Flask App
if __name__ == "__main__":
    app.run(debug = True)
