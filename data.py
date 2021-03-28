# -*- coding: utf-8 -*-
from __future__ import absolute_import
from base64 import b64decode as decode


encoding = u"utf-8"

engine_url = u"aHR0cHM6Ly9peGlyYy5jb20v"

networks = {
  u"Q3liZXJheA==": u"aXJjLmN5YmVyYXgub3Jn",
  u"Q2hlZXppbklSQw==": u"aXJjLmNoZWV6aW4ubmV0",
  u"QWJhbmRvbmVkLUlSQw==": u"aXJjLmFiYW5kb25lZC1pcmMubmV0",
  u"aXJjLk9jZWFuSVJDLm5ldA==": u"aXJjLm9jZWFuaXJjLm5ldA==",
  u"Q3JpdGVu": u"aXJjLmNyaXRlbi5uZXQ=",
  u"MTAxLUZyZWVkb20=": u"aXJjLjEwMS1mcmVlZG9tLm9yZw==",
  u"QWJqZWN0cw==": u"aXJjLmFiamVjdHMubmV0",
  u"Uml6b24=": u"aXJjLnJpem9uLm5ldA==",
  u"WmVzdHlsYW5kLmNvbQ==": u"aXJjLnplc3R5bGFuZC5uZXQ=",
  u"WGVyb01lbQ==": u"aXJjLnhlcm9tZW0uY29t",
  u"UGFuYW1hNTA3": u"aXJjLnNwYWNlNTA3LmNvbQ==",
  u"QWxwaGFJUkM=": u"aXJjLmFscGhhaXJjLmNvbQ==",
  u"RnJvWnlu": u"aXJjLmZyb3p5bi5uZXQ=",
  u"MWFuZGFsbElSQy5uZXQ=": u"aXJjLjFhbmRhbGxpcmMubmV0",
  u"UmVsYXhlZElSQw==": u"aXJjLnJlbGF4ZWRpcmMubmV0",
  u"bWlyY3BoYW50b20ubmV0": u"aXJjLm1pcmNwaGFudG9tLm5ldA==",
  u"U2NlbmVQMlA=": u"aXJjLnNjZW5lcDJwLm5ldA==",
  u"WGVOb24tSXJj": u"aXJjLnhlbm9uLWlyYy5uZXQ="
}


def Networks():
    d = dict(( decode(str(k).encode(encoding)).decode(encoding), decode(str(v).encode(encoding)).decode(encoding))
          for k,v in networks.items())
    return d

def Engine_Url():
    c = decode(str(engine_url).encode(encoding))
    return c.decode(encoding)
