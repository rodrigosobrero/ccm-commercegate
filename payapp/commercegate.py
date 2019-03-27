@require_http_methods(["GET"])
def iframe_commercegate(request):
    try:
        data = request.body
    except Exception:
        body = { 'status': 'error', 'message': 'error loading request' }
        return HttpResponse(json.dumps(body), content_type='application/json', status=200)

    urlVars = { }

    ## API Endpoints
    # 'url':                'https://checkout.cgpaytech.com/'                       # integrator_settings
    # 'url':                'https://checkout.cgpaytech.com/get-token',             # integrator_settings
    # 'url':                'https://secure.cgpaytech.com/api/customer/v2/refund'   # integrator_settings

    ## Token API
    # 'cid':                '', # integrator_settings
    # 'wid':                '', # integrator_settings
    # 'redirect':           '', # integrator_settings
    # 'packid':             '', # request
    # 'username':           '', # request
    # 'email':              '', # request (optional)

    ## Form Request API
    # 'cid':                '', # integrator_settings
    # 'wid':                '', # integrator_settings
    # 'token':              '', # request
    # 'invalidTokenUrl':    '', # integrator_settings (optional)

    ## Refund API
    # 'customerId':         '', # integrator_settings
    # 'password':           '', # integrator_settings
    # 'transactionId':      '', # request
    # 'amount':             '', # request (optional)

    ## Cancel Membership API
    # 'customerId':         '', # integrator_settings
    # 'password':           '', # integrator_settings
    # 'websiteId':          '', # integrator_settings
    # 'username':           '', # request
    # 'email':              '', # request (optional)
    # 'first_trx':          '', # request (optional)

    return url + urllib.urlencode(urlVars)