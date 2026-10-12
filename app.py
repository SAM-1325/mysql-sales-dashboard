
import os
import pymysql
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_connection():
    return pymysql.connect(
        host=os.environ["MYSQL_HOST"],
        port=int(os.environ["MYSQL_PORT"]),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
        ssl={"ssl": {}},
        connect_timeout=15
    )

@app.route("/")
def home():
    return jsonify({"message": "Sales Dashboard API is running"})

@app.route("/api/sales")
def sales():
    try:
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*),
                           SUM(quantity),
                           SUM(returned_quantity),
                           SUM(unit_price * (quantity - returned_quantity))
                    FROM sales
                """)
                summary = cursor.fetchone()

                cursor.execute("""
                    SELECT DATE_FORMAT(sale_date, '%%Y-%%m-%%d'),
                           SUM(unit_price * (quantity - returned_quantity))
                    FROM sales
                    GROUP BY sale_date
                    ORDER BY sale_date
                """)
                daily = cursor.fetchall()

                cursor.execute("""
                    SELECT product_name,
                           SUM(unit_price * (quantity - returned_quantity))
                    FROM sales
                    GROUP BY product_name
                    ORDER BY 2 DESC
                """)
                products = cursor.fetchall()

                cursor.execute("""
                    SELECT category,
                           SUM(unit_price * (quantity - returned_quantity))
                    FROM sales
                    GROUP BY category
                    ORDER BY 2 DESC
                """)
                categories = cursor.fetchall()

            return jsonify({
                "summary": {
                    "records": int(summary[0]),
                    "quantity": int(summary[1] or 0),
                    "returns": int(summary[2] or 0),
                    "netRevenue": float(summary[3] or 0)
                },
                "daily": [
                    {"name": str(x[0]), "value": float(x[1])}
                    for x in daily
                ],
                "products": [
                    {"name": str(x[0]), "value": float(x[1])}
                    for x in products
                ],
                "categories": [
                    {"name": str(x[0]), "value": float(x[1])}
                    for x in categories
                ]
            })
        finally:
            conn.close()

    except Exception:
        app.logger.exception("Database query failed")
        return jsonify({"error": "Database temporarily unavailable"}), 503
