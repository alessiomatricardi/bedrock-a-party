from flakon import JsonBlueprint
from flask import abort, jsonify, request

from bedrock_a_party.classes.party import CannotPartyAloneError, FoodList, ItemAlreadyInsertedByUser, NotExistingFoodError, NotInvitedGuestError, Party

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party


# /parties API accepts 2 types of request:
# POST: Creates a new party and gets the party identifier back.
# GET: Retrieves all scheduled parties.
@parties.route("/parties" , methods=['POST', 'GET'])
def all_parties():
    result = None
    if request.method == 'POST':
        try:
            # create a party
            result = create_party(request)
            
        except CannotPartyAloneError:
            # return 400
            abort(400)

    elif request.method == 'GET':
        # get all the parties
        result = get_all_parties()

    return result


# /parties/loaded API accepts 1 type of request:
# GET: returns the number of parties currently loaded in the system
@parties.route("/parties/loaded")
def loaded_parties():
    result = ''

    if 'GET' == request.method:
        # return the number of elements inside the dictionary
        result = jsonify({'loaded_parties': len(_LOADED_PARTIES)})

    return result
    

# /party/<id> API accepts 2 types of request:
# GET: Retrieves the party identified by <id>.
# DELETE: Deletes the party identified by <id> from the system.
@parties.route("/party/<id>", methods=['GET', 'DELETE'])
def single_party(id):
    global _LOADED_PARTIES
    result = ""

    # check if the party is an existing one
    exists_party(id)

    if 'GET' == request.method:
        # retrieve a party
        party = _LOADED_PARTIES[id]
        result = jsonify(party.serialize())

    elif 'DELETE' == request.method:
        # delete a party
        _LOADED_PARTIES.pop(id)

    return result


# /party/<id>/foodlist accepts 1 type of reques:
# GET: Retrieves the current foodlist of the party identified by <id>
@parties.route("/party/<id>/foodlist")
def get_foodlist(id):
    global _LOADED_PARTIES
    result = ""

    # check if the party is an existing one
    exists_party(id)

    if 'GET' == request.method:
        party = _LOADED_PARTIES[id]
        result = jsonify({'foodlist': party.get_food_list().serialize()})

    return result


# /party/<id>/foodlist/<user>/<item> API accepts 2 types of request:
# POST: Adds* the <item> brought by <user> to the food-list of the party < id > .
# DELETE: Removes the given <item> brought by <user> from the food-list of the party <id>
@parties.route("/party/<id>/foodlist/<user>/<item>", methods=['POST', 'DELETE'])
def edit_foodlist(id, user, item):
    global _LOADED_PARTIES

    # check if the party is an existing one
    exists_party(id)

    # retrieve the party
    party = _LOADED_PARTIES[id]

    result = ""

    if 'POST' == request.method:
        # add item to food-list handling NotInvitedGuestError (401) and ItemAlreadyInsertedByUser (400)
        try:
            call = party.add_to_food_list(item, user)
            result = jsonify(call.serialize())
        except NotInvitedGuestError:
            abort(401)
        except ItemAlreadyInsertedByUser:
            abort(400)
    if 'DELETE' == request.method:
        # delete item to food-list handling NotExistingFoodError (400)
        try:
            party.remove_from_food_list(item, user)
            result = jsonify({'msg': "Food deleted!"})
        except NotExistingFoodError:
            abort(400)

    return result

#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#

def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError("you cannot party alone!")

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize() for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(_id in _LOADED_PARTIES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore
