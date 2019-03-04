import mechanize
from bs4 import BeautifulSoup
import cookielib
import requests
import urllib2
import time
import json
from  datetime import datetime 
import mysql.connector as con

class OcppServer:

    def __init__(self):
        self.name = 'ocppservice'
        self.username = 'admin'
        self.password = '1234'
        self.csrf = None
        self.response = None
        self.endpoint = 'http://192.168.1.127:9090/steve/manager'
        self.signin = '/signin'
        self.home = '/home'
        self.signout = '/signout'
        self.remotestart ='/operations/v1.6/RemoteStartTransaction'
        self.remotestop = '/operations/v1.6/RemoteStopTransaction'
        self.txinfo = '/transactions/details/' # with transactionID
        self.br = None
        self.txid = None
        self.energy = None
        self.duration = None
        self.start_tx = None
        self.stop_tx = None

    def login(self):
    
        URL = str(self.endpoint+self.signin)
        cookie = cookielib.CookieJar()
        br = mechanize.Browser()
        br.set_cookiejar(cookie)
        br.open(URL)
        br.select_form(nr=0)
        br.form['username'] = self.username
        br.form['password'] = self.password
        br.submit()
        # print br.response().read()
        return br

    def logout(self, br ,cookie):
        print('logout server session')
        # br.open(self.endpoint+self.signout)
        res = requests.get(
            url = self.endpoint+self.signout ,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": "JSESSIONID={}".format(cookie),
                "Authorization": "Basic YWRtaW46MTIzNA==",
            },
            data = {},
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=res.status_code))

        if res.status_code == 200:
            return True
        else:
            return False

    def remote_start(self):
        csrf = None
        br = self.login()
        br.open(self.endpoint+self.remotestart)
        for form in br.forms():
            csrf = form.get_value(nr=4)
        # print("CSRF : {}".format(csrf))
        # # print("Start Create Ocpp Tag")
        serverip = self.endpoint.split(':')[1].replace('//','')
        cookie= br.cookiejar._cookies[serverip]['/steve']['JSESSIONID'].value
        
        try :
            if csrf is not None:
                status = self.handle_startTrx(csrf, cookie)
                if status :
                    res = self.logout(br ,cookie)
                    if res:
                        print("Logout Transaction Success")
                    else:
                        print("Logout Fail")
                

        except Exception as Err:
            print(Err)
    
    def handle_startTrx(self, csrf, cookie):
        print("Send Request for Start Transaction")
        response = requests.post(
            url = self.endpoint+self.remotestart,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": "JSESSIONID={}".format(cookie),
                "Authorization": "Basic YWRtaW46MTIzNA==",
            },
            data={
                "chargePointSelectList": "JSON;CP1001;-",
                "connectorId": "1",
                "idTag": "fixtag",
                "_csrf": csrf,
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        txid = response.url.split('/')[-1]
        if response.status_code == 200 :
            time.sleep(5)
            # get transaction id
            sess = requests.get(
                url = self.endpoint +'/ajax/CP1001/transactionIds',
                headers ={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cookie": "JSESSIONID={}".format(cookie),
                    "Authorization": "Basic YWRtaW46MTIzNA==",
                },)
            self.txid = sess.content
            print("Transaction ID : {}".format(self.txid))
            return True
        else:
            return False
    
    def remote_stop(self):
        print("remote stop transaction")
        br = self.login()
        br.open(self.endpoint+self.remotestop)
        for form in br.forms():
            csrf = form.get_value(nr=3)
        # print("CSRF : {}".format(csrf))
        # # print("Start Create Ocpp Tag")
        serverip = self.endpoint.split(':')[1].replace('//','')
        cookie= br.cookiejar._cookies[serverip]['/steve']['JSESSIONID'].value
        
        try :
            if csrf is not None:
                status = self.handle_stopTrx(csrf, cookie)
                if status :
                    res = self.logout(br ,cookie)
                    if res:
                        print("Logout Transaction Success")
                    else:
                        print("Logout Fail")
                else: # Second Time Operation
                    print("Something Wrong")
                    time.sleep(2)
                    self.handle_stopTrx(csrf, cookie)
                    time.sleep(2)
                    self.logout(br ,cookie)

        except Exception as Err:
            print(Err)

    def handle_stopTrx(self, csrf, cookie):
        print("Send Request for Stop Transaction")
        if self.txid == None:
            #get transaction id first
            self.txid = self.get_tx_id(cookie)
        response = requests.post(
            url = self.endpoint+self.remotestop,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Cookie": "JSESSIONID={}".format(cookie),
                "Authorization": "Basic YWRtaW46MTIzNA==",
            },
            data={
                "chargePointSelectList": "JSON;CP1001;-",
                "transactionId": str(self.txid[0]),
                "idTag": "fixtag",
                "_csrf": csrf,
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))

        if response.status_code == 200 :
            print("Remote Stop Transaction Complete")
            time.sleep(2)
            return self.get_txid_info(cookie)

        else:
            print("Remote Stop Transaction Fail")
            return False

    # Not done Function !!! 
    def get_txid_info(self, cookie):
        print("get Billing Transaction")
        time.sleep(2)
        flag = False
        # get Transaction infomation details from TxID
        if self.txid == None:
            self.txid = self.get_txid(cookie)
    '''
        !!!! Comment Because this is a bad way to get Transaction infomtion !!!!
        # res = requests.get(
        #     url = self.endpoint+self.txinfo+'{}'.format(self.txid[0]),
        #     headers ={
        #         "Content-Type": "application/x-www-form-urlencoded",
        #         "Cookie": "JSESSIONID={}".format(cookie),
        #         "Authorization": "Basic YWRtaW46MTIzNA==",
        #     }
        # )
        # if res.status_code == 200:
        #     # print("Get Infomation of Transaction ID : {} Complete".format(self.txid[0]))
        #     # duration = self.get_tx_duration(res)
        #     # energy = self.get_tx_energy(res)
        #     try :
        #         htmlparsed = BeautifulSoup(res.content, 'html5lib')
        #         tabledetail = htmlparsed.find('table', attrs={'class':'cpd'}).text
        #         element = tabledetail.replace(' ','').split('\n')
        #         self.startvalue = list(filter(lambda x : x.startswith('StartValue'), element))[0].replace('StartValue','')
        #         self.stopvalue = list(filter(lambda x : x.startswith('StopValue'), element))[0].replace('StopValue','')
        #         self.startdate = list(filter(lambda x : x.startswith('StartDate'), element))[0].split('at')[-1]
        #         self.stopdate = list(filter(lambda x : x.startswith('StopDate'), element))[0].split('at')[-1]
        #         delta = datetime.strptime(self.stopdate, '%H:%M') - datetime.strptime(self.startdate, '%H:%M')
        #         self.duration = delta.seconds // 60.0 # Convert duration to minute
        #         print("Charge Duration : {}".format(self.duration))
        #         flag =  True
        #     except Exception as e :
        #         flag = False
        #         pass


        return flag
    ''' 
        # -- This is function for get Transaction infomation by Database Access


    def get_tx_id(self, cookie): # use for Request Active Transaction ID.
        res = requests.get(
                url = self.endpoint +'/ajax/CP1001/transactionIds',
                headers ={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Cookie": "JSESSIONID={}".format(cookie),
                    "Authorization": "Basic YWRtaW46MTIzNA==",
                },)
        return json.loads(res.content)

    # TODO : Development for Mobile User
    def send_session_infomation(self): # Send to mobile
        print("send to firebase")
        self.duration
        self.energy
        self.start_tx
        self.stop_tx

def main():
    print("Start OCPP Service ...")
    app = OcppServer()
    # app.remote_start()
    app.remote_stop()
     
if __name__ == '__main__':
    app = OcppServer()
    main()

