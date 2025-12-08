
# Inventory System (Flask + MySQL)

A fully functional **Role-Based Inventory Management System** developed in **Python (Flask)** with **MySQL** integration.
This project is deployed online using **Render (Web App Hosting)** and **Railway (MySQL Database Hosting)**.

Developed as a final requirement for **Advanced Database System**.

---

## 🔧 Features

### 👤 **User Roles**

* **Admin**

  * Add, edit, delete, and view products
  * Manage users
  * Full access to dashboard
* **Standard User**

  * View-only access to products

---

### 📦 **Inventory Management**

* Create new product entries
* Read/view product list
* Update product details
* Delete product records
* Responsive UI using Bootstrap

---

### 🔐 **Security**

* Secure password hashing (bcrypt + PBKDF2 compatible)
* Role-based access control
* Audit logging (tracks user actions)
* Session-based authentication

---

## 🌐 Online Hosting

### **Backend / Web App**

Hosted on: **Render.com**

* Auto-deployed from GitHub
* Uses Render’s environment variables for database connection
* Runs Flask app with dynamic PORT from Render

### **Database**

Hosted on: **Railway.app**

* MySQL database instance
* External proxy host + port used by Flask app
* Secure credentials stored in Render Environment Variables

---

## 🗂️ Project Structure

```
inventory_system/
│── app.py
│── db.py
│── security.py
│── requirements.txt
│── README.md
│
├── templates/
│   ├── login.html
│   ├── dashboard.html
│   ├── products_list.html
│   ├── product_form.html
│   ├── user_form.html
│
└── static/
    ├── css/
    ├── js/
    └── assets/
```

---

## ⚙️ Local Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/your-username/msit_inventory_system.git
cd msit_inventory_system
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS / Linux
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Create `.env` (Local DB or Railway DB)

```
DB_HOST=your-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=railway
```

### 5️⃣ Run Application

```bash
python app.py
```

Open in browser:

```
http://127.0.0.1:10000
```

---

## 👨‍💻 Developer

**Patrick Jason L. Torres**
*MSIT Student / Developer*
Creator and maintainer of this project.

---

## 📄 Notes

* This system is intended for academic and development use.
* Uses secure password hashing and role-based access control.
* Flask runs in development mode locally; Render handles production hosting.

