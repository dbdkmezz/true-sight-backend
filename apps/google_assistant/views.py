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

    try:
        responder = QuestionParser(google_request.text).get_responder()
    except DoNotUnderstandQuestion:
        return JsonResponse(AppResponse().tell(
            "Sorry, I don't understand. I heard you say: {}".format(google_request.text)))

    response = responder.generate_response()
    return JsonResponse(AppResponse().tell(response))
