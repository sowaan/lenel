



import frappe
from frappe.utils import now, now_datetime, nowdate, get_datetime, add_to_date
import requests
import json









def send_checkins(all_events, device_id, log_type, timestamp, table, inout, utc_time) :

    utc_time = int(utc_time)
    valid_sources = table
    filtered_events = [event for event in all_events if log_type in event]    
    filtered_events = [event for event in filtered_events if event[log_type] in valid_sources]

    if isinstance(table, str):
            table = json.loads(table)
    if isinstance(inout, str):
        inout = json.loads(inout)

    for ev in filtered_events :       
        lg_type = ""
        for i in range(len(table)) :
            if ev[log_type] == table[i] :
                lg_type = inout[i]

        if lg_type == 'IN' or lg_type == 'OUT' :
            emp_list = frappe.get_list("Employee",
                                        filters={
                                        'attendance_device_id': ev[device_id]
                                        })
            if emp_list :
                emp_doc = frappe.get_doc("Employee",emp_list[0].name)
                event_datetime = get_datetime(ev[timestamp])
                event_datetime_naive = event_datetime.replace(tzinfo=None)
                event_datetime_naive = add_to_date(event_datetime_naive, hours=utc_time)


                checkin_doc = frappe.get_doc({
                        'doctype': 'Employee Checkin',
                        'employee': emp_doc.name ,
                        'time' : event_datetime_naive ,
                        'log_type' : lg_type,
                    })
                check = frappe.db.exists("Employee Checkin", {"employee":emp_doc.name , "time":event_datetime_naive , "log_type":lg_type })
                if not check :
                    checkin_doc.insert()



def get_url(open_access_url, params="", url_type="instances"):
    return open_access_url + url_type + '?' + \
            "version=1.0" + params + "&queue=false"



@frappe.whitelist()
def authentication( api, host_ip, port, application_id, user_name, password, directory_id, tls ) :
    headers = {'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Application-Id':  application_id,
                'Session-Token': ''}
    open_access_url = "http{tls}://{server_ip}:{port}/{api}/".format(
            tls='s' if tls else '',
            server_ip=host_ip,
            port=port,
            api=api
        )
    session = requests.Session()
    response_timeout = 3000
    body = {
            "user_name" : user_name,
            "password" : password,
            "directory-id" : directory_id
        }
    url = get_url(open_access_url, url_type="authentication")
    r = session.request('POST', url, headers=headers, json=body, verify=False)
    response = r.json()
    return response    



@frappe.whitelist()
def get_logged_events(api, host_ip, port, application_id, user_name, password, tls, session_token, from_date, device_id, log_type, timestamp, table, inout, utc_time):


    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Application-Id': application_id,
        'Session-Token': session_token
    }
    open_access_url = "http{tls}://{server_ip}:{port}/{api}/".format(
        tls='s' if tls else '',
        server_ip=host_ip,
        port=port,
        api=api
    )
    session = requests.Session()
    response_timeout = 3000
    body = {
        "user_name": user_name,
        "password": password,
        "directory-id": "id-1"
    }

    to_date = now()
    page_number = 1
    total_pages = 1
    all_events = []

    if from_date != 'False':
        params_filter = f'&filter=timestamp>="{from_date}"&page_number={{page_number}}&page_size=100'
        # params_filter = f'&filter=timestamp>="{from_date}"andbadge_id="25"&page_number={{page_number}}&page_size=100'
    else:
        params_filter = f'&filter=timestamp<="{to_date}"&page_number={{page_number}}&page_size=100'


    while page_number <= total_pages:
        url = get_url(open_access_url, params=params_filter.format(page_number=page_number), url_type="logged_events")

        try:
            r = session.request('GET', url, headers=headers, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            frappe.throw(f"HTTP error occurred: {http_err}")
        except Exception as err:
            frappe.throw(f"Other error occurred: {err}")

        response = r.json()

        if 'error' in response:
            frappe.throw(f"Error in response: {response['error']}")

        if 'item_list' not in response or len(response['item_list']) == 0:
            frappe.msgprint("No logged events found.")
            break
        else:
            all_events.extend(response['item_list'])
            total_pages = response.get('total_pages', 1)
            page_number += 1

    send_checkins(all_events, device_id, log_type, timestamp, table, inout, utc_time)

    # return all_events
    return to_date








@frappe.whitelist()
def get_checkins_from_scheduler() :

    lenel_sett_list = frappe.get_list("Lenel Site Setting")



    if lenel_sett_list :
        for list in lenel_sett_list :
            lenel_sett_doc = frappe.get_doc("Lenel Site Setting",list.name)

            response = authentication(lenel_sett_doc.api ,lenel_sett_doc.host_ip ,lenel_sett_doc.port ,lenel_sett_doc.application_id ,lenel_sett_doc.user_name ,lenel_sett_doc.password, lenel_sett_doc.directory_id, lenel_sett_doc.og_openaccess_tls )
            session_token = response['session_token']

            till_datetime = "False"
            if lenel_sett_doc.till_datetime :
                till_datetime = lenel_sett_doc.till_datetime
            

            logs_array = []
            inout = []
            for row in lenel_sett_doc.logtype_definition :
                logs_array.append(row.lenel_definition)
                inout.append(row.logtype)  
            

            utc_time = 0
            if lenel_sett_doc.time_zone :
                utc_time = int(lenel_sett_doc.time_zone)
            

            res1 = get_logged_events(lenel_sett_doc.api, lenel_sett_doc.host_ip, lenel_sett_doc.port, lenel_sett_doc.application_id, lenel_sett_doc.user_name, lenel_sett_doc.password, lenel_sett_doc.og_openaccess_tls, session_token, till_datetime , lenel_sett_doc.employee_id_field, lenel_sett_doc.logtype_field, lenel_sett_doc.timestamp_field, logs_array, inout, utc_time )
            lenel_sett_doc.till_datetime = res1
            lenel_sett_doc.save()






























































# @frappe.whitelist()
# def get_directory( api, host_ip, port, application_id, user_name, password, tls ) :

#     headers = {'Content-Type': 'application/json',
#                 'Accept': 'application/json',
#                 'Application-Id':  application_id,
#                 'Session-Token': ''}

#     open_access_url = "http{tls}://{server_ip}:{port}/{api}/".format(
#             tls='s' if tls else '',
#             server_ip=host_ip,
#             port=port,
#             api=api
#         )
#     session = requests.Session()
#     response_timeout = 30


#     body = {
#             'user_name': user_name,
#             'password': password
#         }

#     url = get_url(open_access_url, url_type="directories")

    
#     r = session.request('GET', url, headers=headers, timeout=response_timeout, verify=False)
#     response = r.json()
#     return response 