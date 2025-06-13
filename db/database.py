def polacz(host, login, haslo, db):
    db = mysql.connector.connect(
            host=host,
            user=login,
            password=haslo,
            database=db
        )
cursor = db.cursor()