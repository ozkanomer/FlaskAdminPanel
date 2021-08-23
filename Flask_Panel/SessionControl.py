from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from functools import wraps

# Session Control
def Login_Required(f):
    @wraps(f)
    def SessionControl(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görebilmek için, lütfen giriş yapınız!", "danger")
            return redirect(url_for("PanelLogin"))
    return SessionControl
