# some basic tests of bottle_user
# this does not use any fancy objects, just really basic coding

from __init__ import *

if __name__ == '__main__':
    print("**** USER.PY tests ****")
    initialize('./testing')
    username1 = 'fred.flintstone'
    password1 = 'Wilma!'
    username2 = 'homer.simpson'
    username2_wife = 'marge.simpson'
    password2 = 'Doh!'
    print(get_users())
    # remove the user, just in case
    delete_user(username1)
    delete_user(username2)
    # create a user, should be True
    assert( create_user(username1, password1) == True )
    # create same user should return False
    assert( create_user(username1, password1) == False )
    # create another user with extended parameters
    assert( create_user(username2, password2,
                wife=username2_wife,
                children=['Bart', 'Lisa', 'Maggie'], age=40
    ) == True )
    user = get_user(username2)
    # test if an extended parameter is present
    assert( user['wife'] == username2_wife )
    # make sure get_users() returns both users
    users = get_users()
    assert( len(users) >= 2)
    # test authentication, True if matched, False if not
    assert(authenticate(username1, password1) == True)
    assert(authenticate(username1, password2) == False)
    # test update_user
    update_user(username1, hometown='Bedrock', pet='Dino')
    user = get_user(username1)
    assert(user['username']==username1
        and user['hometown']=='Bedrock'
        and user['pet']=='Dino')
    # test if update_user will remove the pet name Dino
    # note -- TinyMongo DID NOT implement unset, so omit test for now
    #update_user(username1, pet=None)
    #user = get_user(username1)
    #print(user)
    #assert(('pet' in user) == False)
    # teardown
    delete_user(username1)
    delete_user(username2)
    print("**** PASSED TESTS ****")
