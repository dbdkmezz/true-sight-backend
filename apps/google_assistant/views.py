import logging
from django.http import HttpResponse, JsonResponse

from libs.google_actions import AppResponse, AppRequest, NoJsonException

from .response import QuestionParser
from .exceptions import DoNotUnderstandQuestion


logger = logging.getLogger(__name__)


# TODO
# abilities with the same name, hex, blink
# Fix issues parsing abilities, lots of heroes have too many, e.g. two Rs
# More ability info
# BKB and magic resistance
# context - responding to follow on questions
# More hero aliases
# Ability aliases
# Try it lots
# Upgrade to Django 2
# Do I really want the Hero model in hero advanteages?
# Is the pattern for parsing and getting responder good?
# Think about what logging I need to deploy

# v2
# Removable by types of dispel
# Linkens sphere
# Range
# Talents
# All details of spell


def index(request):
    try:
        google_request = AppRequest(request)
    except NoJsonException:
        return HttpResponse("Hello there, I'm a Google Assistant App.")

    if not google_request.text:
        return JsonResponse(AppResponse().ask("Hi, I'm Roshan. Ask me a question about Dota."))

    try:
        responder = QuestionParser(google_request.text).get_responder()
    except DoNotUnderstandQuestion:
        return JsonResponse(AppResponse().ask(
            "Sorry, I don't understand. I heard you say: {}".format(google_request.text)))

    response = responder.generate_response()
    logger.info("Question: %s. Response: %s", google_request.text, response)
    return JsonResponse(AppResponse().ask(response))
