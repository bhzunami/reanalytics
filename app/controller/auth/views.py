#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from ...models import User
from .forms import LoginForm


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    If the user credentials are valid the user will be
    logged in.
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            current_user.set_lastlogin()
            flash('You have successfully logged in {}'.format(user.name), 'success')
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password', 'danger')

    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    """
    Logout user
    """
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.index'))
