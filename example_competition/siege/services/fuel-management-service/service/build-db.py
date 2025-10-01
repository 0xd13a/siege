#!/usr/bin/python3
# -*- coding: utf8 -*-
#

import sqlite3

DB = "./fms-users.db"

def exec_sql(query, param=[], update=False):
	con = None
	cur = None
	rows = []
	try:
		con = sqlite3.connect(DB)
		cur = con.cursor()
		for row in cur.execute(query, param):
			rows.append(row)
		if update:
			con.commit()
	except Exception as e:
		print(e)
		traceback.print_exc()
	finally:
		if cur != None:
			cur.close()
		if con != None:
			con.close()
	return rows

exec_sql("CREATE TABLE users (user VARCHAR(255), pwd VARCHAR(255), monitor_only INT);", [], True)

with open("fms-users.txt","r") as file:
	for line in file.readlines():
		username, _, hash, monitor_only = line.strip().split(",")
		exec_sql("INSERT INTO users (user, pwd, monitor_only) VALUES(?, ?, ?);", [username, hash, monitor_only], True)
