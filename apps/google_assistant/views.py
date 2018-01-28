import logging

from django.http import HttpResponse, JsonResponse

from libs.google_actions import AppResponse, AppRequest, NoJsonException

from .response import QuestionParser
from .exceptions import DoNotUnderstandQuestion


logger = logging.getLogger(__name__)


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
    return JsonResponse(AppResponse().ask(response))
