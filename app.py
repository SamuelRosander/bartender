from flask import Flask, render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
import json
import time
import os
import RPi.GPIO as GPIO

pump_speed = 7   # time in seconds it takes to pour 1 cl
app = Flask(__name__)
app.config["SECRET_KEY"] = "2a3124439cb4e6341320acfb294279a6"

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
conf_file = os.path.join(SITE_ROOT, 'config.json')

with open(conf_file) as f_global:
    conf_global = json.load(f_global)

GPIO.setmode(GPIO.BCM)
for i in range(1, 7):
    GPIO.setup(conf_global["pumps"][str(i)]["bcm"], GPIO.OUT, initial=1)


@app.route("/", methods=["POST", "GET"])
def index():
    with open(conf_file) as f:
        conf = json.load(f)

    form = ConfigForm()

    # if form has been sent (user is coming from config.html), update config values
    if form.validate_on_submit():
        conf["pumps"]["1"]["ingredient"] = form.pump1.data
        conf["pumps"]["2"]["ingredient"] = form.pump2.data
        conf["pumps"]["3"]["ingredient"] = form.pump3.data
        conf["pumps"]["4"]["ingredient"] = form.pump4.data
        conf["pumps"]["5"]["ingredient"] = form.pump5.data
        conf["pumps"]["6"]["ingredient"] = form.pump6.data

        conf["drink_size"] = form.drink_size.data

        with open(conf_file, 'w') as fw:
            json.dump(conf, fw, indent=2)

    available_ingredients = []
    for pump, pump_data in conf["pumps"].items():
        available_ingredients.append(pump_data["ingredient"])

    available_drinks = {}
    for drink, drink_data in conf["drinks"].items():
        if has_ingredients(drink_data, available_ingredients):
            available_drinks[drink] = drink_data

    return render_template("index.html", drinks=available_drinks, drink_size=conf["drink_size"])


@app.route("/make_drink/<drink>/<int:drink_size>")
def make_drink(drink, drink_size):
    with open(conf_file) as f:
        conf = json.load(f)

    pour_drink(conf["drinks"][drink]["ingredients"], drink_size, conf)

    return redirect(url_for("index"))


@app.route("/config")
def config():
    with open(conf_file) as f:
        conf = json.load(f)

    form = ConfigForm()

    # set the default values of the drop down menus
    form.pump1.default = conf["pumps"]["1"]["ingredient"]
    form.pump2.default = conf["pumps"]["2"]["ingredient"]
    form.pump3.default = conf["pumps"]["3"]["ingredient"]
    form.pump4.default = conf["pumps"]["4"]["ingredient"]
    form.pump5.default = conf["pumps"]["5"]["ingredient"]
    form.pump6.default = conf["pumps"]["6"]["ingredient"]
    form.process()

    return render_template("config.html", conf=conf, form=form)


@app.route("/clean")
def clean():
    return render_template("clean.html")


@app.route("/clean/<int:pump>")
def clean_pump(pump):
    GPIO.output(conf_global["pumps"][str(pump)]["bcm"], GPIO.LOW)   # turn on the correct pump, LOW = relay ON
    print("Pump", pump, "on")
    time.sleep(10)
    GPIO.output(conf_global["pumps"][str(pump)]["bcm"], GPIO.HIGH)   # turn on the correct pump, HIGH = relay OFF
    print("Pump", pump, "off")

    return render_template("clean.html")


@app.route("/clean_all")
def clean_all():
    for pump in range(1, 4):
        GPIO.output(conf_global["pumps"][str(pump)]["bcm"], GPIO.LOW)
        print("Pump", pump, "on")
    time.sleep(10)
    for pump in range(1, 4):
        GPIO.output(conf_global["pumps"][str(pump)]["bcm"], GPIO.HIGH)
        print("Pump", pump, "off")
    for pump in range(4, 7):
        GPIO.output(conf_global["pumps"][str(pump)]["bcm"], GPIO.LOW)
        print("Pump", pump, "on")
    time.sleep(10)
    for pump in range(4, 7):
        GPIO.output(conf_global["pumps"][str(pump)]["bcm"], GPIO.HIGH)
        print("Pump", pump, "off")

    return render_template("clean.html")


@app.errorhandler(403)
def error_403(error):
    return render_template("error.html")


@app.errorhandler(404)
def error_404(error):
    return render_template("error.html")


@app.errorhandler(500)
def error_500(error):
    return render_template("error.html")


def has_ingredients(drink_data, available_ingredients):
    """ Returns True if the drink is makeable with all available ingredients """
    for ingredient in drink_data["ingredients"]:
        if ingredient["name"] not in available_ingredients:
            return False
    return True


def pour_drink(ingredients, drink_size, conf):
    """ Pump control for pouring a drink """

    pouring_ingredients = []
    for ing in ingredients:
        if ing["amount"] == -1:  # amount = -1 if it's a filler
            pouring_ingredients.append({"name": ing["name"], "amount": 30-drink_size})
        else:   # otherwise amount is percent of drink size of 100 (i.e. 33 for 1/3)
            pouring_ingredients.append({"name": ing["name"], "amount": ing["amount"] * drink_size / 100})

    for ing in pouring_ingredients:
        print("Pouring", ing["name"], ing["amount"])
        for i, pump in conf["pumps"].items():
            if pump["ingredient"] == ing["name"]:
                GPIO.output(pump["bcm"], GPIO.LOW)
                print(pump["bcm"], "on")

    start_time = time.time()

    while True:
        for ing in pouring_ingredients:
            if time.time() > start_time + ing["amount"] * pump_speed:
                print("Stop", ing["name"])
                for i, pump in conf["pumps"].items():
                    if pump["ingredient"] == ing["name"]:
                        GPIO.output(pump["bcm"], GPIO.HIGH)
                        print(pump["bcm"], "off")
                pouring_ingredients.remove(ing)

        if len(pouring_ingredients) == 0:
            break


class ConfigForm(FlaskForm):
    drink_size = StringField("drink_size")
    choices = [(ing, ing) for ing in conf_global["ingredients"]]
    pump1 = SelectField("Pump 1", choices=choices)
    pump2 = SelectField("Pump 2", choices=choices)
    pump3 = SelectField("Pump 3", choices=choices)
    pump4 = SelectField("Pump 4", choices=choices)
    pump5 = SelectField("Pump 5", choices=choices)
    pump6 = SelectField("Pump 6", choices=choices)
    submit = SubmitField("<")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
