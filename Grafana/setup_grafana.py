#!/usr/bin/env python
# Based on https://github.com/QualiApps/grafana-docker/blob/master/files/start.py
import requests
import git
import shutil
import json
from os import environ, listdir, path
from time import sleep
from urllib.parse import urlunparse
from subprocess import Popen, PIPE


class Grafana(object):
    env = environ.get
    scheme = "http"
    api_path_datasources = "api/datasources"
    api_path_gnet_inspectit = "api/gnet/dashboards/1691"
    api_path_gnet_jmeter = "api/gnet/dashboards/1152"
    api_path_import = "api/dashboards/import"
    api_path_dashbaord = "/api/dashboards/db"
    dashboards = "dashboards"

    def __init__(self):
        '''
            Init params
        '''
        self.inspectit_params = {
            "name": self.env("DS_NAME", "inspectit-influx"),
            "type": self.env("DS_TYPE", "influxdb"),
            "access": self.env("DS_ACCESS", "direct"),
            "url": self.env("DS_URL", "http://localhost:8086"),
            "password": self.env("DS_PASS", "root"),
            "user": self.env("DS_USER", "root"),
            "database": self.env("DS_DB", "inspectit"),
            "basicAuth": self.env("DS_AUTH", 'false'),
            "basicAuthUser": self.env("DS_AUTH_USER", ""),
            "basicAuthPassword": self.env("AUTH_PASS", ""),
            "isDefault": self.env("DS_IS_DEFAULT", 'false'),
            "jsonData": self.env("DS_JSON_DATA", 'null')
        }

        self.jmeter_params = {
            "name": self.env("DS_NAME", "jmeter-influx"),
            "type": self.env("DS_TYPE", "influxdb"),
            "access": self.env("DS_ACCESS", "direct"),
            "url": self.env("DS_URL", "http://localhost:8086"),
            "password": self.env("DS_PASS", "root"),
            "user": self.env("DS_USER", "root"),
            "database": self.env("DS_DB", "jmeter"),
            "basicAuth": self.env("DS_AUTH", 'false'),
            "basicAuthUser": self.env("DS_AUTH_USER", ""),
            "basicAuthPassword": self.env("AUTH_PASS", ""),
            "isDefault": self.env("DS_IS_DEFAULT", 'false'),
            "jsonData": self.env("DS_JSON_DATA", 'null')
        }

        # clone inspectit dashboard repo
        git.Git().clone("https://github.com/inspectit-labs/dashboards")

        # Create grafana api paths
        self.gf_url_datasources = urlunparse(
            (
                self.scheme,
                ":".join((self.env("GF_HOST", "localhost"), self.env("GF_PORT", "3000"))),
                self.api_path_datasources, "", "", ""
            )
        )
        self.gf_url_gnet_inspectit = urlunparse(
            (
                self.scheme,
                ":".join((self.env("GF_HOST", "localhost"), self.env("GF_PORT", "3000"))),
                self.api_path_gnet_inspectit, "", "", ""
            )
        )
        self.gf_url_gnet_jmeter = urlunparse(
            (
                self.scheme,
                ":".join((self.env("GF_HOST", "localhost"), self.env("GF_PORT", "3000"))),
                self.api_path_gnet_jmeter, "", "", ""
            )
        )
        self.gf_url_import = urlunparse(
            (
                self.scheme,
                ":".join((self.env("GF_HOST", "localhost"), self.env("GF_PORT", "3000"))),
                self.api_path_import, "", "", ""
            )
        )
        self.gf_url_dashboard = urlunparse(
            (
                self.scheme,
                ":".join((self.env("GF_HOST", "localhost"), self.env("GF_PORT", "3000"))),
                self.api_path_dashbaord, "", "", ""
            )
        )
        # Init requests session
        self.auth = self.env("GF_USER", "admin"), self.env("GF_PASS", "admin")
        self.sess = requests.Session()

    def init_datasources(self):
        '''
            Initializes all datasources.
            :return: bool
        '''
        res = self.sess.get(self.gf_url_datasources, auth=self.auth)
        if res.ok:
            inspectit = True
            jmeter = True
            for ds in res.json():
                if ds["name"] == self.inspectit_params["name"]:
                    print("*------------WARNING: Datasource with name " + self.inspectit_params["name"] + " already exists!------------*")
                    inspectit = False
                if ds["name"] == self.jmeter_params["name"]:
                    print("*------------WARNING: Datasource with name " + self.jmeter_params["name"] + " already exists!------------*")
                    jmeter = False

            exit_code = True

            if inspectit:
                exit_code = exit_code and self.init_inspectit_datasource()

            if jmeter:
                exit_code = exit_code and self.init_jmeter_datasource()

            return exit_code

        return False

    def init_inspectit_datasource(self):
        '''
            Upload a datasource
            :return bool
        '''
        response = False
        res = self.sess.post(self.gf_url_datasources, data=self.inspectit_params, auth=self.auth)
        if res.ok:
            response = True

        print(res)

        return response

    def init_jmeter_datasource(self):
        '''
            Upload a datasource
            :return bool
        '''
        response = False
        res = self.sess.post(self.gf_url_datasources, data=self.jmeter_params, auth=self.auth)
        if res.ok:
            response = True

        return response

    def import_dashboards(self):
        '''
            Imports all neccessary dashboards.
            :return: void
        '''
        response = self.import_inspectit_dashboard() and self.import_jmeter_dashboard()

        for filename in listdir(self.dashboards):
            if filename.endswith(".json"):
                print("Importing dashboard: " + filename)
                with open(path.join(self.dashboards, filename), 'r') as f:
                    dashboard = json.load(f)
                    response = response and self.import_dashboard(dashboard, "DS_INSPECTIT", self.inspectit_params["type"], self.inspectit_params["name"])

        return response

    def import_inspectit_dashboard(self):
        '''
            Import the official inspectIT dashboard
            :return: bool
        '''
        response = False
        res = self.sess.get(self.gf_url_gnet_inspectit, auth=self.auth)

        if not res.ok:
            print(res.text)
            return response

        dashboard = res.json()

        return self.import_dashboard(dashboard.pop("json"), "DS_INFLUXDB", self.inspectit_params["type"], self.inspectit_params["name"])

    def import_jmeter_dashboard(self):
        '''
            Import the official JMeter dashboard
            :return: bool
        '''
        response = False
        res = self.sess.get(self.gf_url_gnet_jmeter, auth=self.auth)

        if not res.ok:
            print(res.text)
            return response

        dashboard = res.json()

        return self.import_dashboard(dashboard.pop("json"), "DS_JMETER", self.jmeter_params["type"], self.jmeter_params["name"])

    def import_dashboard(self, db, ds_name, ds_plugin_id, ds_value):
        '''
            Import the given dashboard
            :dashboard: json
            :return: bool
        '''
        dashboard = {}
        dashboard["dashboard"] = db
        dashboard["overwrite"] = True

        dashboard_datasource = {
            "name": ds_name,
            "type": "datasource",
            "pluginId": ds_plugin_id,
            "value": ds_value
        }
        dashboard["inputs"] = [dashboard_datasource]
        dashboard["dashboard"]["inputs"] = [dashboard_datasource]
        dashboard["dashboard"]["__inputs"] = [dashboard_datasource]

        res = self.sess.post(self.gf_url_import, json=dashboard, auth=self.auth)
        if res.ok:
            response = True
        else:
            print(res.text)

        return response

    def create_influx_database(self):
        '''
            Workaround for INSPECTIT-2493
            :return: bool
        '''
        response = False
        res = requests.post("http://localhost:8086/query", data={'q': 'CREATE DATABASE "inspectit"'})
        if res.ok:
            response = True

        return response

    def create_jmeter_database(self):
        '''
           Create JMeter database.
        '''
        response = False
        res = requests.post("http://localhost:8086/query", data={'q': 'CREATE DATABASE "jmeter"'})
        if res.ok:
            response = True

        return response

    def start(self):
        '''
            Check api
            :return tuple - status
        '''
        status = False
        # wait, until gf api will be available
        # trying 5 times
        retry = 0
        while retry <= 5:
            if self._check_gf():
                status = True
                break
            retry += 1
            sleep(3)

        return status

    def _check_gf(self):
        '''
            Check gf api
            :return bool
        '''
        resp = False
        try:
            res = self.sess.get(self.gf_url_datasources, auth=self.auth)
            resp = True if res and res.ok else False
        except Exception as message:
            print("CONNECTION! %s" % message)

        return resp

if __name__ == "__main__":
    gf = Grafana()
    try:
        exit_code = 0
        status = gf.start()
        print("Grafana API is running: " + str(status))
        if status:
            if gf.init_datasources():
                print("*------------SUCCESS! Your datasource was added!------------*")
            else:
                print("*------------ERROR! Your datasource was not added!------------*")
                exit(1)
            if gf.create_influx_database():
                print("*------------SUCCESS! Influx database created!--------------*")
            else:
                print("*------------ERROR! Influx database not created!--------------*")
                exit(1)
            if gf.create_jmeter_database():
                print("*------------SUCCESS! JMeter database created!--------------*")
            else:
                print("*------------ERROR! JMeter database not created!--------------*")
                exit(1)
            if gf.import_dashboards():
                print("*------------SUCCESS! Dashboard was added!------------------*")
            else:
                print("*------------ERROR! Dashboard was not added!------------------*")
                exit(1)
    except Exception as error:
        print("*------------ERROR! %s------------*" % error)
        exit_code = 1
    finally:
        shutil.rmtree(gf.dashboards)
        exit(exit_code)

