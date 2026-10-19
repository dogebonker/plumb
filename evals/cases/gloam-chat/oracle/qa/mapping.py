"""The reference product already speaks the contract's API, so every /qa request passes through unchanged."""


def handle(request, product):
    target = request.path + ('?' + request.query if request.query else '')
    response = product.call(request.method, target, request.body or None)
    return response.status, response.body, [('Set-Cookie', cookie) for cookie in response.headers.get_all('Set-Cookie') or []]
