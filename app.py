from flask import Flask, render_template, url_for, request, redirect, session
import re
import pandas as pd
from datetime import datetime
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
factory = StemmerFactory()
stemmer = factory.create_stemmer()
import mysql.connector
import os
import json

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import confusion_matrix


app=Flask(__name__)
app.secret_key=os.urandom(24)
#Konek Database
conn=mysql.connector.connect(host="localhost",user="root",password="",database="klasifikasiforensik")
cursor=conn.cursor()
now = datetime.now()

#Routing halaman Login
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html')

#Routing halaman Register
@app.route('/register')
def register():
    return render_template('register.html')

#Routing halaman dashboard
@app.route('/index')
def dashboard():
    if 'user_id' in session:
        cursor = conn.cursor()
        #SELECT TABEL Kumpulankata
        cursor.execute("SELECT * FROM kumpulankata")
        #Ambil semua row pada tabel
        kk = cursor.fetchall()
        #Memutuskan koneksi ke server
        cursor.close()

        #Membuat variabel arr untuk menyimpan data pada array
        arr = []
        count=0
        for x in kk:
            count=count+1
            arr.append({
            'id_kata':x[0],
            'no':count,
            'kata':x[1],
            })
        return render_template('index.html', kumpulankata=arr)
    else:
        return redirect('/')

#Simpan Data Kata
@app.route('/simpandatakata', methods=["POST"])
def simpandatakata():
    #Request Form dari modal
    katapelecehan = request.form['katapelecehan']
    #Membuat objek yaitu cursor untuk mengeksekusi perintah SQL atau query
    cursor = conn.cursor()
    #Insert pada tabel kumpulankata
    cursor.execute("INSERT INTO kumpulankata (kata) VALUES (%s)",(katapelecehan,))
    #Simpan perubahan pada database
    conn.commit()
    return redirect(url_for('dashboard'))

#Routing Update
@app.route('/update', methods=["POST","GET"])
def update():
    if request.method == 'POST':
        id_kata = request.form['id_kata']
        katapelecehan = request.form['katapelecehan']
        cursor = conn.cursor()
        cursor.execute("UPDATE kumpulankata SET kata=%s WHERE id_kata=%s",(katapelecehan,id_kata,))
        conn.commit()
        return redirect(url_for('dashboard'))

@app.route('/hapus/<string:id_kata>', methods=["GET"])
def hapus(id_kata):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM kumpulankata WHERE id_kata=%s",(id_kata,))
    conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/login_validation', methods=['POST'])
def login_validation():
    username=request.form.get('username')
    password=request.form.get('password')
    cursor.execute("""SELECT * FROM `user` WHERE `username` LIKE '{}' AND `password` LIKE '{}'"""
                   .format(username,password))
    user=cursor.fetchall()
    if len(user)>0:
        session['user_id']=user[0][0]
        return redirect('/index')
    else:
        return redirect('/')
    
@app.route('/logout')
def logout():
    session.pop('user_id')
    return redirect('/')

@app.route('/add_user', methods=['POST'])
def add_user():
    username=request.form.get('username')
    password=request.form.get('password')
    cursor.execute("""INSERT INTO `user` (`user_id`,`username`,`password`) VALUES (NULL,'{}','{}')""".format(username,password))
    conn.commit()
    
    cursor.execute("""SELECT * FROM `user` WHERE `username` LIKE '{}'""".format(username))
    myuser=cursor.fetchall()
    session['user_id']=myuser[0][0]
    return redirect('/')

@app.route('/dataset')
def dataset():
    if 'user_id' not in session:
        return redirect('/')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dataset")
    myresult = cursor.fetchall()

    arr = []
    count=0
    for x in myresult:
        count=count+1
        arr.append({
            'no':count,
            'percakapan':x[0],
            'kelas':x[1],
            })
    
    return render_template('dataset.html', data=arr)

@app.route('/importdataset', methods=['GET','POST'])
def importdataset():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('dataset'))
        file = request.files['file']
        excel = pd.read_excel(file)

        cursor = conn.cursor()
        cursor.execute("DELETE FROM dataset")
        conn.commit()

        sql = "INSERT INTO dataset (percakapan,kelas) VALUES (%s,%s)"

        tupp = []
        counter=-1
        for x in excel["percakapan"]:
            counter=counter+1
            tupp.append((x,excel["kelas"][counter]))

        cursor.executemany(sql,tupp)
        conn.commit()

        return redirect(url_for("dataset"))
    
@app.route('/datasetdua')
def datasetdua():
    if 'user_id' not in session:
        return redirect('/')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasetdua")
    myresult = cursor.fetchall()

    arr = []
    count=0
    for x in myresult:
        count=count+1
        arr.append({
            'no':count,
            'percakapan':x[0],
            'kelas':x[1],
            })
    
    return render_template('datasetdua.html', data=arr)

@app.route('/importdatasetdua', methods=['GET','POST'])
def importdatasetdua():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(url_for('datasetdua'))
        file = request.files['file']
        excel = pd.read_excel(file)

        cursor = conn.cursor()
        cursor.execute("DELETE FROM datasetdua")
        conn.commit()

        sql = "INSERT INTO datasetdua (percakapan,kelas) VALUES (%s,%s)"

        tupp = []
        counter=-1
        for x in excel["percakapan"]:
            counter=counter+1
            tupp.append((x,excel["kelas"][counter]))

        cursor.executemany(sql,tupp)
        conn.commit()

        return redirect(url_for("datasetdua"))
    
@app.route('/prosestext')
def prosestext():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dataset")
    myresult = cursor.fetchall()

    factory = StopWordRemoverFactory()
    stopword = factory.create_stop_word_remover()

    payload = []

    for x in myresult:
        #### MELAKUKAN PROSES STEMMING STOPWORD BAHASA INDONESIA
        satu = stopword.remove(x[0])
        #### MENGHILANGKAN TEXT TIDAK PENTING SEPERTI HASHTAG DAN MENTION
        dua = re.sub(r"@[^\s]+"," ",satu)
        dua = re.sub(r"#[^\s]+"," ",dua)
        dua = re.sub(r"\."," ",dua)
        dua = re.sub(r"http[^\s]+"," ",dua)
        dua = re.sub(r"\?"," ",dua)
        dua = re.sub(r","," ",dua)
        dua = re.sub(r"”"," ",dua)
        dua = re.sub(r"co/[^\s]+"," ",dua)
        dua = re.sub(r":'\)"," ",dua)
        dua = re.sub(r":\)","",dua)
        dua = re.sub(r"&"," ",dua)
        dua = re.sub(r'\"([^\"]+)\"',"\g<1>",dua)
        dua = re.sub(r'\([^\)]+\"',"",dua)
        dua = re.sub(r'\((.+)\)',"\g<1>",dua)
        dua = re.sub(r'-'," ",dua)
        dua = re.sub(r':\('," ",dua)
        dua = re.sub(r':'," ",dua)
        dua = re.sub(r'\('," ",dua)
        dua = re.sub(r'\)'," ",dua)
        dua = re.sub(r"'"," ",dua)
        dua = re.sub(r'"'," ",dua)
        dua = re.sub(r';'," ",dua)
        dua = re.sub(r':v'," ",dua)
        dua = re.sub(r'²'," ",dua)
        dua = re.sub(r':"\)'," ",dua)
        dua = re.sub(r'\[\]'," ",dua)
        dua = re.sub(r'“',"",dua)
        dua = re.sub(r'_'," ",dua)
        dua = re.sub(r'—'," ",dua)
        dua = re.sub(r'…'," ",dua)
        dua = re.sub(r'='," ",dua)
        dua = re.sub(r'\/'," ",dua)
        dua = re.sub(r'\[\w+\]'," ",dua)
        dua = re.sub(r'!'," ",dua)
        dua = re.sub(r"'"," ",dua)
        dua = re.sub(r'\s+'," ",dua)
        dua = re.sub(r'^RT',"",dua) 
        dua = re.sub(r'\s+$',"",dua)   
        dua = re.sub(r'^\s+',"",dua)   
        #### MENGUBAH CASE KATA MENJADI LOWERCASE
        tiga = dua.lower()
        empat = stemmer.stem(tiga)
        #### MENGUBAH KATA KEKINIAN MENJADI SESUAI PUEBI
        payload.append((empat,x[1]))

    cursor = conn.cursor()
    sql = "DELETE FROM processingtext"
    cursor.execute(sql)
    conn.commit()

    sql = "INSERT INTO processingtext (percakapan,kelas) VALUES (%s,%s)"
    cursor.executemany(sql,payload)
    conn.commit()

    return redirect(url_for("processing"))
   
@app.route('/processing')
def processing():
    if 'user_id' not in session:
        return redirect('/')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processingtext")
    myresult = cursor.fetchall()
    cursor.execute("SELECT * FROM dataset")
    myresult2 = cursor.fetchall()

    arr = []
    count=0
    for x in myresult:
        count=count+1
        arr.append({"no":count,"sebelum":myresult2[count-1][0],"percakapan":x[0].split(),"kelas":x[1]})
    
    return render_template("processing.html",data=arr)

@app.route('/prosestextdua')
def prosestextdua():
    if 'user_id' not in session:
        return redirect(url_for("login"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM datasetdua")
    myresult = cursor.fetchall()

    factory = StopWordRemoverFactory()
    stopword = factory.create_stop_word_remover()

    payload = []

    for x in myresult:
        #### MELAKUKAN PROSES STEMMING STOPWORD BAHASA INDONESIA
        satu = stopword.remove(x[0])
        #### MENGHILANGKAN TEXT TIDAK PENTING SEPERTI HASHTAG DAN MENTION
        dua = re.sub(r"@[^\s]+"," ",satu)
        dua = re.sub(r"#[^\s]+"," ",dua)
        dua = re.sub(r"\."," ",dua)
        dua = re.sub(r"http[^\s]+"," ",dua)
        dua = re.sub(r"\?"," ",dua)
        dua = re.sub(r","," ",dua)
        dua = re.sub(r"”"," ",dua)
        dua = re.sub(r"co/[^\s]+"," ",dua)
        dua = re.sub(r":'\)"," ",dua)
        dua = re.sub(r":\)","",dua)
        dua = re.sub(r"&"," ",dua)
        dua = re.sub(r'\"([^\"]+)\"',"\g<1>",dua)
        dua = re.sub(r'\([^\)]+\"',"",dua)
        dua = re.sub(r'\((.+)\)',"\g<1>",dua)
        dua = re.sub(r'-'," ",dua)
        dua = re.sub(r':\('," ",dua)
        dua = re.sub(r':'," ",dua)
        dua = re.sub(r'\('," ",dua)
        dua = re.sub(r'\)'," ",dua)
        dua = re.sub(r"'"," ",dua)
        dua = re.sub(r'"'," ",dua)
        dua = re.sub(r';'," ",dua)
        dua = re.sub(r':v'," ",dua)
        dua = re.sub(r'²'," ",dua)
        dua = re.sub(r':"\)'," ",dua)
        dua = re.sub(r'\[\]'," ",dua)
        dua = re.sub(r'“',"",dua)
        dua = re.sub(r'_'," ",dua)
        dua = re.sub(r'—'," ",dua)
        dua = re.sub(r'…'," ",dua)
        dua = re.sub(r'='," ",dua)
        dua = re.sub(r'\/'," ",dua)
        dua = re.sub(r'\[\w+\]'," ",dua)
        dua = re.sub(r'!'," ",dua)
        dua = re.sub(r"'"," ",dua)
        dua = re.sub(r'\s+'," ",dua)
        dua = re.sub(r'^RT',"",dua) 
        dua = re.sub(r'\s+$',"",dua)   
        dua = re.sub(r'^\s+',"",dua)   
        #### MENGUBAH CASE KATA MENJADI LOWERCASE
        tiga = dua.lower()
        empat = stemmer.stem(tiga)
        #### MENGUBAH KATA KEKINIAN MENJADI SESUAI PUEBI
        payload.append((empat,x[1]))

    cursor = conn.cursor()
    sql = "DELETE FROM processingtextdua"
    cursor.execute(sql)
    conn.commit()

    sql = "INSERT INTO processingtextdua (percakapan,kelas) VALUES (%s,%s)"
    cursor.executemany(sql,payload)
    conn.commit()

    return redirect(url_for("processingdua"))
   
@app.route('/processingdua')
def processingdua():
    if 'user_id' not in session:
        return redirect('/')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processingtextdua")
    myresult = cursor.fetchall()
    cursor.execute("SELECT * FROM datasetdua")
    myresult2 = cursor.fetchall()

    arr = []
    count=0
    for x in myresult:
        count=count+1
        arr.append({"no":count,"sebelum":myresult2[count-1][0],"percakapan":x[0].split(),"kelas":x[1]})
    
    return render_template("processingdua.html",data=arr)

@app.route('/klasifikasi')
def klasifikasi():
    if 'user_id' not in session:
        return redirect('/')
    #konek Database
    cursor = conn.cursor()
    #Mengambil data dari tabel processingtext
    cursor.execute("SELECT * FROM processingtext")
    #Ambil semua data pada tabel
    myresult = cursor.fetchall()

    X = []
    y = []
    # X dijadikan tempat untuk menampung data percakapan
    # Y dijadikan tempat untuk menampung data kelas
    for l in myresult:
        X.append(l[0])
        y.append(l[1])
    # Mengisi data training dan testing (Random 50%)
    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.5, train_size=0.5, random_state=19)
    vectorizerr = TfidfVectorizer(sublinear_tf=True, use_idf=True, lowercase=True, preprocessor=None, tokenizer=None)

    X_train_tf = vectorizerr.fit_transform(X_train)
    X_test_tf = vectorizerr.transform(X_test)
    # Klasifikasi Naive Bayes
    model = MultinomialNB()
    model.fit(X_train_tf, y_train)
    result = model.predict(X_test_tf)

    c=-1
    p = []
    for x in result:
        c=c+1
        p.append({"no":c+1,"percakapan":X_test[c],"kelas":x})
        print(p)
    #print(confusion_matrix(y_test,result,labels=["Positif","Negatif"]))
    return render_template("klasifikasi.html", data=p)

@app.route('/klasifikasidua')
def klasifikasidua():
    if 'user_id' not in session:
        return redirect('/')
    #konek Database
    cursor = conn.cursor()
    #Mengambil data dari tabel processingtext
    cursor.execute("SELECT * FROM processingtextdua")
    #Ambil semua data pada tabel
    myresult = cursor.fetchall()

    X = []
    y = []
    # X dijadikan tempat untuk menampung data percakapan
    # Y dijadikan tempat untuk menampung data kelas
    for l in myresult:
        X.append(l[0])
        y.append(l[1])
    # Mengisi data training dan testing (Random 50%)
    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.5, train_size=0.5, random_state=4)
    vectorizer = TfidfVectorizer(sublinear_tf=False)

    X_train_tf = vectorizer.fit_transform(X_train)
    X_test_tf = vectorizer.transform(X_test)
    # Klasifikasi Naive Bayes
    model = MultinomialNB()
    model.fit(X_train_tf, y_train)
    result = model.predict(X_test_tf)

    c=-1
    p = []
    for x in result:
        c=c+1
        p.append({"no":c+1,"percakapan":X_test[c],"kelas":x})
        print(p)
    #print(confusion_matrix(y_test,result,labels=["Positif","Negatif"]))
    return render_template("klasifikasidua.html", data=p)

@app.route('/pengujian')
def pengujian():
    if 'user_id' not in session:
        return redirect('/')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processingtext")
    myresult = cursor.fetchall()

    X = []
    y = []

    for l in myresult:
        X.append(l[0])
        y.append(l[1])

    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.5, train_size=0.5, random_state=19)
    vectorizerr = TfidfVectorizer(sublinear_tf=True, use_idf=True, lowercase=True, preprocessor=None, tokenizer=None)

    X_train_tf = vectorizerr.fit_transform(X_train)
    X_test_tf = vectorizerr.transform(X_test)

    model = MultinomialNB()
    model.fit(X_train_tf, y_train)
    result = model.predict(X_test_tf)

    c=-1
    p = []
    for x in result:
        c=c+1
        p.append({"no":c+1,"percakapan":X_test[c],"kelas":x})
    
    matrix = confusion_matrix(y_test,result,labels=["Positif","Negatif"])

    cmatrix = [{ "kosong": "Predicted True", "actualtrue": int(matrix[0][0]), "actualfalse": int(matrix[0][1]) },{ "kosong": "Predicted False", "actualtrue": int(matrix[1][0]), "actualfalse": int(matrix[1][1]) }]
    cmatrix_dump = json.dumps(cmatrix)
    return render_template("pengujian.html", cmatrix=cmatrix_dump)

@app.route('/pengujiandua')
def pengujiandua():
    if 'user_id' not in session:
        return redirect('/')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM processingtextdua")
    myresult = cursor.fetchall()

    X = []
    y = []

    for l in myresult:
        X.append(l[0])
        y.append(l[1])

    X_train, X_test, y_train, y_test = train_test_split(X,y, test_size=0.5, train_size=0.5, random_state=4)
    vectorizer = TfidfVectorizer(sublinear_tf=True)

    X_train_tf = vectorizer.fit_transform(X_train)
    X_test_tf = vectorizer.transform(X_test)

    model = MultinomialNB()
    model.fit(X_train_tf, y_train)
    result = model.predict(X_test_tf)

    c=-1
    p = []
    for x in result:
        c=c+1
        p.append({"no":c+1,"percakapan":X_test[c],"kelas":x})
    
    matrix = confusion_matrix(y_test,result,labels=["Positif","Negatif"])

    cmatrix = [{ "kosong": "Actual True", "actualtrue": int(matrix[0][0]), "actualfalse": int(matrix[0][1]) },{ "kosong": "Actual False", "actualtrue": int(matrix[1][0]), "actualfalse": int(matrix[1][1]) }]
    cmatrix_dump = json.dumps(cmatrix)
    return render_template("pengujiandua.html", cmatrix=cmatrix_dump)

if __name__=="__main__":
    app.run(debug=True)