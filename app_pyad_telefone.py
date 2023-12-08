from flask import Flask, request, jsonify
import pythoncom
from pyad import adquery
from pyad import aduser

app = Flask(__name__)

def initialize_com():
    try:
        pythoncom.CoInitialize()
    except Exception as e:
        print(f"Erro ao chamar CoInitialize: {str(e)}")

def uninitialize_com():
    try:
        pythoncom.CoUninitialize()
    except Exception as e:
        print(f"Erro ao chamar CoUninitialize: {str(e)}")

def user_exists(username):
    try:
        q = adquery.ADQuery()
        cn = None

        # Consulta para buscar o SamAccountName especificado
        q.execute_query(
            attributes=["SamAccountName", "distinguishedname"],
            where_clause="SamAccountName = '{}'".format(username),
        )

        x = bool(q.get_results())
        if str(x) == "True":
            for row in q.get_results():
                cn = str(row["distinguishedname"]).split(",")[0].replace("CN=", "")
                print(cn)
            # User exists, return True
            return cn
        else:
            # User does not exist, return False
            return None
    except Exception as e:
        return e

def get_user_phone_number(cn):
    try:
        # Fetch the user's phone number from Active Directory (you need to adjust this based on your AD schema)
        user = aduser.ADUser.from_cn(f"{cn}")
        phone_number = user.get_attribute('telephoneNumber')
        return phone_number
    except Exception as e:
        return None


@app.route("/reset_password", methods=["POST"])
def reset_password():
    try:
        initialize_com()
        data = request.get_json()

        # Verify if the 'username', 'new_password', and 'phone_number' fields are present in the JSON
        if "username" not in data or "new_password" not in data or "phone_number" not in data:
            return jsonify({"error": "Missing username, new_password, or phone_number field."}), 400

        username = data["username"]
        new_password = data["new_password"]
        provided_phone_number = data["phone_number"]

        # Check if the user exists in Active Directory
        cn = user_exists(username)

        if cn is None:
            return jsonify({"error": "User does not exist in Active Directory."}), 404

        try:
            # Find the user in AD
            
            user = aduser.ADUser.from_cn(f"{cn}")
            print(user)

            # Reset the password
            user.set_password(new_password)

            # Retrieve the user's phone number from AD
            ad_phone_number = get_user_phone_number(cn)[0]
            print(ad_phone_number)

            if ad_phone_number == provided_phone_number:
                return jsonify({"message": new_password}), 200
            else:
                return jsonify({"error": "Phone number validation failed."}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        uninitialize_com()  # Call CoUninitialize when done



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
