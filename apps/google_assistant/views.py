import logging
from django.http import HttpResponse, JsonResponse

from libs.google_actions import AppResponse, AppRequest, NoJsonException

from .response import ResponseGenerator
from .exceptions import DoNotUnderstandQuestion


logger = logging.getLogger(__name__)


# # TODO
#
# # General
# Hero role accuracy
# More hero aliases
# Ability aliases
# Try it lots
# Do I really want the Hero model in hero advanteages?
#
# # Logging
# log if we have to use the fallback advantage response
# Fix issues parsing abilities, there are still those which have too many
# Track unique users and individual usage
# Track popularity of each question type
# Track daily activity
# Log failures to parse separately (not the __name__ logger?). Log all questions separately too.
#
# Questions
# Is X good/strong against Y?

# # V2
# Context and follow up questions
# Abilities with the same name, hex, blink
# Warn if an ability was not found this time when loading them (e.g. name change)
# Damage type
# Add the abilities of heroes summoned units
# Add abilities from talents or aghanims (be careful they don't override existing abilities, e.g. Brewmaster's Drunken Haze)  # noqa
# Talents
# Removable by types of dispel
# Linkens sphere interactions
# Ability duration
# Ability Range
# All details of spell
# Vision range of heroes
# Cast range


def index(request):
    try:
        google_request = AppRequest(request)
    except NoJsonException:
        return HttpResponse("Hello there, I'm a Google Assistant App.")

    try:
        if not google_request.text:
            return JsonResponse(AppResponse().ask("Hi, I'm Roshan. Ask me a question about Dota."))

        try:
            response = ResponseGenerator.respond(google_request.text)
        except DoNotUnderstandQuestion:
            return JsonResponse(AppResponse().ask(
                "Sorry, I don't understand. I heard you say: {}".format(google_request.text)))

        logger.info("Question: %s. Response: %s", google_request.text, response)
        return JsonResponse(AppResponse().ask(response))
    except:
        logger.exception()
        return JsonResponse(AppResponse().ask(
            "I'm sorry, something went wrong, please try again."))
