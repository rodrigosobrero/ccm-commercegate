#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Settings
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from integrator_settings import PAYMENTEZ


def paymentez_translator(content):
    ret = {}
    if "status_detail" in content["transaction"]:
        code = content["transaction"]["status_detail"]
    else:
        code = "-1"

    data = PAYMENTEZ["paymentez"]["codes"][str(code)]

    ret["up_status"]     = data["up_status"]
    ret["up_message"]    = content["transaction"]["message"]
    ret["up_recurrence"] = data["up_recurrence"]

    ret["ph_status"]    = data["ph_status"]
    ret["ph_gatewayid"] = content["transaction"]["id"]
    ret["ph_message"]   = content

    ret["user_expire"]  = data["expire_user"]

    ret["user_message"] = data["user_msg"]

    ret["intercom"]     = data["intercom"]

    return ret


def paymentez_intercom_metadata(data):
    ret = {"integrator": "paymentez",
           "authorization_code": "",
           "id": "",
           "status_detail": "",
           "amount": ""}

    for key in ret.keys():
        if key in data:
            ret[key] = data[key]

    return ret
