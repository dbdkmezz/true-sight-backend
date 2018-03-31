import json
import random
import logging
from django.http import HttpResponse, JsonResponse

from apps.metadata.models import User, DailyUse
from libs.google_actions import AppResponse, AppRequest, NoJsonException

from .response import ResponseGenerator, QuestionParser
from .exceptions import DoNotUnderstandQuestion, Goodbye


logger = logging.getLogger(__name__)
good_response_logger = logging.getLogger('good_response')


# # TODO
#
# # Pre reddit
# test that my exception logger works (then remove that code)
# Respond to ability questions not with "any more ability" but if they want to know more about it.
# cooldown, damange type ... of ultimate (OR at least let them ask more about it)
# ensure I'm happy with the logging
# persona?
# fix all the ablities which aren't loading properly
# Try saying all heroes
# Think about all prompts
# feedback
# emphasis of does pierce
# say the valve stuff faster
#
# # V2
# lane in implicit discovery
# what does just saying no do?
# don't just quit if they say 1, but quit if they say it twice in a row
# move where I handle donotunderstand and the talk to responses to response.py
# maximum 3 consecutive I don't understand respones!
# leave (and others)
#
# # V3
# Just "hex" and "blink" don't work
# Talents
# Aghs upgrades
# Linkens sphere interactions
# Context and follow up questions
# Abilities with the same name, hex, blink
# Do I really want the Hero model in hero advanteages?
# Advantage against multiple heroes
# Ability aliases
# Warn if an ability was not found this time when loading them (e.g. name change)
# Add the abilities of heroes summoned units
# Add abilities from talents or aghanims (be careful they don't override existing abilities, e.g. Brewmaster's Drunken Haze)  # noqa
# Removable by types of dispel
# Ability duration
# Ability Range
# All details of spell
# Vision range of heroes
# Better response for multiple ultimates? (Dark Willow)
# Cast range


def index(request):
    try:
        return _respond_to_request(request)
    except:
        logger.exception("Uncaught exception")
        return JsonResponse(AppResponse().tell("I'm sorry, something went wrong."))


def _respond_to_request(request):
    try:
        google_request = AppRequest(request)
    except NoJsonException:
        return HttpResponse("Hello there, I'm a Google Assistant App.")

    if google_request.text == '1':  # Google's ping
        JsonResponse(AppResponse().tell("Hello Google"))

    if google_request.text == 'test exception':
        raise Exception

    user_id = google_request.user_id
    User.log_user(user_id)

    context = None
    if google_request.conversation_token:
        context = json.loads(google_request.conversation_token)

    logger.info("Recieved question: {}, context: {}".format(google_request.text, context))
    try:
        response, context = ResponseGenerator.respond(
            google_request.text, conversation_token=context, user_id=user_id)
    except DoNotUnderstandQuestion:
        if google_request.text.lower().startswith('talk to') or google_request.text == '1':
            return JsonResponse(AppResponse().tell((
                "I'm sorry, you're currently talking to True Sight, I'll leave the conversation "
                "so you can try again. Goodbye.")))
        DailyUse.log_use(success=False, user_id=user_id)
        return JsonResponse(AppResponse().ask((
            "Sorry, I don't understand. I heard you say: '{}'. {} "
            "To end the conversation, just say 'goodbye'.").format(
                google_request.text,
                random.choice((
                    "Have another go.",
                    "Could you say that again?",
                    "Please try again.",
                )),
            ),
            json.dumps(context)))
    except Goodbye:
        return JsonResponse(AppResponse().tell('Goodbye'))

    good_response_logger.info(
        "%s Context: %s. Response: %s",
        QuestionParser(google_request.text, user_id=user_id),
        context,
        response)
    DailyUse.log_use(success=True, user_id=user_id)

    if context:
        json_context = json.dumps(context)
        return JsonResponse(AppResponse().ask(response, json_context))
    else:
        return JsonResponse(AppResponse().tell(response))
