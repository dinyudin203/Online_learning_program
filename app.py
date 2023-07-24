import psycopg2
from flask import Flask, render_template, request

app = Flask(__name__)
connect = psycopg2.connect("dbname=practice3 user=postgres password=****")
cur = connect.cursor()  # create cursor

@app.route('/')
def main():
    return render_template("main.html")

@app.route('/return', methods=['post'])
def re_turn():
    return render_template("main.html")


@app.route('/adjust', methods=['post'])
def adjust(): #subject list 확인
    cur.execute("SELECT * from subject;")
    result = cur.fetchall()
    return render_template("adjust.html", subjects=result)

@app.route('/adjust_confirm', methods=['post'])
def adjust_confirm(): #subject 추가 확인
    code = request.form["code"]
    name = request.form["name"]
    send = request.form["submit"]

    if send == 'add':
        cur.execute("SELECT code FROM subject WHERE code = %s;", (code,))
        exist1=cur.fetchall()
        cur.execute("SELECT subject_name FROM subject WHERE subject_name= %s;", (name,))
        exist2=cur.fetchall()
        if exist1:
            return render_template("error.html")
        elif exist2:
            return render_template("error.html")
        else:
            cur.execute("INSERT INTO subject VAlUES(%s, %s);", (code, name))
            connect.commit()
            return render_template("adjust_confirm.html")

@app.route('/delete_confirm', methods=['post'])
def delete_confirm():
    send = request.form["send"]

    if send == 'delete':
        code = request.form["code"]
        cur.execute("DELETE FROM enrollment WHERE code = %s;", (code,))
        cur.execute("DELETE FROM lecture WHERE code = %s;", (code,))
        cur.execute("DELETE FROM subject WHERE code = %s;", (code,))
        connect.commit()
        return render_template("delete_confirm.html")



@app.route('/admin', methods=['post'])
def admin():
    cur.execute("SELECT l.tutor, s.subject_name, l.name AS lecture_name FROM lecture l JOIN enrollment e ON l.code = e.code AND l.name = e.lecture_name JOIN subject s ON l.code = s.code GROUP BY l.tutor, s.subject_name, l.name HAVING COUNT(*) = ( SELECT MAX(enrollment_count) FROM (SELECT COUNT(*) AS enrollment_count FROM enrollment GROUP BY code, lecture_name) AS subquery);")
    result2 = cur.fetchall()
    cur.execute("SELECT id, credit, rating FROM account WHERE id = 'admin';")
    account = cur.fetchall()
    cur.execute("SELECT code, name, price, tutor FROM lecture;")
    subjects = cur.fetchall()
    return render_template("admin.html", result=result2, account = account, subjects = subjects)


@app.route('/register', methods=['post'])
def register():
    id = request.form["id"]
    password = request.form["password"]
    send = request.form["send"]

    cur.execute("SELECT * FROM users;")
    result1 = cur.fetchall()
    cur.execute("SELECT role FROM account WHERE id = %s;", (id,))
    role = cur.fetchall()
    cur.execute("SELECT id, credit, rating FROM account WHERE id = %s;", (id,))
    account = cur.fetchall()
    cur.execute("SELECT code, name, price, tutor FROM lecture;")
    subjects = cur.fetchall()
    cur.execute("SELECT l.tutor, s.subject_name, l.name AS lecture_name FROM lecture l JOIN enrollment e ON l.code = e.code AND l.name = e.lecture_name JOIN subject s ON l.code = s.code GROUP BY l.tutor, s.subject_name, l.name HAVING COUNT(*) = ( SELECT MAX(enrollment_count) FROM (SELECT COUNT(*) AS enrollment_count FROM enrollment GROUP BY code, lecture_name) AS subquery);")
    result2 = cur.fetchall()
    flag1 = 0
    if send == "login":
        if id == 'admin' and password == '0000':
            cur.execute("SELECT id, credit, rating FROM account WHERE id = %s;", (id,))
            account = cur.fetchall()
            cur.execute("SELECT code, name, price, tutor FROM lecture;")
            subjects = cur.fetchall()
            return render_template("admin.html", result=result2, account = account, subjects = subjects)
        for i in range(len(result1)):
            if id == result1[i][0]:
                if password == result1[i][1]:
                    flag1 += 1
                    if role[0][0] == 'tutee':
                        return render_template("tutee.html", result=result2, account=account, subjects=subjects)
                    if role[0][0] == 'tutor':
                        return render_template("tutor.html", result=result2, account=account, subjects=subjects)
        if flag1 == 0:
            return render_template("login_fail.html")

    elif send == "sign up":
        return render_template("sign_up.html")
    connect.commit()



@app.route('/sign_up', methods=['post'])
def signup():
    id = request.form["id"]
    password = request.form["password"]
    role = request.form["roles"]

    cur.execute("SELECT * FROM users;")
    result = cur.fetchall()

    flag = 0

    for i in range(len(result)):
        if id == result[i][0]:
            flag += 1
            return render_template("ID_collision.html")
    if flag == 0:
        cur.execute("INSERT INTO users VALUES('{}', '{}');".format(id, password))
        cur.execute("INSERT INTO account VALUES('{}', '10000', 'welcome', '{}');".format(id, role))
        cur.execute("SELECT id, credit, rating FROM account WHERE id = %s;", (id,))
        account = cur.fetchall()
        cur.execute("SELECT code, name, price, tutor FROM lecture;")
        subjects = cur.fetchall()
        cur.execute("SELECT l.tutor, s.subject_name, l.name AS lecture_name FROM lecture l JOIN enrollment e ON l.code = e.code AND l.name = e.lecture_name JOIN subject s ON l.code = s.code GROUP BY l.tutor, s.subject_name, l.name HAVING COUNT(*) = ( SELECT MAX(enrollment_count) FROM (SELECT COUNT(*) AS enrollment_count FROM enrollment GROUP BY code, lecture_name) AS subquery);")
        result = cur.fetchall()
        connect.commit()
        if role == 'tutee':
            return render_template("tutee.html", result=result, account = account, subjects = subjects)
        if role == 'tutor':
            return render_template("tutor.html", result=result, account = account, subjects = subjects )

@app.route('/buy', methods=['post'])
def buy(): #tutee의 역할로_입장
    code = request.form["code"]
    name = request.form["name"]
    price = request.form["price"]
    te_id = request.form["te_id"]
    tr_id = request.form["tr_id"]

    cur.execute("SELECT tutor, code, lecture_name, lecture_price FROM enrollment WHERE tutee = %s;", (te_id,))
    exist = cur.fetchall()
    flag = 0
    price = int(price)
    for word in exist:
        if word == (tr_id, code, name, price):
            flag = 1
    if flag == 1:
        return render_template("error.html")
    if flag == 0:
        if tr_id != te_id:
            cur.execute("SELECT credit, rating FROM account NATURAL JOIN rating_info WHERE id = %s;", (te_id,))
            result = cur.fetchall()
            price = float(price)
            origin = [int(price)]
            cur.execute("SELECT credit FROM account WHERE id = %s;", (te_id,))
            result1 = cur.fetchall()
            result2 = int(result1[0][0])
            cur.execute("SELECT discount FROM account NATURAL JOIN rating_info WHERE id = %s", (te_id,))
            discount = cur.fetchall()
            discount2 = float(discount[0][0])
            origin += [int(price * discount2)]  # Discounted price
            origin += [int(price - origin[1])]  # Final discounted price
            if origin[2] > result2:
                return render_template("error.html")
            else:
                return render_template("buy.html", code=code, name=name, price=price, tr_id=tr_id, result=result, origin=origin, te_id=te_id)

        else:
            return render_template("error.html")
    else:
        return render_template("error.html")

@app.route('/user_info', methods=['post'])
def user_info():
    cur.execute("SELECT * FROM users NATURAL JOIN account;")
    users=cur.fetchall()
    return render_template("user_info.html", users=users)

@app.route('/trades_info', methods=['post'])
def trades_info():
    cur.execute("SELECT * FROM enrollment;")
    subjects=cur.fetchall()
    return render_template("trades_info.html", subjects=subjects)

@app.route('/error', methods=['post'])
def error():
    return render_template("error.html")

@app.route('/my_info', methods=['post'])
def my_info():
    te_id = request.form["te_id"]
    cur.execute("SELECT subject_name, lecture_name, tutee, lecture_price FROM subject NATURAL JOIN enrollment WHERE tutee = %s;",(te_id,))
    result = cur.fetchall()
    return render_template("my_lecture.html", subjects=result)

@app.route('/tutor_info', methods=['post'])
def tutor_info():
    te_id = request.form["id"]
    tr_id = request.form["id"]
    cur.execute("SELECT subject_name, lecture_name, tutor, lecture_price FROM subject NATURAL JOIN enrollment WHERE tutee = %s;",(te_id,))
    result1 = cur.fetchall()
    cur.execute("SELECT subject_name, name, tutee, price FROM (subject NATURAL JOIN lecture) natural left outer join enrollment WHERE tutor = %s;", (tr_id,))
    result2 = cur.fetchall()
    return render_template("tutor_info.html", subjects1=result1, subjects2=result2)

@app.route('/confirm', methods=['post'])
def confirm():
    code = request.form["code"]
    name = request.form["name"]
    te_id = request.form["te_id"]
    tr_id = request.form["tr_id"]
    price = request.form["rprice"]
    discount = request.form["discount"]

    cur.execute("SELECT tutor, code, lecture_name, lecture_price FROM enrollment WHERE tutee = %s;", (te_id,))
    exist = cur.fetchall()
    flag = 0
    price = int(price)
    for word in exist:
        if word == (tr_id, code, name, price):
            flag = 1
    if flag == 1:
        return render_template("error.html")

    cur.execute("UPDATE account SET credit = credit - %s WHERE id = %s;", (discount, te_id))
    cur.execute("UPDATE account SET credit = credit + %s WHERE id = %s;", (price, tr_id))

    cur.execute("SELECT credit FROM account WHERE id = %s;", (te_id,))
    state1 = cur.fetchall()

    cur.execute("SELECT credit FROM account WHERE id = %s;", (tr_id,))
    state2 = cur.fetchall()

    cur.execute("INSERT into enrollment VALUES(%s, %s, %s, %s, %s);", (te_id, tr_id, code, name, price))
    connect.commit()


    rating1 = state1[0][0]

    if state1[0][0] < 50000:
        rating2 = 'welcome'
    elif state1[0][0] < 1000000:
        rating2 = 'bronze'
    elif state1[0][0] < 5000000:
        rating2 = 'silver'
    else:
        rating2 = 'gold'


    cur.execute("SELECT tutor, tutee, subject_name, lecture_name, lecture_price FROM enrollment NATURAL JOIN subject WHERE tutee = %s;", (te_id,))
    subject = cur.fetchall()
    if rating1 != rating2:
        cur.execute("UPDATE account SET rating = %s WHERE id = %s;", (rating2, te_id))
        connect.commit()

    rating3 = state2[0][0]

    if state2[0][0] < 50000:
        rating4 = 'welcome'
    elif state2[0][0] < 1000000:
        rating4 = 'bronze'
    elif state2[0][0] < 5000000:
        rating4 = 'silver'
    else:
        rating4 = 'gold'

    if rating3 != rating4:
        cur.execute("UPDATE account SET rating = %s WHERE id = %s;", (rating4, tr_id))
        connect.commit()

    return render_template("confirm.html", subjects=subject)

@app.route('/add', methods=['post'])
def add(): #tutor add하러 입장
    tr_id=request.form["tr_id"]
    cur.execute("SELECT * from subject;")
    result=cur.fetchall()
    return render_template("add.html", subjects=result, tr_id=tr_id)

@app.route('/add_confirm', methods=['post'])
def add_confirm():
    code = request.form["code"]
    lecture_name = request.form["name"]
    lecture_price = request.form["price"]
    tr_id = request.form["tr_id"]
    send = request.form["submit"]


    cur.execute("SELECT tutor FROM lecture WHERE code = %s AND tutor = %s AND name = %s;",(code, tr_id, lecture_name))
    exist2 = cur.fetchall()
    if send == 'add':
        if exist2:
            return render_template("error.html")
        else:
            cur.execute("INSERT into lecture VALUES(%s, %s, %s, %s);", (code, lecture_name, lecture_price, tr_id))
            connect.commit()
            return render_template("add_confirm.html")





add.debug = True

if __name__ == '__main__':
    app.run()
