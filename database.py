import mysql.connector as con

database = con.connect(host="172.20.10.3",
                    user="volta",
                    passwd="PEAadmin1oo%",
                    database="stevedb"
                    )


cursor = database.cursor()
queryCommand = "SELECT * FROM transaction WHERE transaction_pk = {}".format(28)
cursor.execute(queryCommand)
results=cursor.fetchall()


for x in results:
    print(x)

