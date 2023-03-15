'''
Created by Frederikme (TeetiFM)
'''

from tinderbotz.session import Session
import time
from tinderbotz.helpers.constants_helper import *
import openai
import asyncio


async def main():
    # creates instance of session
    session = Session()
    # Or if you want to use a proxy
    # AUTHORISED BY IP -> "HOST:PORT"
    # AUTHORISED BY USERNAME, PASSWORD -> "username:password@HOST:PORT"
    # session = Session(proxy="23.23.23.23:3128")

    # set location (Don't need to be logged in for this)
    # session.set_custom_location(latitude=50.879829, longitude=4.700540)
    
    # replace this with your own email and password!
    email = ""
    password = ""
    
    # login using your google account with a verified email!
    #session.login_using_google(email, password)

    # Alternatively you can login using facebook with a connected profile!
    session.login_using_facebook(email, password)

    # Alternatively, you can also use your phone number to login
    '''
    - country is needed to get the right prefix, in my case +32
    - phone_number is everything after the prefix (+32)
    NOTE: this is not my phone number :)
    '''
    #country = "Belgium"
    #phone_number = "479011124"
    #session.login_using_sms(country, phone_number)

    # spam likes, dislikes and superlikes
    # to avoid being banned:
    #   - it's best to apply a randomness in your liking by sometimes disliking.
    #   - some sleeping between two actions is recommended
    # by default the amount is 1, ratio 100% and sleep 1 second
    #session.like(amount=10, ratio="72.5%", sleep=1)
    #session.dislike(amount=1)
    #session.superlike(amount=1)
    
    # adjust allowed distance for geomatches
    # Note: PARAMETER IS IN KILOMETERS!
    #session.set_distance_range(km=150)

    # set range of prefered age
    #session.set_age_range(18, 55)

    # set interested in gender(s) -> options are: WOMEN, MEN, EVERYONE
    #session.set_sexuality(Sexuality.WOMEN)

    # Allow profiles from all over the world to appear
    #session.set_global(True)

    # Getting matches takes a while, so recommended you load as much as possible from local storage
    # get new matches, with whom you haven't interacted yet
    # Let's load the first 10 new matches to interact with later on.
    # quickload on false will make sure ALL images are stored, but this might take a lot more time
    new_matches = session.get_new_matches(amount=1, quickload=True)
    # messaged_matches = session.get_messaged_matches(amount=20, quickload=True)
    # get already interacted with matches (matches with whom you've chatted already)
    # messaged_matches = session.get_messaged_matches()
    
    # # you can store the data and images of these matches now locally in data/matches
    # # For now let's just store the messaged_matches

    # Pick up line with their personal name so it doesn't look spammy
    OPEN_AI_KEY = ""
    openai.api_key = OPEN_AI_KEY

    # print(new_matches)
    # print(messaged_matches)

    # loop through my new matches and send them the first message of the conversation
    for match in new_matches:
        # store name and chatid in variables so we can use it more simply later on
        session.store_local(match)
        # print("match:", match.get_dictionary())
        prompt = f'Write a flirty conversation starter for a Tinder conversation with {match.name}. She is {match.age}.'
        if len(match.passions) > 0:
            prompt = prompt + " Her interests/passions are: " + ", ".join(match.passions) + "."
        if len(match.bio) > 0:
            prompt = prompt + f' Her bio is: {match.bio}.\n\n Use information from her bio and one of her interests, to come up with a witty, clever, and casual pick-up one-liner.'
        print("prompt", prompt)
        completion = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=140,
        temperature=0.5,
        n=5
        )
        pickup_lines = completion.choices
        for index, line in enumerate(pickup_lines):
            print(f"\nLine {index}:", line.text)
        pickup_line = completion.choices[0].text
        # pickup_line = completion.choices[0].message.content
        # name = match.get_name()
        # send pick up line with their name in it to all my matches
        id = match.get_chat_id()

        # print(id)

        # Format the match her/his name in your pickup line for a more personal approach.
        # message = pickup_line.format(name)
        print("\nmessage:", pickup_line)

        time.sleep(5)
        # session.send_message(chatid=id, message=pickup_line)
        break

        # send a funny gif
        #session.send_gif(chatid=id, gifname="")

        # send a funny song
        #session.send_song(chatid=id, songname="")

        # send instagram or other socials like facebook, phonenumber and snapchat
        #session.send_socials(chatid=id, media=Socials.INSTAGRAM, value="Fredjemees")

        # you can also unmatch
        #session.unmatch(chatid=id)

    # let's scrape some geomatches now
    #for _ in range(5):
        # get profile data (name, age, bio, images, ...)
        #geomatch = session.get_geomatch(quickload=False)
        # store this data locally as json with reference to their respective (locally stored) images
        #session.store_local(geomatch)
        # dislike the profile, so it will show us the next geomatch (since we got infinite amount of dislikes anyway)
       # session.dislike()


if __name__ == "__main__":
    asyncio.run(main())